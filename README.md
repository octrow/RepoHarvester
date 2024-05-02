# RepoHarvester

## Overview
RepoHarvester is a Python utility designed to clone a GitHub repository and compile all non-media files into a single text file. It's particularly useful for code analysis, backups, or when you need an offline version of the repository's text-based content.

## Features
- **Selective Cloning**: Clones the repository and excludes media files based on their extensions.
- **Comment Removal**: Offers an option to remove comments from code files, supporting multiple programming languages.
- **Flexible Exclusions**: Allows for fine-grained control over which types of files to exclude.
- **Single File Output**: Compiles all text-based files into a single, well-organized text file.

## Installation
Clone the RepoHarvester repository or download the `repoharvester.py` script. Ensure you have Python and Git installed on your system.

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
- `--skip-media`: Skip media files like images and audio.
- `--skip-office`: Skip office files such as documents and spreadsheets.
- `--skip-system`: Skip system-related files like logs and configurations.
- Additional flags are available for skipping executables, archives, audio, video, databases, fonts, temporary files, compiled code, certificates, configuration files, virtual environments, node modules, Python bytecode, package locks, log files, and cache files.

### Example
This command will clone the repository at git@github.com:username/repo.git, remove comments from code files, skip media files, and compile the remaining files into a single file named repo_all_files.txt:
```bash
python repoharvester.py git@github.com:username/repo.git --remove --skip-media
```

## Excluded File Types
By default, RepoHarvester excludes a wide range of file types that are typically not necessary for textual analysis. This includes but is not limited to:
The script excludes the following media file extensions by default:
- Media files: png, jpg, jpeg, gif, bmp, tiff, svg, ico, raw, psd, ai
- Office documents: xlsx, xls, docx, pptx, pdf
- System files: pack, idx, log, DS_Store, sys, ini, bat, plist
- And many more…

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
