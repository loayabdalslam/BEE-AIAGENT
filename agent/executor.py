"""
Command execution module for the AI Code Agent.
"""
import logging
import subprocess
import os
import sys
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path

from models.gemini_client import GeminiClient
from agent.utils import extract_code_from_markdown

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Executor:
    """
    Responsible for executing commands and generating code.
    """

    def __init__(self, gemini_client: Optional[GeminiClient] = None, working_dir: Optional[Path] = None):
        """
        Initialize the executor.

        Args:
            gemini_client: GeminiClient instance for AI capabilities
            working_dir: Working directory for command execution
        """
        self.gemini_client = gemini_client or GeminiClient()
        self.working_dir = working_dir or Path.cwd()
        self.command_history = []

    def execute_command(self, command: str, capture_output: bool = True) -> Dict:
        """
        Execute a shell command.

        Args:
            command: Command to execute
            capture_output: Whether to capture and return command output

        Returns:
            Dictionary with command execution results
        """
        logger.info(f"Executing command: {command}")
        self.command_history.append(command)

        try:
            # Execute the command
            process = subprocess.run(
                command,
                shell=True,
                cwd=self.working_dir,
                capture_output=capture_output,
                text=True
            )

            result = {
                "command": command,
                "return_code": process.returncode,
                "success": process.returncode == 0
            }

            if capture_output:
                result["stdout"] = process.stdout
                result["stderr"] = process.stderr

            return result
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return {
                "command": command,
                "error": str(e),
                "success": False
            }

    def generate_file(self, file_path: Union[str, Path], content_description: str, language: Optional[str] = None) -> Dict:
        """
        Generate a file with AI-generated content.

        Args:
            file_path: Path to the file to create
            content_description: Description of the file content to generate
            language: Programming language for the file

        Returns:
            Dictionary with file generation results
        """
        file_path = Path(file_path)

        # Determine language from file extension if not provided
        if not language:
            extension = file_path.suffix.lower()
            language_map = {
                ".py": "python",
                ".js": "javascript",
                ".ts": "typescript",
                ".html": "html",
                ".css": "css",
                ".java": "java",
                ".c": "c",
                ".cpp": "c++",
                ".go": "go",
                ".rs": "rust",
                ".rb": "ruby",
                ".php": "php",
                ".sh": "bash",
                ".md": "markdown"
            }
            language = language_map.get(extension, "text")

        logger.info(f"Generating {language} file: {file_path}")

        try:
            # Create parent directories if they don't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Generate content
            content = self.gemini_client.generate_code(content_description, language)

            # Extract code from markdown if needed
            clean_content = extract_code_from_markdown(content)

            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(clean_content)

            return {
                "file_path": str(file_path),
                "language": language,
                "success": True,
                "content_preview": content[:200] + ("..." if len(content) > 200 else "")
            }
        except Exception as e:
            logger.error(f"Error generating file: {e}")
            return {
                "file_path": str(file_path),
                "error": str(e),
                "success": False
            }

    def setup_project_structure(self, structure: Dict) -> Dict:
        """
        Set up a project directory structure.

        Args:
            structure: Dictionary describing the project structure

        Returns:
            Dictionary with setup results
        """
        results = {
            "created_directories": [],
            "created_files": [],
            "errors": []
        }

        try:
            # Create directories
            for directory in structure.get("directories", []):
                dir_path = self.working_dir / directory
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    results["created_directories"].append(str(dir_path))
                except Exception as e:
                    results["errors"].append(f"Error creating directory {directory}: {str(e)}")

            # Create files
            for file_info in structure.get("files", []):
                try:
                    file_result = self.generate_file(
                        self.working_dir / file_info["path"],
                        file_info["description"],
                        file_info.get("language")
                    )

                    if file_result["success"]:
                        results["created_files"].append(file_result["file_path"])
                    else:
                        results["errors"].append(f"Error creating file {file_info['path']}: {file_result.get('error')}")
                except Exception as e:
                    results["errors"].append(f"Error processing file {file_info['path']}: {str(e)}")

            return results
        except Exception as e:
            logger.error(f"Error setting up project structure: {e}")
            results["errors"].append(f"General error: {str(e)}")
            return results

    def get_command_history(self) -> List[str]:
        """
        Get the history of executed commands.

        Returns:
            List of executed commands
        """
        return self.command_history
