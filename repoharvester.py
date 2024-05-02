# import os
# import shutil
# import subprocess
#
#
# # Function to get the list of all files in a git repository
# def get_file_list(repo_url):
#     # Clone the repository into a temporary directory
#     repo_name = repo_url.split('/')[-1]
#     temp_dir = f'tmp_{repo_name}'
#     subprocess.run(['git', 'clone', repo_url, temp_dir], check=True)
#
#     # Walk the directory tree to get the list of files
#     file_list = []
#     for root, dirs, files in os.walk(temp_dir):
#         for file in files:
#             if file.split('.')[-1] not in ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'svg', 'xlsx', 'xls', 'pack']:  # Exclude media files
#                 file_list.append(os.path.join(root, file))
#     return file_list, repo_name, temp_dir
#
#
# # Function to write the files into a single text file
# def write_to_union_file(file_list, repo_name):
#     union_filename = f'union file: {repo_name} + alltogether.txt'
#     with open(union_filename, 'wb') as union_file:
#         union_file.write(f'## {repo_name}\n'.encode('utf-8'))
#         for file_path in file_list:
#             try:
#                 with open(file_path, 'rb') as file:
#                     content = file.read()
#                     # Attempt to decode with utf-8, ignore errors
#                     content = content.decode('utf-8', 'ignore')
#                     filename = os.path.basename(file_path)
#                     file_info = f'### {filename}\n{content}\n### end of file\n'
#                     union_file.write(file_info.encode('utf-8'))
#             except Exception as e:
#                 print(f'Error processing file {file_path}: {e}')
#     return union_filename
#
#
# # Main function to execute the script
# def main():
#     repo_url = input('Enter the GitHub repository URL (SSH): ')
#     file_list, repo_name, temp_dir = get_file_list(repo_url)
#     try:
#         union_filename = write_to_union_file(file_list, repo_name)
#         print(f'All files have been written to {union_filename}')
#     except Exception as e:
#         print(f'An error occurred: {e}')
#     finally:
#         # delete the temporary directory
#         shutil.rmtree(temp_dir)
#
#
#
# if __name__ == '__main__':
#     main()
import os
import shutil
import subprocess

EXCLUDED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'svg', 'xlsx', 'xls', 'pack', 'idx', 'log'}

def get_repo_name(repo_url):
    """Extract the repository name from the URL."""
    return repo_url.split('/')[-1].replace('.git', '')

def clone_repository(repo_url, temp_dir):
    """Clone the repository into a temporary directory."""
    subprocess.run(['git', 'clone', repo_url, temp_dir], check=True)

def get_file_list(temp_dir):
    """Walk the directory tree to get the list of files excluding certain extensions."""
    file_list = []
    for root, dirs, files in os.walk(temp_dir):
        for file in files:
            if file.split('.')[-1] not in EXCLUDED_EXTENSIONS:
                file_list.append(os.path.join(root, file))
    return file_list

def write_to_union_file(file_list, repo_name):
    """Write the files into a single text file with a consistent naming convention."""
    union_filename = f'{repo_name}_all_files.txt'
    with open(union_filename, 'w', encoding='utf-8') as union_file:
        union_file.write(f'## {repo_name}\n')
        for file_path in file_list:
            filename = os.path.basename(file_path)
            union_file.write(f'### {filename}\n')
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
                union_file.write(content)
                union_file.write('\n### end of file\n')
    return union_filename

def main():
    """Main function to execute the script."""
    repo_url = input('Enter the GitHub repository URL (SSH): ')
    repo_name = get_repo_name(repo_url)
    temp_dir = f'tmp_{repo_name}'
    try:
        clone_repository(repo_url, temp_dir)
        file_list = get_file_list(temp_dir)
        union_filename = write_to_union_file(file_list, repo_name)
        print(f'All files have been written to {union_filename}')
    finally:
        try:
            shutil.rmtree(temp_dir)
        except OSError as e:
            print(f'Error: {e.strerror} - {e.filename}')

if __name__ == '__main__':
    main()
