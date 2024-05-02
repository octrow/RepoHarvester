import argparse
import os
import re
import shutil
import subprocess

from comment_pattens import COMMENT_PATTERNS

EXTENSION_GROUPS = {
    'media': {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'svg', 'ico', 'raw', 'psd', 'ai'},
    'office': {'xlsx', 'xls', 'docx', 'pptx', 'pdf'},
    'system': {'pack', 'idx', 'DS_Store', 'sys', 'ini', 'bat', 'plist'},
    'executables': {'exe', 'dll', 'so', 'bin'},
    'archive': {'zip', 'rar', '7z', 'tar', 'gz', 'bz2'},
    'audio': {'mp3', 'wav', 'aac', 'flac'},
    'video': {'mp4', 'avi', 'mov', 'wmv', 'flv'},
    'database': {'db', 'sqlitedb', 'mdb'},
    'font': {'ttf', 'otf', 'woff', 'woff2'},
    'temporary': {'tmp', 'temp', 'swp', 'swo'},
    'compiled_code': {'o', 'obj', 'pyc', 'class'},
    'certificate': {'cer', 'pem', 'crt', 'key'},
    'configuration': {'conf', 'cfg', 'config'},
    'virtual_env': {'venv', 'env'},
    'node_modules': {'node_modules'},
    'python_bytecode': {'pyo'},
    'package_locks': {'package-lock.json', 'yarn.lock', 'Gemfile.lock'},
    'log_files': {'err', 'stderr', 'stdout', 'log',},
    'cache_files': {'cache', 'cached'}
}
# # Define groups of file extensions
# MEDIA_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'svg', 'ico', 'raw', 'psd', 'ai'}
# OFFICE_EXTENSIONS = {'xlsx', 'xls', 'docx', 'pptx', 'pdf'}
# SYSTEM_EXTENSIONS = {'pack', 'idx', 'DS_Store', 'sys', 'ini', 'bat', 'plist'}
# EXECUTABLE_EXTENSIONS = {'exe', 'dll', 'so', 'bin'}
# ARCHIVE_EXTENSIONS = {'zip', 'rar', '7z', 'tar', 'gz', 'bz2'}
# AUDIO_EXTENSIONS = {'mp3', 'wav', 'aac', 'flac'}
# VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'wmv', 'flv'}
# DATABASE_EXTENSIONS = {'db', 'sqlitedb', 'mdb'}
# FONT_EXTENSIONS = {'ttf', 'otf', 'woff', 'woff2'}
# TEMPORARY_EXTENSIONS = {'tmp', 'temp', 'swp', 'swo'}
# COMPILED_CODE_EXTENSIONS = {'o', 'obj', 'pyc', 'class'}
# CERTIFICATE_EXTENSIONS = {'cer', 'pem', 'crt', 'key'}
# CONFIGURATION_EXTENSIONS = {'conf', 'cfg', 'config'}
# VIRTUAL_ENV_EXTENSIONS = {'venv', 'env'}
# NODE_MODULES = {'node_modules'}
# PYTHON_BYTECODE = {'pyo'}
# PACKAGE_LOCKS = {'package-lock.json', 'yarn.lock', 'Gemfile.lock'}
# LOG_FILES = {'err', 'stderr', 'stdout', 'log',}
# CACHE_FILES = {'cache', 'cached'}
#
# # Combine all extensions into a single set for exclusion
# ALL_EXTENSIONS = (MEDIA_EXTENSIONS | OFFICE_EXTENSIONS | SYSTEM_EXTENSIONS | EXECUTABLE_EXTENSIONS |
#                   ARCHIVE_EXTENSIONS | AUDIO_EXTENSIONS | VIDEO_EXTENSIONS | DATABASE_EXTENSIONS |
#                   FONT_EXTENSIONS | TEMPORARY_EXTENSIONS | COMPILED_CODE_EXTENSIONS | CERTIFICATE_EXTENSIONS |
#                   CONFIGURATION_EXTENSIONS | VIRTUAL_ENV_EXTENSIONS | NODE_MODULES | PYTHON_BYTECODE |
#                   PACKAGE_LOCKS | LOG_FILES | CACHE_FILES)

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
    parser.add_argument('--skip', nargs='+', help='Skip files of certain types')
    args = parser.parse_args()

    excluded_extensions = set()

    # Build the set of excluded extensions based on the selected categories
    if args.skip:
        for group in args.skip:
            if group in EXTENSION_GROUPS:
                excluded_extensions |= EXTENSION_GROUPS[group]

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
