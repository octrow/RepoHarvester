import argparse
import os
import re
import shutil
import subprocess

from comment_pattens import COMMENT_PATTERNS

# Define groups of file extensions
MEDIA_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'svg', 'ico', 'raw', 'psd', 'ai'}
OFFICE_EXTENSIONS = {'xlsx', 'xls', 'docx', 'pptx', 'pdf'}
SYSTEM_EXTENSIONS = {'pack', 'idx', 'DS_Store', 'sys', 'ini', 'bat', 'plist'}
EXECUTABLE_EXTENSIONS = {'exe', 'dll', 'so', 'bin'}
ARCHIVE_EXTENSIONS = {'zip', 'rar', '7z', 'tar', 'gz', 'bz2'}
AUDIO_EXTENSIONS = {'mp3', 'wav', 'aac', 'flac'}
VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'wmv', 'flv'}
DATABASE_EXTENSIONS = {'db', 'sqlitedb', 'mdb'}
FONT_EXTENSIONS = {'ttf', 'otf', 'woff', 'woff2'}
TEMPORARY_EXTENSIONS = {'tmp', 'temp', 'swp', 'swo'}
COMPILED_CODE_EXTENSIONS = {'o', 'obj', 'pyc', 'class'}
CERTIFICATE_EXTENSIONS = {'cer', 'pem', 'crt', 'key'}
CONFIGURATION_EXTENSIONS = {'conf', 'cfg', 'config'}
VIRTUAL_ENV_EXTENSIONS = {'venv', 'env'}
NODE_MODULES = {'node_modules'}
PYTHON_BYTECODE = {'pyo'}
PACKAGE_LOCKS = {'package-lock.json', 'yarn.lock', 'Gemfile.lock'}
LOG_FILES = {'err', 'stderr', 'stdout', 'log',}
CACHE_FILES = {'cache', 'cached'}

# Combine all extensions into a single set for exclusion
ALL_EXTENSIONS = (MEDIA_EXTENSIONS | OFFICE_EXTENSIONS | SYSTEM_EXTENSIONS | EXECUTABLE_EXTENSIONS |
                  ARCHIVE_EXTENSIONS | AUDIO_EXTENSIONS | VIDEO_EXTENSIONS | DATABASE_EXTENSIONS |
                  FONT_EXTENSIONS | TEMPORARY_EXTENSIONS | COMPILED_CODE_EXTENSIONS | CERTIFICATE_EXTENSIONS |
                  CONFIGURATION_EXTENSIONS | VIRTUAL_ENV_EXTENSIONS | NODE_MODULES | PYTHON_BYTECODE |
                  PACKAGE_LOCKS | LOG_FILES | CACHE_FILES)

def get_repo_name(repo_url):
    """Extract the repository name from the URL."""
    return repo_url.strip().split('/')[-1].replace('.git', '')

def clone_repository(repo_url, temp_dir):
    """Clone the repository into a temporary directory."""
    subprocess.run(['git', 'clone', repo_url, temp_dir], check=True)

def get_file_list(temp_dir, excluded_extensions):
    """Walk the directory tree to get the list of files excluding certain extensions, .git, and .github directories."""
    file_list = []
    for root, dirs, files in os.walk(temp_dir):
        dirs[:] = [d for d in dirs if d not in {'.git', '.github'}]  # Skip the .git and .github directories
        for file in files:
            if file.split('.')[-1] not in excluded_extensions:
                file_list.append(os.path.join(root, file))
    return file_list

def remove_comments(content, file_extension):
    """Remove comments from the content based on the file extension."""
    pattern = COMMENT_PATTERNS.get(file_extension)
    if pattern:
        content = re.sub(pattern, '', content, flags=re.MULTILINE)
    return content

def write_to_union_file(file_list, repo_name, remove_comments_flag):
    """Write the files into a single text file with a consistent naming convention."""
    union_filename = f'{repo_name}_all_files.txt'
    with open(union_filename, 'w', encoding='utf-8') as union_file:
        union_file.write(f'## {repo_name}\n')
        for file_path in file_list:
            filename = os.path.basename(file_path)
            file_extension = filename.split('.')[-1]
            union_file.write(f'### {filename}\n')
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
                if remove_comments_flag:
                    content = remove_comments(content, file_extension)
                union_file.write(content)
                union_file.write('\n### end of file\n')
    return union_filename

def main():
    """Main function to execute the script."""
    parser = argparse.ArgumentParser(description='Clone a repo and compile its contents into a single file.')
    parser.add_argument('repo_url', type=str, help='GitHub repository URL (SSH)')
    parser.add_argument('-r', '--remove', action='store_true', help='Remove comments from code files')
    parser.add_argument('--skip-media', action='store_true', help='Skip media files')
    parser.add_argument('--skip-office', action='store_true', help='Skip office files')
    parser.add_argument('--skip-system', action='store_true', help='Skip system files')
    parser.add_argument('--skip-executables', action='store_true', help='Skip executable files')
    parser.add_argument('--skip-archive', action='store_true', help='Skip archive files')
    parser.add_argument('--skip-audio', action='store_true', help='Skip audio files')
    parser.add_argument('--skip-video', action='store_true', help='Skip video files')
    parser.add_argument('--skip-database', action='store_true', help='Skip database files')
    parser.add_argument('--skip-font', action='store_true', help='Skip font files')
    parser.add_argument('--skip-temporary', action='store_true', help='Skip temporary files')
    parser.add_argument('--skip-compiled-code', action='store_true', help='Skip compiled code files')
    parser.add_argument('--skip-certificate', action='store_true', help='Skip certificate files')
    parser.add_argument('--skip-configuration', action='store_true', help='Skip configuration files')
    parser.add_argument('--skip-virtual-env', action='store_true', help='Skip virtual environment files')
    parser.add_argument('--skip-node-modules', action='store_true', help='Skip node modules')
    parser.add_argument('--skip-python-bytecode', action='store_true', help='Skip Python bytecode files')
    parser.add_argument('--skip-package-locks', action='store_true', help='Skip package lock files')
    parser.add_argument('--skip-log-files', action='store_true', help='Skip log files')
    parser.add_argument('--skip-cache-files', action='store_true', help='Skip cache files')
    args = parser.parse_args()

    excluded_extensions = set()

    if args.skip_media:
        excluded_extensions |= MEDIA_EXTENSIONS
    if args.skip_office:
        excluded_extensions |= OFFICE_EXTENSIONS
    if args.skip_system:
        excluded_extensions |= SYSTEM_EXTENSIONS
    if args.skip_executables:
        excluded_extensions |= EXECUTABLE_EXTENSIONS
    if args.skip_archive:
        excluded_extensions |= ARCHIVE_EXTENSIONS
    if args.skip_audio:
        excluded_extensions |= AUDIO_EXTENSIONS
    if args.skip_video:
        excluded_extensions |= VIDEO_EXTENSIONS
    if args.skip_database:
        excluded_extensions |= DATABASE_EXTENSIONS
    if args.skip_font:
        excluded_extensions |= FONT_EXTENSIONS
    if args.skip_temporary:
        excluded_extensions |= TEMPORARY_EXTENSIONS
    if args.skip_compiled_code:
        excluded_extensions |= COMPILED_CODE_EXTENSIONS
    if args.skip_certificate:
        excluded_extensions |= CERTIFICATE_EXTENSIONS
    if args.skip_configuration:
        excluded_extensions |= CONFIGURATION_EXTENSIONS
    if args.skip_virtual_env:
        excluded_extensions |= VIRTUAL_ENV_EXTENSIONS
    if args.skip_node_modules:
        excluded_extensions |= NODE_MODULES
    if args.skip_python_bytecode:
        excluded_extensions |= PYTHON_BYTECODE
    if args.skip_package_locks:
        excluded_extensions |= PACKAGE_LOCKS
    if args.skip_log_files:
        excluded_extensions |= LOG_FILES
    if args.skip_cache_files:
        excluded_extensions |= CACHE_FILES

    repo_name = get_repo_name(args.repo_url)
    temp_dir = f'tmp_{repo_name}'
    try:
        clone_repository(args.repo_url, temp_dir)
        file_list = get_file_list(temp_dir, excluded_extensions)
        union_filename = write_to_union_file(file_list, repo_name, args.remove)
        print(f'All files have been written to {union_filename}')
    finally:
        try:
            shutil.rmtree(temp_dir)
        except OSError as e:
            print(f'Error: {e.strerror} - {e.filename}')

if __name__ == '__main__':
    main()
