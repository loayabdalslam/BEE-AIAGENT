"""
Code editor utilities for the AI Code Agent.
"""
import logging
import os
import platform
import subprocess
from pathlib import Path
from typing import Optional, Union

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def open_code_editor(project_dir: Union[str, Path]) -> bool:
    """
    Open the project directory in a code editor.
    
    Args:
        project_dir: Path to the project directory
        
    Returns:
        True if successful, False otherwise
    """
    project_dir = Path(project_dir)
    
    if not project_dir.exists() or not project_dir.is_dir():
        logger.error(f"Project directory not found: {project_dir}")
        return False
    
    try:
        # Determine the operating system
        system = platform.system()
        
        if system == "Windows":
            # Try VS Code first
            try:
                subprocess.Popen(["code", str(project_dir)], shell=True)
                logger.info(f"Opened VS Code with project: {project_dir}")
                return True
            except Exception as e:
                logger.warning(f"Failed to open VS Code: {e}")
                
                # Try other editors
                try:
                    os.startfile(str(project_dir))
                    logger.info(f"Opened default file explorer with project: {project_dir}")
                    return True
                except Exception as e:
                    logger.error(f"Failed to open project directory: {e}")
                    return False
        
        elif system == "Darwin":  # macOS
            # Try VS Code first
            try:
                subprocess.Popen(["code", str(project_dir)])
                logger.info(f"Opened VS Code with project: {project_dir}")
                return True
            except Exception as e:
                logger.warning(f"Failed to open VS Code: {e}")
                
                # Try opening with Finder
                try:
                    subprocess.Popen(["open", str(project_dir)])
                    logger.info(f"Opened Finder with project: {project_dir}")
                    return True
                except Exception as e:
                    logger.error(f"Failed to open project directory: {e}")
                    return False
        
        elif system == "Linux":
            # Try VS Code first
            try:
                subprocess.Popen(["code", str(project_dir)])
                logger.info(f"Opened VS Code with project: {project_dir}")
                return True
            except Exception as e:
                logger.warning(f"Failed to open VS Code: {e}")
                
                # Try other editors or file managers
                for cmd in ["xdg-open", "gnome-open", "kde-open"]:
                    try:
                        subprocess.Popen([cmd, str(project_dir)])
                        logger.info(f"Opened {cmd} with project: {project_dir}")
                        return True
                    except Exception:
                        continue
                
                logger.error("Failed to open project directory with any available command")
                return False
        
        else:
            logger.error(f"Unsupported operating system: {system}")
            return False
    
    except Exception as e:
        logger.error(f"Error opening code editor: {e}")
        return False
