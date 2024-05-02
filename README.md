# RepoHarvester

## Overview
RepoHarvester is a Python-based tool designed to streamline the process of downloading non-media files from a GitHub repository. It efficiently clones the repository, filters out media files, and compiles the content of text-based files into a single, easily accessible document.

## Features
- **Selective Downloading**: Downloads all non-media files (like `.md`, `.py`, etc.) from the specified repository.
- **Union File Creation**: Generates a single text file that includes the content of all downloaded files, organized by filename and format.
- **Easy to Use**: Simple command-line interface that prompts for the repository URL and handles the rest.

## Installation
Ensure that you have `git` installed on your system. Clone the RepoHarvester repository or download the `repoharvester.py` script directly to your local machine.

## Usage
Run the script using a Python interpreter:

\```shell
python repoharvester.py
\```

When prompted, enter the full URL of the GitHub repository you wish to download files from. The script will perform the following actions:
- Clone the repository to a temporary directory.
- Filter out and exclude media files.
- Compile the content of the remaining files into a single text file named `union file: <repo_name> + alltogether.txt`.

## Output Format
The generated text file will have the following structure:

\```
## <name_of_repository>
### <filename>.<file_extension>
<content_of_the_file>
### end of file
\```

This pattern repeats for each file downloaded from the repository.

## Contributing
Contributions to RepoHarvester are welcome! Please read our contributing guidelines to get started.

## License
RepoHarvester is released under the MIT License. See the LICENSE file for more details.
