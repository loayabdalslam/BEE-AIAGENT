"""
Git operations module for the AI Code Agent.
"""
import logging
from typing import Dict, List, Optional, Union
from pathlib import Path
import git
from git import Repo

from config import COMMIT_MESSAGE_PREFIX

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GitManager:
    """
    Responsible for managing Git operations.
    """

    def __init__(self, repo_path: Optional[Union[str, Path]] = None):
        """
        Initialize the Git manager.

        Args:
            repo_path: Path to the Git repository
        """
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()
        self.repo = None

        # Try to load the repository
        try:
            self.repo = Repo(self.repo_path)
            logger.info(f"Loaded Git repository at {self.repo_path}")
        except (git.InvalidGitRepositoryError, git.NoSuchPathError):
            logger.info(f"No Git repository found at {self.repo_path}")

    def init_repo(self) -> Dict:
        """
        Initialize a new Git repository.

        Returns:
            Dictionary with initialization results
        """
        if self.repo:
            return {
                "success": False,
                "message": f"Repository already exists at {self.repo_path}"
            }

        try:
            self.repo = Repo.init(self.repo_path)
            logger.info(f"Initialized new Git repository at {self.repo_path}")
            return {
                "success": True,
                "message": f"Initialized new Git repository at {self.repo_path}"
            }
        except Exception as e:
            logger.error(f"Error initializing repository: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def add_files(self, file_paths: Optional[List[Union[str, Path]]] = None) -> Dict:
        """
        Add files to the Git staging area.

        Args:
            file_paths: List of file paths to add (None for all files)

        Returns:
            Dictionary with add results
        """
        if not self.repo:
            return {
                "success": False,
                "message": "No Git repository found"
            }

        try:
            if file_paths:
                # Add specific files
                for file_path in file_paths:
                    self.repo.git.add(str(file_path))
                logger.info(f"Added {len(file_paths)} files to staging area")
            else:
                # Add all files
                self.repo.git.add(A=True)
                logger.info("Added all files to staging area")

            return {
                "success": True,
                "message": f"Added files to staging area"
            }
        except Exception as e:
            logger.error(f"Error adding files: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def commit(self, message: str, add_all: bool = True, timeout: int = 30) -> Dict:
        """
        Commit changes to the repository.

        Args:
            message: Commit message
            add_all: Whether to add all files before committing
            timeout: Timeout in seconds for Git operations

        Returns:
            Dictionary with commit results
        """
        if not self.repo:
            return {
                "success": False,
                "message": "No Git repository found"
            }

        try:
            import threading

            # Create a result container
            result = {"success": False, "error": "Timeout exceeded"}

            # Define the commit operation
            def do_commit():
                nonlocal result
                try:
                    # Add files if requested
                    if add_all:
                        self.repo.git.add(A=True)

                    # Add prefix to commit message
                    full_message = f"{COMMIT_MESSAGE_PREFIX} {message}"

                    # Commit changes
                    commit = self.repo.index.commit(full_message)
                    logger.info(f"Committed changes with message: {full_message}")

                    # Update result
                    result = {
                        "success": True,
                        "message": f"Committed changes with message: {full_message}",
                        "commit_hash": commit.hexsha
                    }
                except Exception as e:
                    logger.error(f"Error committing changes: {e}")
                    result = {
                        "success": False,
                        "error": str(e)
                    }

            # Create and start the thread
            commit_thread = threading.Thread(target=do_commit)
            commit_thread.daemon = True  # Allow the thread to be terminated when the main program exits
            commit_thread.start()

            # Wait for the thread to complete or timeout
            commit_thread.join(timeout)

            # Check if the thread is still alive (timeout occurred)
            if commit_thread.is_alive():
                logger.warning(f"Git commit operation timed out after {timeout} seconds")
                return {
                    "success": False,
                    "error": f"Git commit operation timed out after {timeout} seconds"
                }

            return result
        except Exception as e:
            logger.error(f"Error committing changes: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def create_branch(self, branch_name: str, checkout: bool = True) -> Dict:
        """
        Create a new branch.

        Args:
            branch_name: Name of the branch to create
            checkout: Whether to checkout the new branch

        Returns:
            Dictionary with branch creation results
        """
        if not self.repo:
            return {
                "success": False,
                "message": "No Git repository found"
            }

        try:
            # Create the branch
            new_branch = self.repo.create_head(branch_name)
            logger.info(f"Created new branch: {branch_name}")

            # Checkout the branch if requested
            if checkout:
                new_branch.checkout()
                logger.info(f"Checked out branch: {branch_name}")

            return {
                "success": True,
                "message": f"Created branch: {branch_name}" + (f" and checked it out" if checkout else "")
            }
        except Exception as e:
            logger.error(f"Error creating branch: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def checkout_branch(self, branch_name: str) -> Dict:
        """
        Checkout a branch.

        Args:
            branch_name: Name of the branch to checkout

        Returns:
            Dictionary with checkout results
        """
        if not self.repo:
            return {
                "success": False,
                "message": "No Git repository found"
            }

        try:
            # Check if the branch exists
            if branch_name not in [b.name for b in self.repo.heads]:
                return {
                    "success": False,
                    "message": f"Branch {branch_name} does not exist"
                }

            # Checkout the branch
            self.repo.git.checkout(branch_name)
            logger.info(f"Checked out branch: {branch_name}")

            return {
                "success": True,
                "message": f"Checked out branch: {branch_name}"
            }
        except Exception as e:
            logger.error(f"Error checking out branch: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_status(self) -> Dict:
        """
        Get the status of the repository.

        Returns:
            Dictionary with repository status
        """
        if not self.repo:
            return {
                "success": False,
                "message": "No Git repository found"
            }

        try:
            # Get current branch
            current_branch = self.repo.active_branch.name

            # Get status
            status = self.repo.git.status(porcelain=True)

            # Parse status
            untracked_files = []
            modified_files = []
            staged_files = []

            for line in status.split('\n'):
                if not line.strip():
                    continue

                status_code = line[:2]
                file_path = line[3:]

                if status_code.startswith('??'):
                    untracked_files.append(file_path)
                elif status_code.startswith('M'):
                    modified_files.append(file_path)
                elif status_code.startswith('A'):
                    staged_files.append(file_path)

            return {
                "success": True,
                "current_branch": current_branch,
                "untracked_files": untracked_files,
                "modified_files": modified_files,
                "staged_files": staged_files,
                "is_clean": len(status.strip()) == 0
            }
        except Exception as e:
            logger.error(f"Error getting repository status: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def push(self, remote: str = "origin", branch: Optional[str] = None) -> Dict:
        """
        Push changes to a remote repository.

        Args:
            remote: Name of the remote repository
            branch: Name of the branch to push (None for current branch)

        Returns:
            Dictionary with push results
        """
        if not self.repo:
            return {
                "success": False,
                "message": "No Git repository found"
            }

        try:
            # Get current branch if not specified
            if not branch:
                branch = self.repo.active_branch.name

            # Check if remote exists
            try:
                self.repo.remote(remote)
            except ValueError:
                return {
                    "success": False,
                    "message": f"Remote {remote} does not exist"
                }

            # Push changes
            push_info = self.repo.git.push(remote, branch)
            logger.info(f"Pushed changes to {remote}/{branch}")

            return {
                "success": True,
                "message": f"Pushed changes to {remote}/{branch}",
                "push_info": push_info
            }
        except Exception as e:
            logger.error(f"Error pushing changes: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def pull(self, remote: str = "origin", branch: Optional[str] = None) -> Dict:
        """
        Pull changes from a remote repository.

        Args:
            remote: Name of the remote repository
            branch: Name of the branch to pull (None for current branch)

        Returns:
            Dictionary with pull results
        """
        if not self.repo:
            return {
                "success": False,
                "message": "No Git repository found"
            }

        try:
            # Get current branch if not specified
            if not branch:
                branch = self.repo.active_branch.name

            # Check if remote exists
            try:
                self.repo.remote(remote)
            except ValueError:
                return {
                    "success": False,
                    "message": f"Remote {remote} does not exist"
                }

            # Pull changes
            pull_info = self.repo.git.pull(remote, branch)
            logger.info(f"Pulled changes from {remote}/{branch}")

            return {
                "success": True,
                "message": f"Pulled changes from {remote}/{branch}",
                "pull_info": pull_info
            }
        except Exception as e:
            logger.error(f"Error pulling changes: {e}")
            return {
                "success": False,
                "error": str(e)
            }
