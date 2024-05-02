COMMENT_PATTERNS = {
    'py': r'#.*',  # Python
    'js': r'//.*|/\*[\s\S]*?\*/',  # JavaScript
    'html': r'<!--.*?-->',  # HTML
    'css': r'/\*[\s\S]*?\*/',  # CSS
    'java': r'//.*|/\*[\s\S]*?\*/',  # Java
    'c': r'//.*|/\*[\s\S]*?\*/',  # C
    'cpp': r'//.*|/\*[\s\S]*?\*/',  # C++
    'cs': r'//.*|/\*[\s\S]*?\*/',  # C#
    'php': r'//.*|/\*[\s\S]*?\*/|#.*',  # PHP
    'rb': r'#.*',  # Ruby
    'go': r'//.*|/\*[\s\S]*?\*/',  # Go
    'swift': r'//.*|/\*[\s\S]*?\*/',  # Swift
    'kt': r'//.*|/\*[\s\S]*?\*/',  # Kotlin
    'rs': r'//.*|/\*[\s\S]*?\*/',  # Rust
    'lua': r'--.*',  # Lua
    'perl': r'#.*',  # Perl
    'r': r'#.*',  # R
    'sh': r'#.*',  # Shell Script
    'sql': r'--.*|/\*[\s\S]*?\*/',  # SQL
    'yaml': r'#.*',  # YAML
    'xml': r'<!--.*?-->',  # XML
    # Add more patterns for different file types as needed
}
