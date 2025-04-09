"""
Tests for the executor module.
"""
import pytest
import os
from unittest.mock import MagicMock, patch
from pathlib import Path

from agent.executor import Executor

@pytest.fixture
def mock_gemini_client():
    """Create a mock GeminiClient."""
    mock_client = MagicMock()
    mock_client.generate_code.return_value = "print('Hello, World!')"
    return mock_client

@pytest.fixture
def executor(mock_gemini_client, tmp_path):
    """Create an Executor instance with a mock client and temporary directory."""
    return Executor(mock_gemini_client, tmp_path)

def test_execute_command(executor):
    """Test executing a command."""
    # Mock subprocess.run
    with patch('subprocess.run') as mock_run:
        # Configure the mock
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "Command output"
        mock_process.stderr = ""
        mock_run.return_value = mock_process
        
        # Execute a command
        result = executor.execute_command("echo 'Hello, World!'")
        
        # Check that subprocess.run was called
        mock_run.assert_called_once()
        
        # Check the result
        assert result["success"] is True
        assert result["return_code"] == 0
        assert result["stdout"] == "Command output"
        assert result["command"] == "echo 'Hello, World!'"

def test_generate_file(executor, tmp_path):
    """Test generating a file."""
    # Generate a file
    file_path = tmp_path / "test.py"
    result = executor.generate_file(file_path, "Create a Hello World program", "python")
    
    # Check the result
    assert result["success"] is True
    assert result["file_path"] == str(file_path)
    assert result["language"] == "python"
    
    # Check that the file was created
    assert file_path.exists()
    
    # Check the file content
    with open(file_path, 'r') as f:
        content = f.read()
    assert content == "print('Hello, World!')"
    
    # Check that the client was called
    executor.gemini_client.generate_code.assert_called_once()

def test_setup_project_structure(executor, tmp_path):
    """Test setting up a project structure."""
    # Define a project structure
    structure = {
        "directories": [
            "src",
            "tests",
            "docs"
        ],
        "files": [
            {
                "path": "src/main.py",
                "description": "Create a main module",
                "language": "python"
            },
            {
                "path": "README.md",
                "description": "Create a README file",
                "language": "markdown"
            }
        ]
    }
    
    # Set up the project structure
    result = executor.setup_project_structure(structure)
    
    # Check the result
    assert len(result["created_directories"]) == 3
    assert len(result["created_files"]) == 2
    assert len(result["errors"]) == 0
    
    # Check that the directories were created
    assert (tmp_path / "src").exists()
    assert (tmp_path / "tests").exists()
    assert (tmp_path / "docs").exists()
    
    # Check that the files were created
    assert (tmp_path / "src" / "main.py").exists()
    assert (tmp_path / "README.md").exists()

def test_command_history(executor):
    """Test command history tracking."""
    # Mock subprocess.run
    with patch('subprocess.run') as mock_run:
        # Configure the mock
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        # Execute some commands
        executor.execute_command("command1")
        executor.execute_command("command2")
        executor.execute_command("command3")
        
        # Check the command history
        history = executor.get_command_history()
        assert len(history) == 3
        assert history[0] == "command1"
        assert history[1] == "command2"
        assert history[2] == "command3"
