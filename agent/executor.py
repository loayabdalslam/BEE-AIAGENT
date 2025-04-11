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
from agent.package_handler import PackageHandler

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

    def execute_command(self, command: str, capture_output: bool = True, timeout: int = 600) -> Dict:
        """
        Execute a shell command.

        Args:
            command: Command to execute
            capture_output: Whether to capture and return command output
            timeout: Timeout in seconds (default: 10 minutes)

        Returns:
            Dictionary with command execution results
        """
        logger.info(f"Executing command: {command}")
        self.command_history.append(command)

        # Check if this is a known project creation command that should be avoided
        is_code_generator = any(cmd in command for cmd in [
            "create-react-app",
            "npx create-",
            "yarn create",
            "django-admin startproject",
            "rails new",
            "vue create",
            "ng new"
        ])

        # Warn about code generators and suggest manual file creation instead
        if is_code_generator:
            logger.warning(f"Code generator command detected: {command}")
            logger.warning("Code generators should be avoided in favor of direct file creation.")
            print(f"\n[WARNING] Code generator command detected: {command}")
            print("This type of command should be avoided in favor of direct file creation.")
            print("The agent will proceed, but consider modifying your approach to use direct file creation instead.\n")

        # Check if this is a known project creation command
        is_project_creation = is_code_generator or any(cmd in command for cmd in [
            "npm init -y",
            "cargo init",
            "mvn archetype:generate"
        ])

        # Check if this is a known long-running command
        is_long_running = is_project_creation or any(cmd in command for cmd in [
            "npm install",
            "yarn install",
            "pip install",
            "mvn install",
            "gradle build",
            "cargo build"
        ])

        # Handle project creation commands specially
        if is_project_creation:
            # Extract the project name from the command
            project_name = self._extract_project_name_from_command(command)

            # Check if we're already in a directory with that name
            current_dir_name = Path(self.working_dir).name

            if project_name and project_name != current_dir_name:
                logger.info(f"Project creation command detected. Project name: {project_name}")
                logger.info(f"Current directory: {current_dir_name}")

                # If we're not in a directory with the project name, we have two options:
                # 1. Change the command to create in the current directory
                # 2. Change our working directory to the parent and let the command create a new directory

                # Option 1: Modify the command to create in the current directory
                if "create-react-app" in command or "npx create-" in command:
                    # For React apps, we can use '.' to create in the current directory
                    modified_command = command.replace(project_name, ".")
                    logger.info(f"Modified command to create in current directory: {modified_command}")
                    command = modified_command
                    print(f"\nModified command to create in current directory: {command}")

        if is_long_running:
            logger.info(f"Detected long-running command: {command}")
            logger.info("This may take several minutes. Please be patient...")
            print(f"\nExecuting long-running command: {command}")
            print("This may take several minutes. Please be patient...\n")

        try:
            # For long-running commands, show output in real-time
            if is_long_running and not capture_output:
                process = subprocess.Popen(
                    command,
                    shell=True,
                    cwd=self.working_dir,
                    text=True
                )
                process.wait(timeout=timeout)

                result = {
                    "command": command,
                    "return_code": process.returncode,
                    "success": process.returncode == 0,
                    "long_running": True
                }

                return result

            # For normal commands or when capturing output
            process = subprocess.run(
                command,
                shell=True,
                cwd=self.working_dir,
                capture_output=capture_output,
                text=True,
                timeout=timeout
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
        except subprocess.TimeoutExpired:
            logger.warning(f"Command timed out after {timeout} seconds: {command}")
            return {
                "command": command,
                "error": f"Command timed out after {timeout} seconds",
                "success": False,
                "timed_out": True
            }
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

            # Ensure package files are created based on project type
            package_handler = PackageHandler(self.working_dir)
            package_results = package_handler.ensure_package_files(structure)

            # Add package files to results
            results["created_files"].extend(package_results.get("created_files", []))
            results["errors"].extend(package_results.get("errors", []))

            return results
        except Exception as e:
            logger.error(f"Error setting up project structure: {e}")
            results["errors"].append(f"General error: {str(e)}")
            return results

    def _extract_project_name_from_command(self, command: str) -> Optional[str]:
        """
        Extract the project name from a project creation command.

        Args:
            command: The command string

        Returns:
            The project name or None if it couldn't be extracted
        """
        # For create-react-app and similar commands
        if "create-react-app" in command or "npx create-" in command:
            parts = command.split()
            # The last part is usually the project name
            for part in reversed(parts):
                # Skip options (starting with -)
                if not part.startswith("-") and part != "create-react-app" and "npx" not in part and "create-" not in part:
                    return part

        # For django-admin startproject
        if "django-admin startproject" in command:
            parts = command.split()
            try:
                idx = parts.index("startproject")
                if idx + 1 < len(parts):
                    return parts[idx + 1]
            except ValueError:
                pass

        # For cargo init
        if "cargo init" in command:
            parts = command.split()
            # Check if there's a name after 'init'
            try:
                idx = parts.index("init")
                if idx + 1 < len(parts) and not parts[idx + 1].startswith("--"):
                    return parts[idx + 1]
            except ValueError:
                pass

        return None

    def get_command_history(self) -> List[str]:
        """
        Get the history of executed commands.

        Returns:
            List of executed commands
        """
        return self.command_history
