# RepoHarvester

## Overview
RepoHarvester is a Python utility designed to clone a GitHub repository and compile all non-media files into a single text file. It's particularly useful for code analysis, backups, or when you need an offline version of the repository's text-based content.

## Features
- **Selective Cloning**: Clones a GitHub repository and intelligently excludes non-essential file types (e.g., media, system files).
- **Comment Removal**: Provides an option to remove comments from code files, supporting commonly used programming languages.
- **Flexible Exclusions**: Allows customization of excluded file types using the --no-skip command-line argument.
- **Maximum File Size Control**: Implements size restrictions for included files:
- - Files larger than a specified threshold (`--max-size`) are automatically skipped.
- - Files exceeding 500KB but smaller than the maximum size are logged for awareness.
- **Folder Exclusion**: Exclude specific folders and their contents using the --exclude option.
- **Single File Output**: Compiles relevant files into a unified, well-structured text file.
- **Logging**: Detailed logs, including file processing information, are saved to the specified log file (--log option).

## Installation
1. Ensure you have Python (https://www.python.org/) and Git (https://git-scm.com/) installed.
2. Clone the RepoHarvester repository or download the repoharvester.py and comment_pattens.py.


## Usage
Run the script using the following command:

```shell
python repoharvester.py <repo_url> [options]
```

- `repo_url` : (Required): The SSH URL of the GitHub repository to clone.
- `--remove` \ `-r` (Optional): Removes comments from supported code files.
- `--no-skip` (Optional): Includes specified file groups that would otherwise be excluded.
- - **Available groups**: media, office, system, executables, archive, audio, video, database, font, temporary, compiled_code, certificate, configuration, virtual_env, node_modules, python_bytecode, package_locks, log_files, cache_files
- `--max-size` (Optional):  Set the maximum file size in KB (default: 1000 KB). **Files exceeding this size are skipped**. Files larger than 500KB but within the limit are logged.
- `--log` (Optional): Path to the log file (default: output/union_file.log)
- `--exclude`(Optional): Specify folders to exclude (and their contents).
### Arguments
- `repo_url``: The SSH URL of the GitHub repository to clone.
- `-r, --remove`: Remove comments from code files office files.
- `--skip`: Skip files of certain types. You can specify multiple types separated by spaces. Available types are: media, office, system, executables, archive, audio, video, database, font, temporary, compiled_code, certificate, configuration, virtual_env, node_modules, python_bytecode, package_locks, log_files, cache_files.
### Example
This command:
- Clones the specified repository.
- Removes comments from code files.
- Includes media and office files.
- Sets the maximum allowed file size to 250KB.
- Exclude folder `vendor`

```bash
python repoharvester.py git@github.com:username/repo.git --remove --no-skip media office --max-size 250 --exclude vendor
```

## Default Excluded File Types

RepoHarvester excludes many common file types by default. These include but are not limited to:

- Media files: png, jpg, jpeg, gif, bmp, tiff, svg, ico, raw, psd, ai
- Office documents: xlsx, xls, docx, pptx, pdf
- System files: pack, idx, log, DS_Store, sys, ini, bat, plist
- Executables: exe, dll, so, bin
- And many more…

- See the EXTENSION_GROUPS dictionary within the code for the complete list.


## Comment Patterns
The comment_patterns.py file contains regular expressions used to identify and remove comments from various programming languages:

```python
COMMENT_PATTERNS = {
    'py': r'#.*',  # Python
    'js': r'//.*|/\*[\s\S]*?\*/',  # JavaScript
    ...
    # Add more patterns for different file types as needed
}

```

### Output Format
The generated text file will have the following structure:
```
## <name_of_repository>
### <filename>.<file_extension>
<content_of_the_file>
### end of file
...
```
### Additional Notes:
- non-UTF-8 files are skipped and logged.
- A list of skipped files is saved to `output/skipped_files.txt`.
- The `--exclude` option allows for more granular control over which files are included.

### Contributing
Contributions to RepoHarvester are welcome! Please read our contributing guidelines to get started.

## License
RepoHarvester is released under the MIT License. See the LICENSE file for more details.
