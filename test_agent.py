#!/usr/bin/env python3
"""
Test script for the AI Code Agent.
"""
import logging
from pathlib import Path

from models.ai_client_factory import AIClientFactory
from agent.planner import Planner
from agent.executor import Executor
from agent.git_manager import GitManager
from agent.code_reviewer import CodeReviewer
from agent.logger import MarkdownLogger
from agent.code_editor import open_code_editor
from agent.deployer import LocalDeployer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_ai_client():
    """Test the AI client factory."""
    try:
        # Create an AI client
        ai_client = AIClientFactory.create_client()
        logger.info(f"Successfully created AI client: {type(ai_client).__name__}")
        
        # Generate some text
        response = ai_client.generate_text("Hello, world!")
        logger.info(f"Generated text: {response[:100]}...")
        
        return True
    except Exception as e:
        logger.error(f"Error testing AI client: {e}")
        return False

def test_logger():
    """Test the Markdown logger."""
    try:
        # Create a logger
        test_dir = Path("test_output")
        test_dir.mkdir(exist_ok=True)
        
        logger = MarkdownLogger(test_dir, "test-project")
        
        # Log some content
        logger.start_section("Test Section")
        logger.log_text("This is a test")
        logger.start_subsection("Test Subsection")
        logger.log_code("print('Hello, world!')", "python")
        
        # Save the log
        log_file = logger.save()
        logger.log_text(f"Saved log to {log_file}")
        
        logger.save()
        
        return True
    except Exception as e:
        logger.error(f"Error testing logger: {e}")
        return False

def main():
    """Run the tests."""
    print("Testing AI Code Agent components...")
    
    # Test AI client
    print("\nTesting AI client...")
    if test_ai_client():
        print("✅ AI client test passed")
    else:
        print("❌ AI client test failed")
    
    # Test logger
    print("\nTesting Markdown logger...")
    if test_logger():
        print("✅ Markdown logger test passed")
    else:
        print("❌ Markdown logger test failed")
    
    print("\nTests completed")

if __name__ == "__main__":
    main()
