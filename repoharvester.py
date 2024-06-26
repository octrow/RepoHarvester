import argparse
import logging
import os
import re
import shutil
import subprocess

from comment_pattens import COMMENT_PATTERNS

class RepoHarvester:
    def __init__(self):
        self.EXTENSION_GROUPS = {
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

    def _get_repo_name(self, repo_url):
        """Extract the repository name from the URL."""
        return repo_url.strip().split('/')[-1].replace('.git', '')


    def _clone_repository(self, repo_url, temp_dir):
        """Clone the repository into a temporary directory."""
        subprocess.run(['git', 'clone', repo_url, temp_dir], check=True)

    def _get_file_list(self, temp_dir, excluded_extensions, max_size, excluded_folders):
        """Walk the directory tree to get the list of files excluding certain extensions, .git, and .github directories."""
        file_list = []
        for root, dirs, files in os.walk(temp_dir, topdown=True):
            dirs[:] = [d for d in dirs if d not in {'.git', '.github'} and d not in excluded_folders]  # Skip the .git and .github directories
            for file in files:
                if file.split('.')[-1] not in excluded_extensions:
                    file_path = os.path.join(root, file)
                    file_size_kb = os.path.getsize(file_path) / 1024
                    if file_size_kb > max_size:
                        print(f"Skipping file larger than {max_size} KB: {file}, size: {file_size_kb} KB")
                        continue
                    elif file_size_kb > 500:
                        print(f"File larger than 500 KB: {file}, size: {file_size_kb} KB")
                    file_list.append(os.path.join(root, file))
        return file_list

    def _remove_comments(self, content, file_extension):
        """Remove comments from the content based on the file extension."""
        pattern = COMMENT_PATTERNS.get(file_extension)
        if pattern:
            content = re.sub(pattern, '', content, flags=re.MULTILINE)
        return content

    def _write_to_union_file(self, file_list, repo_name, remove_comments_flag, log_file):
        output_dir = 'output'
        skipped_files = f'{output_dir}/skipped_files.txt'
        os.makedirs(output_dir, exist_ok=True)
        union_filename = f'{output_dir}/{repo_name}_all_files.txt'

        with open(union_filename, 'w', encoding='utf-8') as union_file, \
             open(skipped_files, 'w', encoding='utf-8') as skipped_file:

            union_file.write(f'## {repo_name}\n')

            for file_path in file_list:
                filename = os.path.basename(file_path)
                file_extension = filename.split('.')[-1]
                file_size = os.path.getsize(file_path) / 1024  # Calculate file size in KB

                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        content = file.read()

                        if remove_comments_flag:
                            content = self._remove_comments(content, file_extension)

                        union_file.write(f'### {filename}\n')
                        union_file.write(content)
                        union_file.write('\n### end of file\n')

                        logging.info(f"{filename}, size: {file_size:.2f} KB")
                except UnicodeDecodeError:
                    print(f"Skipping non-UTF-8 file: {filename}")  # Log skipped file
                    skipped_file.write(f"{filename}\n")  # Write skipped file name to file

        return union_filename

    def run_from_command_line(self):
        parser = argparse.ArgumentParser(description='Clone a repo and compile its contents into a single file.')
        parser.add_argument('repo_url', type=str, help='GitHub repository URL (SSH)')
        parser.add_argument('-r', '--remove', action='store_true', help='Remove comments from code files')
        parser.add_argument('--no-skip', nargs='+', help='Do not skip files of these types')
        parser.add_argument('--max-size', type=int, default=1000, help='Maximum file size in KB')
        parser.add_argument('--log', type=str, default='output/union_file.log', help='Path to log file')
        parser.add_argument('--exclude', nargs='+', default=[], help='Exclude these folders (and their contents)')
        args = parser.parse_args()

        # Configure logging
        logging.basicConfig(filename=args.log, level=logging.INFO,
                            format='%(message)s')

        # Start by excluding all extensions
        excluded_extensions = set()
        for extensions in self.EXTENSION_GROUPS.values():
            excluded_extensions.update(extensions)

        # Remove excluded groups if specified in --no-skip
        if args.no_skip:
            for group in args.no_skip:
                if group in self.EXTENSION_GROUPS:
                    excluded_extensions -= self.EXTENSION_GROUPS[group]

        repo_name = self._get_repo_name(args.repo_url)
        temp_dir = f'tmp_{repo_name}'
        try:
            self._clone_repository(args.repo_url, temp_dir)
            file_list = self._get_file_list(temp_dir, excluded_extensions, args.max_size, args.exclude)
            union_filename = self._write_to_union_file(file_list, repo_name, args.remove, args.log)
            print(f'All files have been written to {union_filename}')
        finally:
            try:
                shutil.rmtree(temp_dir)
            except OSError as e:
                print(f'Error: {e.strerror} - {e.filename}')

    def run_from_gui(self, repo_url, remove_comments, excluded_extensions, max_size, exclude_folders, log_file_path='output/union_file.log'):
            # Configure logging
            logging.basicConfig(filename=log_file_path, level=logging.INFO, format='%(message)s')

            repo_name = self._get_repo_name(repo_url)
            temp_dir = f'tmp_{repo_name}'
            try:
                self._clone_repository(repo_url, temp_dir)
                file_list = self._get_file_list(temp_dir, excluded_extensions, max_size, exclude_folders)
                union_filename = self._write_to_union_file(file_list, repo_name, remove_comments, log_file_path)
                print(f'All files have been written to {union_filename}')
            finally:
                try:
                    shutil.rmtree(temp_dir)
                except OSError as e:
                    print(f'Error: {e.strerror} - {e.filename}')


if __name__ == '__main__':
    harvester = RepoHarvester()
    harvester.run_from_command_line()
