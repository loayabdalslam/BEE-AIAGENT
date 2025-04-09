"""
Utility functions for the AI Code Agent.
"""
import logging
import os
import json
import re
from typing import Dict, List, Optional, Union
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_project_description(description: str) -> Dict:
    """
    Parse a project description to extract key information.

    Args:
        description: Project description text

    Returns:
        Dictionary with extracted information
    """
    # Extract project name
    project_name_match = re.search(r'project name:?\s*([^\n]+)', description, re.IGNORECASE)
    project_name = project_name_match.group(1).strip() if project_name_match else "unnamed-project"

    # Extract technologies
    technologies = []
    tech_match = re.search(r'technologies?:?\s*([^\n]+)', description, re.IGNORECASE)
    if tech_match:
        tech_text = tech_match.group(1).strip()
        technologies = [tech.strip() for tech in re.split(r'[,;]', tech_text)]

    # Extract features
    features = []
    feature_section = re.search(r'features?:?\s*(.+?)(?:\n\n|\n[A-Z]|$)', description, re.IGNORECASE | re.DOTALL)
    if feature_section:
        feature_text = feature_section.group(1).strip()
        # Extract features as bullet points or numbered items
        feature_items = re.findall(r'(?:^|\n)(?:[-*]|\d+\.)\s*([^\n]+)', feature_text)
        if feature_items:
            features = [item.strip() for item in feature_items]
        else:
            # If no bullet points, split by newlines
            features = [line.strip() for line in feature_text.split('\n') if line.strip()]

    return {
        "project_name": project_name,
        "technologies": technologies,
        "features": features,
        "raw_description": description
    }

def detect_language_from_file(file_path: Union[str, Path]) -> str:
    """
    Detect the programming language of a file based on its extension.

    Args:
        file_path: Path to the file

    Returns:
        Detected programming language
    """
    file_path = Path(file_path)
    extension = file_path.suffix.lower()

    language_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "jsx",
        ".tsx": "tsx",
        ".html": "html",
        ".css": "css",
        ".scss": "scss",
        ".sass": "sass",
        ".java": "java",
        ".c": "c",
        ".cpp": "c++",
        ".h": "c",
        ".hpp": "c++",
        ".go": "go",
        ".rs": "rust",
        ".rb": "ruby",
        ".php": "php",
        ".sh": "bash",
        ".md": "markdown",
        ".json": "json",
        ".xml": "xml",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".sql": "sql",
        ".kt": "kotlin",
        ".swift": "swift",
        ".dart": "dart",
        ".r": "r",
        ".cs": "csharp"
    }

    return language_map.get(extension, "text")

def save_json(data: Dict, file_path: Union[str, Path]) -> bool:
    """
    Save data to a JSON file.

    Args:
        data: Data to save
        file_path: Path to the file

    Returns:
        True if successful, False otherwise
    """
    file_path = Path(file_path)

    try:
        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write to file
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved JSON data to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving JSON data to {file_path}: {e}")
        return False

def load_json(file_path: Union[str, Path]) -> Optional[Dict]:
    """
    Load data from a JSON file.

    Args:
        file_path: Path to the file

    Returns:
        Loaded data or None if an error occurred
    """
    file_path = Path(file_path)

    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return None

    try:
        # Read from file
        with open(file_path, 'r') as f:
            data = json.load(f)

        logger.info(f"Loaded JSON data from {file_path}")
        return data
    except Exception as e:
        logger.error(f"Error loading JSON data from {file_path}: {e}")
        return None

def format_command_output(output: Dict) -> str:
    """
    Format command execution output for display.

    Args:
        output: Command execution output dictionary

    Returns:
        Formatted output string
    """
    result = []

    # Add command
    result.append(f"$ {output.get('command', 'Unknown command')}")
    result.append("")

    # Add status
    if output.get("success", False):
        result.append("✅ Command executed successfully")
    else:
        result.append("❌ Command failed")

    # Add return code
    if "return_code" in output:
        result.append(f"Return code: {output['return_code']}")

    # Add stdout
    if "stdout" in output and output["stdout"]:
        result.append("")
        result.append("Standard output:")
        result.append("```")
        result.append(output["stdout"])
        result.append("```")

    # Add stderr
    if "stderr" in output and output["stderr"]:
        result.append("")
        result.append("Standard error:")
        result.append("```")
        result.append(output["stderr"])
        result.append("```")

    # Add error
    if "error" in output:
        result.append("")
        result.append(f"Error: {output['error']}")

    return "\n".join(result)

def get_file_content(file_path: Union[str, Path]) -> Optional[str]:
    """
    Get the content of a file.

    Args:
        file_path: Path to the file

    Returns:
        File content or None if an error occurred
    """
    file_path = Path(file_path)

    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return None

    try:
        # Read from file
        with open(file_path, 'r') as f:
            content = f.read()

        return content
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return None

def extract_code_from_markdown(text: str) -> str:
    """
    Extract code from markdown code blocks.

    Args:
        text: Text that may contain markdown code blocks

    Returns:
        Extracted code or original text if no code blocks found
    """
    if "```" not in text:
        return text

    # Find the first code block
    code_block_start = text.find("```")
    if code_block_start < 0:
        return text

    # Find the end of the first line (which might contain the language)
    first_line_end = text.find("\n", code_block_start)
    if first_line_end < 0:
        return text

    # Find the closing code block
    code_block_end = text.find("```", first_line_end)
    if code_block_end < 0:
        return text

    # Extract just the code content, skipping the language identifier line if present
    if text[code_block_start:first_line_end].strip() != "```":
        # There's a language tag, so skip the first line
        code_start = first_line_end + 1
    else:
        # No language tag, start right after the opening ```
        code_start = code_block_start + 3

    return text[code_start:code_block_end].strip()

def find_files_by_extension(directory: Union[str, Path], extensions: List[str]) -> List[Path]:
    """
    Find all files with the specified extensions in a directory.

    Args:
        directory: Directory to search
        extensions: List of file extensions to find

    Returns:
        List of file paths
    """
    directory = Path(directory)

    if not directory.exists() or not directory.is_dir():
        logger.error(f"Directory not found: {directory}")
        return []

    # Normalize extensions to include the dot
    normalized_extensions = [ext if ext.startswith('.') else f'.{ext}' for ext in extensions]

    result = []

    for root, _, files in os.walk(directory):
        for file in files:
            file_path = Path(root) / file

            if any(file_path.suffix.lower() == ext.lower() for ext in normalized_extensions):
                result.append(file_path)

    return result
