# RepoHarvester

## Overview
RepoHarvester is a Python utility designed to clone a GitHub repository and compile all non-media files into a single text file. It's particularly useful for code analysis, backups, or when you need an offline version of the repository's text-based content.

## Features
- **Selective Cloning**: Clones the repository and excludes media files based on their extensions.
- **Comment Removal**: Offers an option to remove comments from code files, supporting multiple programming languages.
- **Single File Output**: Compiles all text-based files into a single, well-organized text file.

## Installation
Clone the RepoHarvester repository or download the `repoharvester.py` script. Ensure you have Python installed on your system.

## Usage
Run the script using the following command:

```shell
python repoharvester.py <repo_url> [--remove]
```
- <repo_url>: The SSH URL of the GitHub repository.
- `--remove` \ `-r` (optional): Include this flag if you want to remove comments from the code files.

### Arguments
- `repo_url``: The SSH URL of the GitHub repository to clone.
- `-r, --remove`: Remove comments from code files.
- `--skip-media`: Skip media files.
- `--skip-office`: Skip office files.
- `--skip-system`: Skip system files.
- `--skip-executables`: Skip executable files.
- `--skip-archive`: Skip archive files.
- `--skip-audio`: Skip audio files.
- `--skip-video`: Skip video files.
- `--skip-database`: Skip database files.
- `--skip-font`: Skip font files.
- `--skip-temporary`: Skip temporary files.
- `--skip-compiled-code`: Skip compiled code files.
- `--skip-certificate`: Skip certificate files.
- `--skip-configuration`: Skip configuration files.
- `--skip-virtual-env`: Skip virtual environment files.
- `--skip-node-modules`: Skip node modules.
- `--skip-python-bytecode`: Skip Python bytecode files.
- `--skip-package-locks`: Skip package lock files.
- `--skip-log-files`: Skip log files.
- `--skip-cache-files`: Skip cache files.

### Example
This command will clone the repository at git@github.com:username/repo.git, remove comments from code files, skip media files, and compile the remaining files into a single file named repo_all_files.txt:
```bash
python repoharvester.py git@github.com:username/repo.git --remove --skip-media
```


## File Types Supported
The script excludes the following media file extensions by default:

png, jpg, jpeg, gif, bmp, tiff, svg, xlsx, xls, pack, idx, log, DS_Store

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

## Output Format
The generated text file will have the following structure:
```
## <name_of_repository>
### <filename>.<file_extension>
<content_of_the_file>
### end of file
...
```

## Contributing
Contributions to RepoHarvester are welcome! Please read our contributing guidelines to get started.

## License
RepoHarvester is released under the MIT License. See the LICENSE file for more details.
