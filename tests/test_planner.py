"""
Tests for the planner module.
"""
import pytest
from unittest.mock import MagicMock, patch

from agent.planner import Planner

@pytest.fixture
def mock_gemini_client():
    """Create a mock GeminiClient."""
    mock_client = MagicMock()
    mock_client.generate_text.return_value = """
    # Project Plan
    
    ## Project Overview
    - Main objective: Create a web application
    - Key features: User authentication, REST API
    - Target users: General users
    
    ## Technical Architecture
    - Recommended technologies: Python, Flask, SQLAlchemy
    - System architecture: Client-server architecture
    - Data models: User, Profile
    
    ## Development Phases
    - Phase 1: Setup and foundation
    - Phase 2: Core functionality
    - Phase 3: Additional features
    - Phase 4: Testing and refinement
    
    ## Implementation Details
    - Directory structure: Standard Flask structure
    - Key files: app.py, models.py, routes.py
    - External dependencies: Flask, SQLAlchemy
    
    ## Development Tasks
    - Task 1: Set up project structure (Low)
    - Task 2: Implement user authentication (Medium)
    - Task 3: Create REST API endpoints (Medium)
    - Task 4: Implement frontend (High)
    - Task 5: Test and refine (Medium)
    
    ## Testing Strategy
    - Unit testing: Pytest
    - Integration testing: Postman
    - Manual testing: Browser testing
    
    ## Deployment Considerations
    - Recommended platform: Heroku
    - Configuration: Environment variables
    - CI/CD: GitHub Actions
    """
    return mock_client

def test_generate_plan(mock_gemini_client):
    """Test generating a project plan."""
    planner = Planner(mock_gemini_client)
    
    # Generate a plan
    plan = planner.generate_plan("Create a web application with user authentication")
    
    # Check that the plan was generated
    assert "raw_plan" in plan
    assert "structured_plan" in plan
    
    # Check that the client was called
    mock_gemini_client.generate_text.assert_called_once()
    
    # Check that the plan contains expected sections
    structured_plan = plan["structured_plan"]
    assert len(structured_plan) > 0
    
    # Check that the raw plan is the mock response
    assert "Project Plan" in plan["raw_plan"]
    assert "Project Overview" in plan["raw_plan"]

def test_generate_tasks(mock_gemini_client):
    """Test generating tasks from a project plan."""
    planner = Planner(mock_gemini_client)
    
    # Mock the tasks response
    mock_gemini_client.generate_text.return_value = """
    Task ID: 1
    Task name: Set up project structure
    Description: Create the initial project structure and install dependencies
    Estimated complexity: Low
    Dependencies: None
    Category: Setup
    
    Task ID: 2
    Task name: Implement user authentication
    Description: Create user registration, login, and authentication system
    Estimated complexity: Medium
    Dependencies: 1
    Category: Backend
    """
    
    # Generate tasks
    plan = {"raw_plan": "Sample plan"}
    tasks = planner.generate_tasks(plan)
    
    # Check that tasks were generated
    assert len(tasks) == 2
    
    # Check that the client was called
    mock_gemini_client.generate_text.assert_called_once()
    
    # Check task properties
    assert tasks[0]["id"] == "1"
    assert "task name" in tasks[0]
    assert tasks[0]["task name"] == "Set up project structure"
    assert tasks[1]["id"] == "2"
    assert tasks[1]["description"] == "Create user registration, login, and authentication system"
