#!/usr/bin/env python3
"""
AI Code Agent - Main application entry point.

This agent can handle software engineering tasks based on a single project description prompt.
"""
import os
import sys
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from models.ai_client_factory import AIClientFactory
from agent.planner import Planner
from agent.executor import Executor
from agent.git_manager import GitManager
from agent.code_reviewer import CodeReviewer
from agent.utils import parse_project_description, format_command_output, save_json
from agent.logger import MarkdownLogger
from agent.code_editor import open_code_editor
from agent.deployer import LocalDeployer
from config import OUTPUT_DIR

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("agent.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize console for rich output
console = Console()

class CodeAgent:
    """
    AI-powered code agent that can handle software engineering tasks.
    """

    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize the code agent."""
        # Initialize components
        self.ai_client = AIClientFactory.create_client()
        self.planner = Planner(self.ai_client)
        self.executor = Executor(self.ai_client)
        self.code_reviewer = CodeReviewer(self.ai_client)
        self.git_manager = None  # Will be initialized in the project directory

        # Project state
        self.project_description = None
        self.project_plan = None
        self.tasks = []
        self.current_task = None
        self.project_name = None
        self.project_dir = None

        # Set output directory
        self.output_dir = output_dir or OUTPUT_DIR

        # Initialize logger (will be properly set up once we have a project name and directory)
        self.logger = None

    def process_project_description(self, description: str) -> Dict:
        """
        Process a project description and generate a plan.

        Args:
            description: Project description

        Returns:
            Dictionary with processing results
        """
        console.print(Panel("[bold blue]Processing Project Description[/bold blue]"))

        # Parse the project description
        self.project_description = parse_project_description(description)

        # Generate an AI name for the project
        console.print("\n[bold yellow]Generating AI project name...[/bold yellow]")
        name_prompt = f"""
        Generate a creative, memorable, and relevant project name for the following project description:

        {description}

        The name should be short (1-3 words), catchy, and reflect the purpose or main features of the project.
        Return ONLY the name without any explanation or additional text.
        """

        try:
            ai_project_name = self.ai_client.generate_text(name_prompt).strip()
            # Clean up the name to be filesystem-friendly
            import re
            clean_name = re.sub(r'[^\w\s-]', '', ai_project_name).strip()
            clean_name = re.sub(r'[\s]+', '-', clean_name).lower()

            if clean_name:
                self.project_name = clean_name
            else:
                self.project_name = self.project_description['project_name']
        except Exception as e:
            logger.warning(f"Error generating AI project name: {e}")
            self.project_name = self.project_description['project_name']

        # Create project directory in the output folder
        self.project_dir = self.output_dir / self.project_name
        self.project_dir.mkdir(exist_ok=True, parents=True)

        # Initialize the logger
        self.logger = MarkdownLogger(self.project_dir, self.project_name)
        self.logger.start_section("Project Initialization")
        self.logger.log_text(f"Project Name: {self.project_name}")
        self.logger.log_text(f"Project Directory: {self.project_dir}")

        console.print(f"Project Name: [bold]{self.project_name}[/bold]")
        console.print(f"Project Directory: [bold]{self.project_dir}[/bold]")

        if self.project_description["technologies"]:
            console.print("Technologies:")
            tech_list = []
            for tech in self.project_description["technologies"]:
                console.print(f"  - {tech}")
                tech_list.append(tech)
            self.logger.log_text("**Technologies:**")
            self.logger.log_text("\n".join([f"- {tech}" for tech in tech_list]))

        if self.project_description["features"]:
            console.print("Features:")
            feature_list = []
            for feature in self.project_description["features"]:
                console.print(f"  - {feature}")
                feature_list.append(feature)
            self.logger.log_text("**Features:**")
            self.logger.log_text("\n".join([f"- {feature}" for feature in feature_list]))

        console.print("\n[bold yellow]Generating project plan...[/bold yellow]")

        # Generate a project plan
        self.project_plan = self.planner.generate_plan(description)

        if "error" in self.project_plan:
            console.print(f"[bold red]Error generating plan:[/bold red] {self.project_plan['error']}")
            return {"success": False, "error": self.project_plan["error"]}

        # Display the plan
        console.print("\n[bold green]Project Plan Generated:[/bold green]")
        console.print(Markdown(self.project_plan["raw_plan"]))

        # Log the plan
        self.logger.start_section("Project Plan")
        self.logger.log_plan(self.project_plan)

        # Generate tasks
        console.print("\n[bold yellow]Generating development tasks...[/bold yellow]")
        try:
            self.tasks = self.planner.generate_tasks(self.project_plan)

            if not self.tasks:
                console.print("[bold red]Error generating tasks: No tasks were returned[/bold red]")
                return {"success": False, "error": "Failed to generate tasks: No tasks were returned"}
        except Exception as e:
            console.print(f"[bold red]Error generating tasks: {str(e)}[/bold red]")
            return {"success": False, "error": f"Failed to generate tasks: {str(e)}"}

        # Display tasks
        console.print(f"\n[bold green]Generated {len(self.tasks)} tasks[/bold green]")
        for i, task in enumerate(self.tasks):
            console.print(f"{i+1}. [bold]{task.get('task name', task.get('name', f'Task {i+1}'))}[/bold]")
            if "description" in task:
                console.print(f"   {task['description']}")

        # Log the tasks
        self.logger.start_section("Development Tasks")
        self.logger.log_tasks(self.tasks)

        # Save the project state and logger
        self._save_project_state()
        self.logger.save()

        return {
            "success": True,
            "project_name": self.project_description["project_name"],
            "plan": self.project_plan,
            "tasks": self.tasks
        }

    def setup_project(self) -> Dict:
        """
        Set up the project structure based on the plan.

        Returns:
            Dictionary with setup results
        """
        if not self.project_plan:
            return {"success": False, "error": "No project plan available"}

        console.print(Panel("[bold blue]Setting Up Project Structure[/bold blue]"))

        # Log the setup process
        self.logger.start_section("Project Setup")

        # Initialize Git repository in the project directory
        console.print("\n[bold yellow]Initializing Git repository in project directory...[/bold yellow]")
        self.git_manager = GitManager(self.project_dir)
        git_init_result = self.git_manager.init_repo()

        if git_init_result["success"]:
            console.print(f"[bold green]{git_init_result['message']}[/bold green]")
            self.logger.log_text(f"✅ {git_init_result['message']}")
        else:
            console.print(f"[bold yellow]Note:[/bold yellow] {git_init_result['message']}")
            self.logger.log_text(f"⚠️ {git_init_result['message']}")

        # Extract directory structure from the plan
        console.print("\n[bold yellow]Creating project structure...[/bold yellow]")

        # Generate a prompt to extract the directory structure
        structure_prompt = f"""
        Based on the following project plan, generate a detailed directory structure and initial files to create:

        {self.project_plan.get('raw_plan', '')}

        Provide your response in the following JSON format:
        {{
            "directories": [
                "path/to/directory1",
                "path/to/directory2",
                ...
            ],
            "files": [
                {{
                    "path": "path/to/file1",
                    "description": "Detailed description of what this file should contain",
                    "language": "programming language"
                }},
                ...
            ]
        }}

        Include only the JSON output without any additional text.
        """

        structure_text = self.gemini_client.generate_text(structure_prompt)

        # Extract JSON from the response
        try:
            # Find JSON in the response
            json_start = structure_text.find('{')
            json_end = structure_text.rfind('}') + 1

            if json_start >= 0 and json_end > json_start:
                json_str = structure_text[json_start:json_end]
                structure = json.loads(json_str)
            else:
                raise ValueError("No JSON found in the response")

            # Update executor to use project directory
            self.executor = Executor(self.ai_client, self.project_dir)

            # Set up the project structure
            setup_result = self.executor.setup_project_structure(structure)

            # Display results
            if setup_result["created_directories"]:
                console.print("\n[bold green]Created directories:[/bold green]")
                self.logger.start_subsection("Created Directories")
                for directory in setup_result["created_directories"]:
                    console.print(f"  - {directory}")
                    self.logger.log_text(f"- {directory}")

            if setup_result["created_files"]:
                console.print("\n[bold green]Created files:[/bold green]")
                self.logger.start_subsection("Created Files")
                for file_path in setup_result["created_files"]:
                    console.print(f"  - {file_path}")
                    self.logger.log_text(f"- {file_path}")

            if setup_result["errors"]:
                console.print("\n[bold red]Errors:[/bold red]")
                self.logger.start_subsection("Errors")
                for error in setup_result["errors"]:
                    console.print(f"  - {error}")
                    self.logger.log_text(f"- ❌ {error}")

            # Commit the initial structure
            console.print("\n[bold yellow]Committing initial project structure...[/bold yellow]")
            commit_result = self.git_manager.commit("Initial project structure")

            if commit_result["success"]:
                console.print(f"[bold green]{commit_result['message']}[/bold green]")
                self.logger.log_text(f"✅ {commit_result['message']}")
            else:
                console.print(f"[bold red]Error committing changes:[/bold red] {commit_result.get('error', 'Unknown error')}")
                self.logger.log_text(f"❌ Error committing changes: {commit_result.get('error', 'Unknown error')}")

            # Save project state to the project directory
            state_file = self.project_dir / "project_state.json"
            self._save_project_state(state_file)

            # Save the logger
            self.logger.save()

            # Open the project in a code editor
            self.open_in_editor()

            return {
                "success": True,
                "directories_created": len(setup_result["created_directories"]),
                "files_created": len(setup_result["created_files"]),
                "errors": setup_result["errors"]
            }
        except Exception as e:
            logger.error(f"Error setting up project structure: {e}")
            console.print(f"[bold red]Error setting up project structure:[/bold red] {str(e)}")
            return {"success": False, "error": str(e)}

    def execute_task(self, task_index: int) -> Dict:
        """
        Execute a specific task from the task list.

        Args:
            task_index: Index of the task to execute

        Returns:
            Dictionary with execution results
        """
        if not self.tasks:
            return {"success": False, "error": "No tasks available"}

        if task_index < 0 or task_index >= len(self.tasks):
            return {"success": False, "error": f"Invalid task index: {task_index}"}

        task = self.tasks[task_index]
        self.current_task = task

        console.print(Panel(f"[bold blue]Executing Task: {task.get('task name', task.get('name', f'Task {task_index+1}'))}[/bold blue]"))
        console.print(f"Description: {task.get('description', 'No description')}")

        # Make sure we're in the project directory
        if not self.project_dir or not self.project_dir.exists():
            console.print("[bold red]Error: Project directory not found[/bold red]")
            return {"success": False, "error": "Project directory not found"}

        # Make sure git is initialized
        if not self.git_manager:
            console.print("[bold yellow]Initializing Git repository in project directory...[/bold yellow]")
            self.git_manager = GitManager(self.project_dir)
            git_init_result = self.git_manager.init_repo()

            if git_init_result["success"]:
                console.print(f"[bold green]{git_init_result['message']}[/bold green]")
            else:
                console.print(f"[bold yellow]Note:[/bold yellow] {git_init_result['message']}")

        # Create a branch for the task
        task_name = task.get('task name', task.get('name', f'task-{task_index+1}'))
        branch_name = f"feature/{task_name.lower().replace(' ', '-')}"

        console.print(f"\n[bold yellow]Creating branch: {branch_name}[/bold yellow]")
        branch_result = self.git_manager.create_branch(branch_name)

        if branch_result["success"]:
            console.print(f"[bold green]{branch_result['message']}[/bold green]")
        else:
            console.print(f"[bold red]Error creating branch:[/bold red] {branch_result.get('error', 'Unknown error')}")

        # Generate a prompt to execute the task
        execution_prompt = f"""
        I need to implement the following task in a software project:

        Task: {task.get('task name', task.get('name', f'Task {task_index+1}'))}
        Description: {task.get('description', 'No description')}

        Project context:
        {self.project_plan.get('raw_plan', '')}

        Generate a list of specific commands and code changes needed to implement this task.
        Provide your response in the following JSON format:
        {{
            "commands": [
                {{
                    "command": "command to execute",
                    "description": "what this command does"
                }},
                ...
            ],
            "code_changes": [
                {{
                    "file_path": "path/to/file",
                    "description": "detailed description of what code to write in this file"
                }},
                ...
            ]
        }}

        Include only the JSON output without any additional text.
        """

        console.print("\n[bold yellow]Generating implementation plan...[/bold yellow]")
        execution_text = self.gemini_client.generate_text(execution_prompt)

        try:
            # Find JSON in the response
            json_start = execution_text.find('{')
            json_end = execution_text.rfind('}') + 1

            if json_start >= 0 and json_end > json_start:
                json_str = execution_text[json_start:json_end]
                execution_plan = json.loads(json_str)
            else:
                raise ValueError("No JSON found in the response")

            # Execute commands
            if "commands" in execution_plan and execution_plan["commands"]:
                console.print("\n[bold green]Executing commands:[/bold green]")

                for cmd_info in execution_plan["commands"]:
                    command = cmd_info.get("command", "")
                    description = cmd_info.get("description", "No description")

                    console.print(f"\n[bold cyan]Command:[/bold cyan] {command}")
                    console.print(f"[italic]{description}[/italic]")

                    # Execute the command
                    result = self.executor.execute_command(command)

                    # Display the result
                    console.print(Markdown(format_command_output(result)))

            # Implement code changes
            if "code_changes" in execution_plan and execution_plan["code_changes"]:
                console.print("\n[bold green]Implementing code changes:[/bold green]")

                for change in execution_plan["code_changes"]:
                    file_path = change.get("file_path", "")
                    description = change.get("description", "No description")

                    console.print(f"\n[bold cyan]File:[/bold cyan] {file_path}")
                    console.print(f"[italic]{description}[/italic]")

                    # Determine the language from the file extension
                    language = None
                    if "." in file_path:
                        extension = file_path.split(".")[-1]
                        language_map = {
                            "py": "python",
                            "js": "javascript",
                            "ts": "typescript",
                            "html": "html",
                            "css": "css",
                            "java": "java",
                            "c": "c",
                            "cpp": "c++",
                            "go": "go",
                            "rs": "rust",
                            "rb": "ruby",
                            "php": "php",
                            "sh": "bash",
                            "md": "markdown"
                        }
                        language = language_map.get(extension.lower())

                    # Generate the file
                    result = self.executor.generate_file(file_path, description, language)

                    if result["success"]:
                        console.print(f"[bold green]Generated file:[/bold green] {result['file_path']}")
                        console.print(f"Preview: {result['content_preview']}")
                    else:
                        console.print(f"[bold red]Error generating file:[/bold red] {result.get('error', 'Unknown error')}")

            # Commit the changes
            console.print("\n[bold yellow]Committing changes...[/bold yellow]")
            commit_message = f"Implement {task.get('task name', task.get('name', f'Task {task_index+1}'))}"
            commit_result = self.git_manager.commit(commit_message)

            if commit_result["success"]:
                console.print(f"[bold green]{commit_result['message']}[/bold green]")
            else:
                console.print(f"[bold red]Error committing changes:[/bold red] {commit_result.get('error', 'Unknown error')}")

            # Save project state to the project directory
            state_file = self.project_dir / "project_state.json"
            self._save_project_state(state_file)

            # Add a README if it doesn't exist
            readme_path = self.project_dir / "README.md"
            if not readme_path.exists():
                console.print("\n[bold yellow]Creating README.md...[/bold yellow]")
                readme_content = f"""# {self.project_name.replace('-', ' ').title()}

This project was generated by AI Code Agent.

## Project Description

{self.project_description.get('raw_description', 'No description available.')}

## Project Structure

Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

                try:
                    with open(readme_path, 'w') as f:
                        f.write(readme_content)
                    console.print(f"[bold green]Created README.md[/bold green]")

                    # Commit the README
                    self.git_manager.add_files([readme_path])
                    self.git_manager.commit("Add README.md")
                except Exception as e:
                    console.print(f"[bold red]Error creating README:[/bold red] {str(e)}")

            return {
                "success": True,
                "task_index": task_index,
                "branch": branch_name,
                "commands_executed": len(execution_plan.get("commands", [])),
                "code_changes": len(execution_plan.get("code_changes", []))
            }
        except Exception as e:
            logger.error(f"Error executing task: {e}")
            console.print(f"[bold red]Error executing task:[/bold red] {str(e)}")
            return {"success": False, "error": str(e)}

    def review_code(self) -> Dict:
        """
        Review the code in the current project.

        Returns:
            Dictionary with review results
        """
        console.print(Panel("[bold blue]Reviewing Code[/bold blue]"))

        # Use the project directory if available, otherwise current directory
        review_dir = self.project_dir if self.project_dir and self.project_dir.exists() else Path.cwd()

        console.print(f"Reviewing code in: {review_dir}")

        # Review the code
        review_result = self.code_reviewer.review_directory(review_dir)

        if not review_result["success"]:
            console.print(f"[bold red]Error reviewing code:[/bold red] {review_result.get('error', 'Unknown error')}")
            return review_result

        # Generate a report
        report = self.code_reviewer.generate_review_report(review_result)

        # Display the report
        console.print("\n[bold green]Code Review Report:[/bold green]")
        console.print(Markdown(report))

        # Save the report
        report_path = review_dir / "code_review_report.md"
        try:
            with open(report_path, 'w') as f:
                f.write(report)
            console.print(f"[bold green]Saved review report to:[/bold green] {report_path}")

            # Commit the review report if we have a git repository
            if self.git_manager:
                try:
                    self.git_manager.add_files([report_path])
                    self.git_manager.commit("Add code review report")
                    console.print("[bold green]Committed code review report[/bold green]")
                except Exception as git_error:
                    logger.error(f"Error committing review report: {git_error}")
        except Exception as e:
            logger.error(f"Error saving review report: {e}")
            console.print(f"[bold red]Error saving review report:[/bold red] {str(e)}")

        return review_result

    def open_in_editor(self) -> bool:
        """
        Open the project in a code editor.

        Returns:
            True if successful, False otherwise
        """
        if not self.project_dir or not self.project_dir.exists():
            console.print("[bold red]Error: Project directory not found[/bold red]")
            return False

        console.print(f"\n[bold yellow]Opening project in code editor: {self.project_dir}[/bold yellow]")

        # Log the action
        if self.logger:
            self.logger.log_text(f"Opening project in code editor: {self.project_dir}")

        # Open the code editor
        result = open_code_editor(self.project_dir)

        if result:
            console.print("[bold green]Successfully opened project in code editor[/bold green]")
            if self.logger:
                self.logger.log_text("✅ Successfully opened project in code editor")
        else:
            console.print("[bold red]Failed to open project in code editor[/bold red]")
            if self.logger:
                self.logger.log_text("❌ Failed to open project in code editor")

        return result

    def deploy_locally(self) -> Dict:
        """
        Deploy the project locally.

        Returns:
            Dictionary with deployment results
        """
        if not self.project_dir or not self.project_dir.exists():
            console.print("[bold red]Error: Project directory not found[/bold red]")
            return {"success": False, "error": "Project directory not found"}

        console.print(f"\n[bold yellow]Deploying project locally: {self.project_dir}[/bold yellow]")

        # Log the action
        if self.logger:
            self.logger.start_section("Local Deployment")
            self.logger.log_text(f"Deploying project locally: {self.project_dir}")

        try:
            # Create a deployer
            deployer = LocalDeployer(self.project_dir)

            # Detect project type
            project_type = deployer.detect_project_type()
            console.print(f"Detected project type: [bold]{project_type}[/bold]")

            if self.logger:
                self.logger.log_text(f"Detected project type: {project_type}")

            # Deploy the project
            result = deployer.deploy_locally()

            if result["success"]:
                console.print(f"[bold green]{result['message']}[/bold green]")
                if "url" in result and result["url"]:
                    console.print(f"URL: [bold blue]{result['url']}[/bold blue]")
                if "process_id" in result:
                    console.print(f"Process ID: [bold]{result['process_id']}[/bold]")

                if self.logger:
                    self.logger.log_text(f"✅ {result['message']}")
                    if "url" in result and result["url"]:
                        self.logger.log_text(f"URL: {result['url']}")
                    if "process_id" in result:
                        self.logger.log_text(f"Process ID: {result['process_id']}")
            else:
                console.print(f"[bold red]{result['message']}[/bold red]")
                if self.logger:
                    self.logger.log_text(f"❌ {result['message']}")

            return result
        except Exception as e:
            error_msg = f"Error deploying project: {str(e)}"
            console.print(f"[bold red]{error_msg}[/bold red]")
            if self.logger:
                self.logger.log_text(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}

    def _save_project_state(self, file_path: Optional[Path] = None) -> bool:
        """
        Save the current project state to a file.

        Args:
            file_path: Path to save the state file (default: project_state.json in current directory)

        Returns:
            True if successful, False otherwise
        """
        state = {
            "project_description": self.project_description,
            "project_plan": self.project_plan,
            "tasks": self.tasks,
            "current_task": self.current_task,
            "project_name": self.project_name,
            "project_dir": str(self.project_dir) if self.project_dir else None
        }

        # Use provided path or default
        save_path = file_path or Path("project_state.json")

        return save_json(state, save_path)

@click.command()
@click.argument("description", required=False)
@click.option("--interactive", "-i", is_flag=True, help="Run in interactive mode")
@click.option("--file", "-f", type=click.Path(exists=True), help="Read project description from a file")
@click.option("--output", "-o", type=click.Path(), help="Output directory for generated projects")
def main(description, interactive, file, output):
    """
    AI Code Agent - Generate and implement software projects from descriptions.

    Provide a project description as an argument, or use --file to read from a file,
    or use --interactive to enter interactive mode.
    """
    # Initialize the agent with custom output directory if provided
    output_dir = Path(output) if output else None
    agent = CodeAgent(output_dir)

    # Get the project description
    if file:
        try:
            with open(file, 'r') as f:
                description = f.read()
        except Exception as e:
            console.print(f"[bold red]Error reading file:[/bold red] {str(e)}")
            return
    elif not description and not interactive:
        console.print("[bold yellow]No project description provided.[/bold yellow]")
        console.print("Use --interactive to enter interactive mode or provide a description as an argument.")
        return

    if interactive:
        console.print(Panel("[bold blue]AI Code Agent - Interactive Mode[/bold blue]"))

        # Interactive mode
        if not description:
            console.print("\nEnter your project description (type 'END' on a new line when finished):")
            lines = []
            while True:
                line = input()
                if line == "END":
                    break
                lines.append(line)
            description = "\n".join(lines)

        # Process the project description
        result = agent.process_project_description(description)

        if not result["success"]:
            console.print(f"[bold red]Error processing project description:[/bold red] {result.get('error', 'Unknown error')}")
            return

        # Interactive menu
        while True:
            console.print("\n[bold blue]What would you like to do?[/bold blue]")
            console.print("1. Set up project structure")
            console.print("2. Execute a task")
            console.print("3. Review code")
            console.print("4. Open in code editor")
            console.print("5. Deploy locally")
            console.print("6. Exit")

            choice = input("\nEnter your choice (1-6): ")

            if choice == "1":
                agent.setup_project()
            elif choice == "2":
                if not agent.tasks:
                    console.print("[bold yellow]No tasks available. Process a project description first.[/bold yellow]")
                    continue

                console.print("\n[bold blue]Available tasks:[/bold blue]")
                for i, task in enumerate(agent.tasks):
                    console.print(f"{i+1}. {task.get('task name', task.get('name', f'Task {i+1}'))}")

                task_choice = input(f"\nEnter task number (1-{len(agent.tasks)}): ")
                try:
                    task_index = int(task_choice) - 1
                    if task_index < 0 or task_index >= len(agent.tasks):
                        console.print(f"[bold red]Invalid task number. Please enter a number between 1 and {len(agent.tasks)}.[/bold red]")
                        continue

                    agent.execute_task(task_index)
                except ValueError:
                    console.print("[bold red]Invalid input. Please enter a number.[/bold red]")
            elif choice == "3":
                agent.review_code()
            elif choice == "4":
                agent.open_in_editor()
            elif choice == "5":
                agent.deploy_locally()
            elif choice == "6":
                console.print("[bold green]Exiting...[/bold green]")
                break
            else:
                console.print("[bold red]Invalid choice. Please enter a number between 1 and 6.[/bold red]")
    else:
        # Non-interactive mode
        console.print(Panel("[bold blue]AI Code Agent[/bold blue]"))

        # Process the project description
        result = agent.process_project_description(description)

        if not result["success"]:
            console.print(f"[bold red]Error processing project description:[/bold red] {result.get('error', 'Unknown error')}")
            return

        # Set up the project
        setup_result = agent.setup_project()

        if not setup_result["success"]:
            console.print(f"[bold red]Error setting up project:[/bold red] {setup_result.get('error', 'Unknown error')}")
            return

        # Execute all tasks
        for i in range(len(agent.tasks)):
            task_result = agent.execute_task(i)

            if not task_result["success"]:
                console.print(f"[bold red]Error executing task {i+1}:[/bold red] {task_result.get('error', 'Unknown error')}")
                break

        # Review the code
        agent.review_code()

if __name__ == "__main__":
    main()
