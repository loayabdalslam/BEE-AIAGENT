#!/usr/bin/env python3
"""
Simple example script for using the AI Code Agent.
"""
import sys
import os
import logging
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.gemini_client import GeminiClient
from agent.planner import Planner
from agent.executor import Executor
from agent.git_manager import GitManager
from agent.code_reviewer import CodeReviewer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Run a simple example of the AI Code Agent."""
    print("AI Code Agent - Simple Example")
    print("==============================")
    
    # Initialize components
    try:
        print("\nInitializing Gemini client...")
        gemini_client = GeminiClient()
        
        print("Initializing planner...")
        planner = Planner(gemini_client)
        
        print("Initializing executor...")
        executor = Executor(gemini_client)
        
        print("Initializing Git manager...")
        git_manager = GitManager()
        
        print("Initializing code reviewer...")
        code_reviewer = CodeReviewer(gemini_client)
        
        # Simple project description
        project_description = """
        Create a simple Flask web application with a single page that displays "Hello, World!".
        The application should have a proper project structure and include a README file.
        """
        
        print("\nGenerating project plan...")
        plan = planner.generate_plan(project_description)
        
        print("\nProject Plan:")
        print("-------------")
        print(plan["raw_plan"])
        
        print("\nGenerating tasks...")
        tasks = planner.generate_tasks(plan)
        
        print("\nTasks:")
        print("------")
        for i, task in enumerate(tasks):
            print(f"{i+1}. {task.get('task name', f'Task {i+1}')}")
            print(f"   Description: {task.get('description', 'No description')}")
            print(f"   Complexity: {task.get('complexity', 'Unknown')}")
            print()
        
        print("\nExample completed successfully!")
        return 0
    except Exception as e:
        logger.error(f"Error in example: {e}")
        print(f"\nError: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
