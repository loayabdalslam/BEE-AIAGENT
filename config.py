"""
Configuration settings for the AI Code Agent.
"""
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

# AI Provider Configuration
# Google/Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# Anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229")

# Selected AI Provider
SELECTED_PROVIDER = os.getenv("SELECTED_PROVIDER", "gemini").lower()  # Options: gemini, openai, anthropic

# Agent Configuration
DEFAULT_TEMPERATURE = 0.2  # Lower temperature for more deterministic outputs
MAX_OUTPUT_TOKENS = 8192  # Maximum tokens for generated responses
PLANNING_TEMPERATURE = 0.4  # Slightly higher temperature for creative planning

# Git Configuration
DEFAULT_BRANCH = "main"
COMMIT_MESSAGE_PREFIX = "[AI-AGENT]"

# Paths
ROOT_DIR = Path(__file__).parent
OUTPUT_DIR = ROOT_DIR / "output"
TEMPLATES_DIR = ROOT_DIR / "templates"

# Output path from environment or default
CUSTOM_OUTPUT_PATH = os.getenv("OUTPUT_PATH")
if CUSTOM_OUTPUT_PATH:
    OUTPUT_DIR = Path(CUSTOM_OUTPUT_PATH)

# Create directories if they don't exist
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
