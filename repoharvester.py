import argparse
import os
import re
import shutil
import subprocess

from comment_pattens import COMMENT_PATTERNS

EXCLUDED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'svg', 'xlsx', 'xls', 'pack', 'idx', 'log', 'DS_Store'}


def get_repo_name(repo_url):
    """Extract the repository name from the URL."""
    return repo_url.strip().split('/')[-1].replace('.git', '')

def clone_repository(repo_url, temp_dir):
    """Clone the repository into a temporary directory."""
    subprocess.run(['git', 'clone', repo_url, temp_dir], check=True)

def get_file_list(temp_dir):
    """Walk the directory tree to get the list of files excluding certain extensions, .git, and .github directories."""
    file_list = []
    for root, dirs, files in os.walk(temp_dir):
        dirs[:] = [d for d in dirs if d not in {'.git', '.github'}]  # Skip the .git and .github directories
        for file in files:
            if file.split('.')[-1] not in EXCLUDED_EXTENSIONS:
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
    args = parser.parse_args()

    repo_name = get_repo_name(args.repo_url)
    temp_dir = f'tmp_{repo_name}'
    try:
        clone_repository(args.repo_url, temp_dir)
        file_list = get_file_list(temp_dir)
        union_filename = write_to_union_file(file_list, repo_name, args.remove)
        print(f'All files have been written to {union_filename}')
    finally:
        try:
            shutil.rmtree(temp_dir)
        except OSError as e:
            print(f'Error: {e.strerror} - {e.filename}')

if __name__ == '__main__':
    main()
