# AI Code Agent

An AI-powered code agent that can handle software engineering tasks based on a single project description prompt. This agent uses Google's Gemini 2.0 Flash model to generate project plans, write code, and review code quality.

## Features

- **Project Planning**: Generate a detailed project plan from a description
- **Command Line Execution**: Run necessary commands to set up and develop the project
- **Git Management**: Handle version control operations
- **Code Review & Auto-Fix**: Review generated code for quality and automatically fix issues
- **Multiple AI Providers**: Support for Google Gemini, OpenAI, Azure OpenAI, and Anthropic
- **Markdown Logging**: Detailed development logs in Markdown format
- **Code Editor Integration**: Open projects in your preferred code editor
- **Local Deployment**: Deploy projects locally with automatic framework detection
- **One-Shot Mode**: Generate, implement, review, and deploy a project in a single command
- **Fix Project Mode**: Analyze existing projects, identify issues, and apply fixes

## Requirements

- Python 3.8+
- Google API key for Gemini 2.0 Flash

## Installation

1. Clone this repository
   ```bash
   git clone https://github.com/yourusername/code-agent.git
   cd code-agent
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your Google API key (use `.env.example` as a template):
   ```bash
   cp .env.example .env
   # Edit .env and add your Google API key
   ```

## Usage

### Interactive Mode

The easiest way to use the agent is in interactive mode:

```bash
python main.py --interactive
```

This will guide you through the process of:
1. Entering a project description
2. Setting up the project structure
3. Executing development tasks
4. Reviewing the code
5. Opening the project in a code editor
6. Deploying the project locally

### Command Line Mode

You can also run the agent with a project description directly:

```bash
python main.py "Create a Flask web application with user authentication and a REST API"
```

Or read the description from a file:

```bash
python main.py --file examples/web_app_description.txt
```

### Custom Output Directory

Specify a custom output directory for generated projects:

```bash
python main.py --output E:\Projects\generated "Create a React web application"
```

### Simple Example

Try the simple example script to see how the agent works:

```bash
python examples/simple_example.py
```

### AI Provider Selection

You can select which AI provider to use by setting the `SELECTED_PROVIDER` environment variable in your `.env` file:

```
SELECTED_PROVIDER=openai  # Options: gemini, openai, azure-openai, anthropic
```

Make sure to set the corresponding API key for your selected provider.

### One-Shot Mode

For a complete end-to-end experience, use the one-shot mode to generate, implement, review, and deploy a project in a single command:

```bash
python oneshot.py "Create a Flask web application with user authentication"
```

By default, all projects are created in the `output` directory to keep your workspace organized.

Options:
- `--output` or `-o`: Specify a custom output directory
- `--no-editor`: Don't open the project in a code editor
- `--no-deploy`: Don't deploy the project locally
- `--name` or `-n`: Specify project name (to avoid creating a new folder)

```bash
python oneshot.py --output E:\Projects\generated --no-deploy "Create a React web application"
```

### Fix Project Mode

Use the fix project mode to analyze an existing project, identify issues based on a problem description, and apply fixes:

```bash
python fix_project.py /path/to/project "Description of the problem to fix"
```

By default, the project will be copied to the `output` directory and all changes will be made there, preserving your original code.

Options:
- `--no-editor`: Don't open the project in a code editor
- `--no-deploy`: Don't deploy the project locally
- `--output` or `-o`: Specify a custom output directory for the fixed project

```bash
python fix_project.py E:\Projects\my-project "Fix the login functionality that's not working"
```

This mode is particularly useful for:
- Debugging existing projects
- Adding new features to existing code
- Refactoring and improving code quality
- Fixing specific issues described by the user

## Project Structure

```
code-agent/
├── README.md
├── requirements.txt
├── main.py
├── config.py
├── .env.example
├── .gitignore
├── agent/
│   ├── __init__.py
│   ├── planner.py
│   ├── executor.py
│   ├── git_manager.py
│   ├── code_reviewer.py
│   └── utils.py
├── models/
│   ├── __init__.py
│   └── gemini_client.py
├── tests/
│   ├── __init__.py
│   └── test_planner.py
└── examples/
    ├── example_prompts.md
    └── simple_example.py
```

## Configuration

You can customize the agent's behavior by modifying `config.py` or setting environment variables in your `.env` file:

- `GOOGLE_API_KEY`: Your Google API key for Gemini
- `DEFAULT_TEMPERATURE`: Temperature for general text generation (default: 0.2)
- `PLANNING_TEMPERATURE`: Temperature for planning (default: 0.4)
- `DEFAULT_BRANCH`: Default Git branch name (default: main)
- `COMMIT_MESSAGE_PREFIX`: Prefix for Git commit messages (default: [AI-AGENT])

## Troubleshooting

### API Key Issues

If you encounter errors related to the API key:
1. Make sure your Google API key is valid and has access to the Gemini API
2. Check that the key is correctly set in your `.env` file
3. Verify that the `.env` file is in the root directory of the project

### Task Generation Errors

If the agent fails to generate tasks:
1. Try using a more detailed project description
2. Check the `agent.log` file for specific error messages
3. The agent will fall back to default tasks if the API fails

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT
