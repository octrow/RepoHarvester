"""Clone a git repository (or read a local folder) and compile its text files into one file."""
import argparse
import logging
import re
import subprocess
import tempfile
from pathlib import Path

log = logging.getLogger("repoharvester")

DEFAULT_MAX_SIZE_KB = 1000
LARGE_FILE_KB = 500
CHARS_PER_TOKEN = 4  # rough average for code and English text
DEFAULT_OUTPUT_DIR = Path("output")

# Matched against lowercased file extensions.
EXTENSION_GROUPS = {
    'media': {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'svg', 'ico', 'raw', 'psd', 'ai', 'webp'},
    'office': {'xlsx', 'xls', 'docx', 'doc', 'pptx', 'ppt', 'pdf'},
    'system': {'pack', 'idx', 'ds_store', 'sys', 'ini', 'bat', 'plist'},
    'executables': {'exe', 'dll', 'so', 'bin', 'dylib'},
    'archive': {'zip', 'rar', '7z', 'tar', 'gz', 'bz2', 'xz'},
    'audio': {'mp3', 'wav', 'aac', 'flac', 'ogg'},
    'video': {'mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv', 'webm'},
    'database': {'db', 'sqlite', 'sqlite3', 'sqlitedb', 'mdb'},
    'font': {'ttf', 'otf', 'woff', 'woff2', 'eot'},
    'temporary': {'tmp', 'temp', 'swp', 'swo'},
    'compiled_code': {'o', 'obj', 'pyc', 'pyo', 'class', 'jar'},
    'certificate': {'cer', 'pem', 'crt', 'key'},
    'configuration': {'conf', 'cfg', 'config'},
    'log_files': {'err', 'stderr', 'stdout', 'log'},
    'cache_files': {'cache', 'cached'},
}
# Matched against exact file names.
FILENAME_GROUPS = {
    'package_locks': {'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', 'Gemfile.lock',
                      'poetry.lock', 'uv.lock', 'Cargo.lock', 'composer.lock'},
}
# Matched against directory names; contents are never walked.
FOLDER_GROUPS = {
    'virtual_env': {'venv', '.venv', 'env'},
    'node_modules': {'node_modules'},
    'cache_files': {'__pycache__', '.mypy_cache', '.pytest_cache', '.ruff_cache'},
}
ALWAYS_SKIPPED_FOLDERS = {'.git', '.github'}
ALL_GROUPS = sorted(EXTENSION_GROUPS.keys() | FILENAME_GROUPS.keys() | FOLDER_GROUPS.keys())

# Each pattern: group 1 = a string literal (kept), group 2 = a comment (removed).
# Matching strings first keeps "http://x" or "#fff" inside strings intact.
_STR = r'"(?:\\.|[^"\\\n])*"|\'(?:\\.|[^\'\\\n])*\''
_C = rf'({_STR}|`(?:\\.|[^`\\])*`)|(//.*|/\*[\s\S]*?\*/)'
_HASH_COMMENT = r'(?<!\S)#.*'  # '#' only at line start or after whitespace: keeps ${#a}, url#frag
_HASH = rf'({_STR})|({_HASH_COMMENT})'
_PY = rf'("""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'|{_STR})|({_HASH_COMMENT})'
_SQL = rf'({_STR})|(--.*|/\*[\s\S]*?\*/)'
_LUA = rf'(\[(=*)\[[\s\S]*?\]\2\]|{_STR})|(--\[(=*)\[[\s\S]*?\]\4\]|--.*)'
_CSS = rf'({_STR})|(/\*[\s\S]*?\*/)'
_XML = r'()(<!--[\s\S]*?-->)'
COMMENT_PATTERNS = {
    **dict.fromkeys(['js', 'jsx', 'ts', 'tsx', 'java', 'c', 'h', 'cpp', 'hpp', 'cs',
                     'go', 'swift', 'kt', 'rs'], _C),
    **dict.fromkeys(['css', 'scss'], _CSS),
    'php': rf'({_STR})|(//.*|/\*[\s\S]*?\*/|#.*)',
    'py': _PY,
    'lua': _LUA,
    **dict.fromkeys(['rb', 'pl', 'r', 'sh', 'bash', 'zsh', 'yaml', 'yml', 'toml'], _HASH),
    'sql': _SQL,
    **dict.fromkeys(['html', 'xml', 'vue'], _XML),
}
_COMPILED = {ext: re.compile(p) for ext, p in COMMENT_PATTERNS.items()}


def remove_comments(content: str, extension: str) -> str:
    """Strip comments for known languages; string literals are preserved."""
    pattern = _COMPILED.get(extension.lower())
    if not pattern:
        return content
    return pattern.sub(lambda m: m.group(1) or '', content)


def get_repo_name(repo: str) -> str:
    name = repo.strip().rstrip('/').split('/')[-1].split(':')[-1]
    return name.removesuffix('.git') or 'repo'


def _members(table: dict[str, set[str]], groups: set[str]) -> set[str]:
    return set().union(*(v for k, v in table.items() if k in groups))


def collect_files(root: Path, skip_groups=None, exclude_folders=(), max_size_kb=DEFAULT_MAX_SIZE_KB):
    """Return sorted files under root, honouring skip groups, excluded folders and size limit."""
    groups = set(ALL_GROUPS if skip_groups is None else skip_groups)
    skip_ext = _members(EXTENSION_GROUPS, groups)
    skip_names = _members(FILENAME_GROUPS, groups)
    skip_dirs = ALWAYS_SKIPPED_FOLDERS | set(exclude_folders) | _members(FOLDER_GROUPS, groups)

    files = []
    for dirpath, dirnames, filenames in root.walk():
        dirnames[:] = sorted(d for d in dirnames if d not in skip_dirs)
        for name in sorted(filenames):
            path = dirpath / name
            ext = path.suffix.lstrip('.').lower()
            if name in skip_names or ext in skip_ext or path.is_symlink():
                continue
            if _within_size(path, root, max_size_kb):
                files.append(path)
    return files


def _within_size(path: Path, root: Path, max_size_kb: int) -> bool:
    """True if path fits max_size_kb; logs skipped and large files."""
    size_kb = path.stat().st_size / 1024
    if size_kb > max_size_kb:
        log.warning("Skipping %s: %.1f KB > %s KB", path.relative_to(root), size_kb, max_size_kb)
        return False
    if size_kb > LARGE_FILE_KB:
        log.info("Large file %s: %.1f KB", path.relative_to(root), size_kb)
    return True


def write_union_file(files, root: Path, out_file: Path, repo_name: str, strip_comments=False):
    """Write files into out_file; return list of relative paths skipped as non-UTF-8."""
    skipped = []
    with out_file.open('w', encoding='utf-8') as out:
        out.write(f'## {repo_name}\n')
        for path in files:
            rel = path.relative_to(root).as_posix()
            try:
                content = path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                log.info("Skipping non-UTF-8 file: %s", rel)
                skipped.append(rel)
                continue
            if strip_comments:
                content = remove_comments(content, path.suffix.lstrip('.'))
            out.write(f'### {rel}\n{content}\n### end of file\n')
    return skipped


def git_visible_files(root: Path) -> set[str] | None:
    """Tracked plus untracked-but-not-ignored files under root, or None if root is not in a git repo."""
    result = subprocess.run(['git', '-C', str(root), 'ls-files', '-z', '--cached', '--others', '--exclude-standard'],
                            capture_output=True, text=True)
    if result.returncode:
        return None
    return set(filter(None, result.stdout.split('\0')))


def harvest(repo: str, output_dir: Path = DEFAULT_OUTPUT_DIR, strip_comments=False, skip_groups=None,
            exclude_folders=(), max_size_kb=DEFAULT_MAX_SIZE_KB) -> Path:
    """Harvest a git URL or local folder into <output_dir>/<name>_all_files.txt and return its path."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    local = Path(repo).expanduser()
    repo_name = local.resolve().name if local.is_dir() else get_repo_name(repo)
    out_file = output_dir / f'{repo_name}_all_files.txt'

    with tempfile.TemporaryDirectory(prefix='repoharvester_') as tmp:
        if local.is_dir():
            root = local
        else:
            root = Path(tmp)
            log.info("Cloning %s", repo)
            subprocess.run(['git', 'clone', '--depth', '1', '--quiet', repo, str(root)],
                           check=True, stderr=subprocess.PIPE, text=True)
        files = collect_files(root, skip_groups, exclude_folders, max_size_kb)
        files = [f for f in files if not f.resolve().is_relative_to(output_dir.resolve())]
        if (visible := git_visible_files(root)) is not None:
            files = [f for f in files if f.relative_to(root).as_posix() in visible]
        skipped = write_union_file(files, root, out_file, repo_name, strip_comments)

    (output_dir / 'skipped_files.txt').write_text(''.join(f'{s}\n' for s in skipped), encoding='utf-8')
    tokens_k = out_file.stat().st_size / CHARS_PER_TOKEN / 1000
    log.info("Wrote %d files to %s, ~%.1fk tokens (%d non-UTF-8 skipped)",
             len(files) - len(skipped), out_file, tokens_k, len(skipped))
    return out_file


def clone_error(e: subprocess.CalledProcessError) -> str:
    """One readable line from a failed git clone."""
    first = next((line.strip() for line in (e.stderr or '').splitlines() if line.strip()), None)
    return f'git clone failed: {first or f"exit code {e.returncode}"}'


def _csv(value: str) -> list[str]:
    return [v.strip() for v in value.split(',') if v.strip()]


def main(argv=None):
    parser = argparse.ArgumentParser(description='Clone a repo and compile its contents into a single file.')
    parser.add_argument('repo', help='git URL (SSH or HTTPS) or path to a local folder')
    parser.add_argument('-r', '--remove', action='store_true', help='remove comments from code files')
    parser.add_argument('--no-skip', action='extend', type=_csv, default=[], metavar='GROUP[,GROUP]',
                        help=f'include these normally skipped groups: {", ".join(ALL_GROUPS)}')
    parser.add_argument('--max-size', type=int, default=DEFAULT_MAX_SIZE_KB, help='maximum file size in KB')
    parser.add_argument('--exclude', action='extend', type=_csv, default=[], metavar='DIR[,DIR]',
                        help='folder names to exclude (with contents); repeatable')
    parser.add_argument('-o', '--output-dir', type=Path, default=DEFAULT_OUTPUT_DIR, help='output directory')
    parser.add_argument('--log', type=Path, help='also write the log to this file')
    args = parser.parse_args(argv)
    if unknown := set(args.no_skip) - set(ALL_GROUPS):
        parser.error(f'unknown group(s): {", ".join(sorted(unknown))}')

    handlers = [logging.StreamHandler()]
    if args.log:
        args.log.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(args.log, encoding='utf-8'))
    logging.basicConfig(level=logging.INFO, format='%(message)s', handlers=handlers)

    try:
        out = harvest(args.repo, args.output_dir, args.remove, set(ALL_GROUPS) - set(args.no_skip),
                      args.exclude, args.max_size)
    except subprocess.CalledProcessError as e:
        parser.exit(1, f'{clone_error(e)}\n')
    print(f'All files have been written to {out}')


if __name__ == '__main__':
    main()
