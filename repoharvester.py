"""Clone a git repository (or read a local folder) and compile its text files into one file."""
import argparse
import io
import logging
import os
import re
import signal
import subprocess
import tempfile
import threading
import tokenize
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger("repoharvester")

DEFAULT_MAX_SIZE_KB = 1000
LARGE_FILE_KB = 500
CHARS_PER_TOKEN = 4  # rough average for code and English text
CANCEL_POLL_S = 0.2
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


def _remove_python_comments(content: str) -> str:
    """Exact removal via the tokenizer; raises TokenError/SyntaxError if the code does not tokenize."""
    comments = [t for t in tokenize.generate_tokens(io.StringIO(content).readline)
                if t.type == tokenize.COMMENT and not (t.start == (1, 0) and t.string.startswith('#!'))]
    lines = content.splitlines(keepends=True)
    for tok in reversed(comments):  # right to left keeps earlier columns valid
        (row, start), (_, end) = tok.start, tok.end
        lines[row - 1] = lines[row - 1][:start] + lines[row - 1][end:]
    return ''.join(lines)


def remove_comments(content: str, extension: str) -> str:
    """Strip comments for known languages; string literals are preserved."""
    if extension.lower() == 'py':
        try:
            return _remove_python_comments(content)
        except (tokenize.TokenError, SyntaxError):
            pass  # not valid Python: the regex below still strips most comments
    pattern = _COMPILED.get(extension.lower())
    if not pattern:
        return content
    return pattern.sub(lambda m: m.group(1) or '', content)


def get_repo_name(repo: str) -> str:
    name = repo.strip().rstrip('/').split('/')[-1].split(':')[-1]
    return name.removesuffix('.git') or 'repo'


def _members(table: dict[str, set[str]], groups: set[str]) -> set[str]:
    return set().union(*(v for k, v in table.items() if k in groups))


@dataclass(frozen=True)
class HarvestOptions:
    """Everything that shapes one harvest besides the source itself."""
    output_dir: Path = DEFAULT_OUTPUT_DIR
    strip_comments: bool = False
    skip_groups: frozenset[str] = frozenset(ALL_GROUPS)
    exclude_folders: tuple[str, ...] = ()
    max_size_kb: int = DEFAULT_MAX_SIZE_KB


DEFAULT_OPTIONS = HarvestOptions()


def collect_files(root: Path, options: HarvestOptions = DEFAULT_OPTIONS) -> list[Path]:
    """Return sorted files under root, honouring skip groups, excluded folders and size limit."""
    groups = options.skip_groups
    skip_ext = _members(EXTENSION_GROUPS, groups)
    skip_names = _members(FILENAME_GROUPS, groups)
    skip_dirs = ALWAYS_SKIPPED_FOLDERS | set(options.exclude_folders) | _members(FOLDER_GROUPS, groups)

    files = []
    for dirpath, dirnames, filenames in root.walk():
        dirnames[:] = sorted(d for d in dirnames if d not in skip_dirs)
        for name in sorted(filenames):
            path = dirpath / name
            ext = path.suffix.lstrip('.').lower()
            if name in skip_names or ext in skip_ext or path.is_symlink():
                continue
            if _within_size(path, root, options.max_size_kb):
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


def _section(path: Path, root: Path, options: HarvestOptions) -> str:
    """One file as an output section; raises UnicodeDecodeError for non-UTF-8 files."""
    content = path.read_text(encoding='utf-8')
    if options.strip_comments:
        content = remove_comments(content, path.suffix.lstrip('.'))
    return f'### {path.relative_to(root).as_posix()}\n{content}\n### end of file\n'


def write_union_file(files: list[Path], root: Path, out_file: Path, options: HarvestOptions) -> list[str]:
    """Append files to out_file; return relative paths skipped as non-UTF-8."""
    skipped = []
    with out_file.open('a', encoding='utf-8') as out:
        for path in files:
            try:
                out.write(_section(path, root, options))
            except UnicodeDecodeError:
                rel = path.relative_to(root).as_posix()
                log.info("Skipping non-UTF-8 file: %s", rel)
                skipped.append(rel)
    return skipped


def _drop_git_ignored(root: Path, files: list[Path]) -> list[Path]:
    """Keep files git would show (tracked + untracked-not-ignored); all files if root is not in a git repo."""
    result = subprocess.run(['git', '-C', str(root), 'ls-files', '-z', '--cached', '--others', '--exclude-standard'],
                            capture_output=True, text=True)
    if result.returncode:
        return files
    visible = set(filter(None, result.stdout.split('\0')))
    return [f for f in files if f.relative_to(root).as_posix() in visible]


def _select_files(root: Path, options: HarvestOptions) -> list[Path]:
    """collect_files minus the output folder and anything git ignores."""
    output = options.output_dir.resolve()
    files = [f for f in collect_files(root, options) if not f.resolve().is_relative_to(output)]
    return _drop_git_ignored(root, files)


class HarvestCancelled(Exception):
    """The cancel event was set while the repository was being cloned."""


class CloneError(Exception):
    """git clone failed; the message is one readable line naming the repo and git's reason."""


def _kill_tree(proc: subprocess.Popen) -> None:
    """Kill git and its children (ssh), which would otherwise keep the pipe open."""
    if os.name == 'posix':
        os.killpg(proc.pid, signal.SIGKILL)
    else:
        proc.kill()
    proc.communicate()


def _clone(repo: str, dest: Path, cancel: threading.Event | None) -> None:
    log.info("Cloning %s", repo)
    cmd = ['git', 'clone', '--depth', '1', '--quiet', repo, str(dest)]
    with subprocess.Popen(cmd, stderr=subprocess.PIPE, text=True, start_new_session=True) as proc:
        while True:
            try:
                _, stderr = proc.communicate(timeout=CANCEL_POLL_S)
                break
            except subprocess.TimeoutExpired:
                if cancel and cancel.is_set():
                    _kill_tree(proc)
                    raise HarvestCancelled from None
    if proc.returncode:
        raise CloneError(_clone_failure(repo, proc.returncode, stderr))


def harvest(repo: str, options: HarvestOptions = DEFAULT_OPTIONS, cancel: threading.Event | None = None) -> Path:
    """Harvest a git URL or local folder into <output_dir>/<name>_all_files.txt and return its path.

    Setting `cancel` aborts a running clone with HarvestCancelled.
    """
    options.output_dir.mkdir(parents=True, exist_ok=True)
    local = Path(repo).expanduser()
    repo_name = local.resolve().name if local.is_dir() else get_repo_name(repo)
    out_file = options.output_dir / f'{repo_name}_all_files.txt'

    with tempfile.TemporaryDirectory(prefix='repoharvester_') as tmp:
        root = local if local.is_dir() else Path(tmp)
        if root != local:
            _clone(repo, root, cancel)
        out_file.write_text(f'## {repo_name}\n', encoding='utf-8')  # only now: a failed clone keeps the old result
        files = _select_files(root, options)
        skipped = write_union_file(files, root, out_file, options)

    (options.output_dir / 'skipped_files.txt').write_text(''.join(f'{s}\n' for s in skipped), encoding='utf-8')
    _report(out_file, len(files) - len(skipped), len(skipped))
    return out_file


def _report(out_file: Path, written: int, skipped: int) -> None:
    tokens_k = out_file.stat().st_size / CHARS_PER_TOKEN / 1000
    log.info("Wrote %d files to %s, ~%.1fk tokens (%d non-UTF-8 skipped)", written, out_file, tokens_k, skipped)


def _clone_failure(repo: str, returncode: int, stderr: str) -> str:
    first = next((line.strip() for line in (stderr or '').splitlines() if line.strip()), None)
    return f'git clone of {repo} failed: {first or f"exit code {returncode}"}'


def _csv(value: str) -> list[str]:
    return [v.strip() for v in value.split(',') if v.strip()]


def _parser() -> argparse.ArgumentParser:
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
    return parser


def _setup_logging(log_file: Path | None) -> None:
    handlers = [logging.StreamHandler()]
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file, encoding='utf-8'))
    logging.basicConfig(level=logging.INFO, format='%(message)s', handlers=handlers)


def main(argv=None):
    parser = _parser()
    args = parser.parse_args(argv)
    if unknown := set(args.no_skip) - set(ALL_GROUPS):
        parser.error(f'unknown group(s): {", ".join(sorted(unknown))}')
    _setup_logging(args.log)
    options = HarvestOptions(args.output_dir, args.remove, frozenset(ALL_GROUPS) - set(args.no_skip),
                             tuple(args.exclude), args.max_size)
    try:
        out = harvest(args.repo, options)
    except CloneError as e:
        parser.exit(1, f'{e}\n')
    print(f'All files have been written to {out}')


if __name__ == '__main__':
    main()
