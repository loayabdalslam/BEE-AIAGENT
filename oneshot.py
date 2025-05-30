#!/usr/bin/env python3
"""
One-shot script for end-to-end project generation and deployment.
This script will:
1. Generate a project from a description
2. Set up the project structure
3. Implement all tasks
4. Review and fix code issues
5. Open the project in a code editor
6. Deploy the project locally
"""
import sys
import logging
import argparse
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from main import CodeAgent
from config import OUTPUT_DIR

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("oneshot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize console for rich output
console = Console()

def oneshot(description: str, output_dir: Optional[Path] = None, open_editor: bool = True, deploy: bool = True, project_name: Optional[str] = None) -> bool:
    """
    Run the entire project generation and deployment process in one shot.

    Args:
        description: Project description
        output_dir: Output directory for the project
        open_editor: Whether to open the project in a code editor
        deploy: Whether to deploy the project locally
        project_name: Optional project name to use (if not provided, will be derived from description)

    Returns:
        True if successful, False otherwise
    """
    console.print(Panel("[bold blue]AI Code Agent - One-Shot Mode[/bold blue]"))
    console.print("This will generate, implement, review, fix, and deploy a project in one go.")
    console.print("")

    try:
        # Initialize the agent
        agent = CodeAgent(output_dir)

        # If project_name is provided, set it directly to avoid creating a new folder
        if project_name:
            agent.project_name = project_name

        # Step 1: Process the project description
        console.print("[bold yellow]Step 1: Processing project description...[/bold yellow]")
        result = agent.process_project_description(description)

        if not result["success"]:
            console.print(f"[bold red]Error processing project description:[/bold red] {result.get('error', 'Unknown error')}")
            return False

        # Step 2: Set up the project structure
        console.print("\n[bold yellow]Step 2: Setting up project structure...[/bold yellow]")
        setup_result = agent.setup_project()

        if not setup_result["success"]:
            console.print(f"[bold red]Error setting up project:[/bold red] {setup_result.get('error', 'Unknown error')}")
            return False

        # Step 3: Execute all tasks
        console.print("\n[bold yellow]Step 3: Implementing all tasks...[/bold yellow]")

        # Print a note about direct code generation
        console.print("\n[bold cyan]Note about code generation:[/bold cyan]")
        console.print("The agent will generate all code directly without using external code generators.")
        console.print("This means it will create all necessary files manually instead of using tools like 'create-react-app'.")
        console.print("All configuration files (package.json, etc.) will be created with appropriate content.")
        console.print("Only necessary package installation commands will be used.\n")

        for i, task in enumerate(agent.tasks):
            task_name = task.get('task name', task.get('name', f'Task {i+1}'))
            console.print(f"\nImplementing task {i+1}/{len(agent.tasks)}: [bold]{task_name}[/bold]")

            # Check if this is likely a project initialization task
            is_init_task = any(keyword in task_name.lower() for keyword in [
                "init", "create", "setup", "scaffold", "generate", "bootstrap"
            ])

            if is_init_task:
                console.print("[yellow]This appears to be a project initialization task.[/yellow]")
                console.print("[yellow]The agent will generate all necessary files directly without using external code generators.[/yellow]")
                console.print("[yellow]Please be patient while the agent generates the code...[/yellow]")

            # Execute the task
            task_result = agent.execute_task(i)

            if not task_result["success"]:
                console.print(f"[bold red]Error executing task {i+1}:[/bold red] {task_result.get('error', 'Unknown error')}")
                # Continue with the next task even if this one failed

        # Step 4: Deploy locally to install packages (if requested)
        if deploy:
            console.print("\n[bold yellow]Step 4: Installing packages...[/bold yellow]")
            console.print("[yellow]Installing packages before code review to ensure all dependencies are available.[/yellow]")
            deploy_result = agent.deploy_locally()

            if not deploy_result["success"]:
                console.print(f"[bold red]Error installing packages:[/bold red] {deploy_result.get('error', 'Unknown error')}")
                # Continue even if package installation failed
            else:
                console.print("\n[bold green]Package installation successful![/bold green]")
                if "start_command" in deploy_result:
                    console.print(f"To start the application, run: [bold yellow]{deploy_result['start_command']}[/bold yellow]")

        # Step 5: Review code
        console.print("\n[bold yellow]Step 5: Reviewing code...[/bold yellow]")
        review_result = agent.review_code(auto_fix=False)

        if not review_result["success"]:
            console.print(f"[bold red]Error reviewing code:[/bold red] {review_result.get('error', 'Unknown error')}")
            # Continue even if review failed

        # Step 6: Fix code issues
        console.print("\n[bold yellow]Step 6: Fixing code issues...[/bold yellow]")
        fix_result = agent.review_code(auto_fix=True)

        if not fix_result["success"]:
            console.print(f"[bold red]Error fixing code:[/bold red] {fix_result.get('error', 'Unknown error')}")
            # Continue even if fixing failed

        # Step 7: Deploy locally again if needed (if requested)
        if deploy:
            console.print("\n[bold yellow]Step 7: Finalizing deployment...[/bold yellow]")
            console.print("[yellow]Running deployment again to ensure all changes are properly applied.[/yellow]")
            deploy_result = agent.deploy_locally()

            if not deploy_result["success"]:
                console.print(f"[bold red]Error deploying project:[/bold red] {deploy_result.get('error', 'Unknown error')}")
                # Continue even if deployment failed
            else:
                console.print("\n[bold green]Deployment successful![/bold green]")
                if "start_command" in deploy_result:
                    console.print(f"To start the application, run: [bold yellow]{deploy_result['start_command']}[/bold yellow]")
                if "url" in deploy_result and deploy_result["url"]:
                    console.print(f"Application will be available at: [bold blue]{deploy_result['url']}[/bold blue]")

        # Step 8: Open in code editor (if requested)
        if open_editor:
            console.print("\n[bold yellow]Step 8: Opening project in code editor...[/bold yellow]")
            agent.open_in_editor()

        # Final summary
        console.print("\n[bold green]Project generation complete![/bold green]")
        console.print(f"Project name: [bold]{agent.project_name}[/bold]")
        console.print(f"Project directory: [bold]{agent.project_dir}[/bold]")

        return True
    except Exception as e:
        logger.error(f"Error in oneshot mode: {e}")
        console.print(f"[bold red]Error in oneshot mode:[/bold red] {str(e)}")
        return False

def main():
    """Main entry point for the one-shot script."""
    parser = argparse.ArgumentParser(description="Generate and deploy a project in one shot.")
    parser.add_argument("description", help="Project description")
    parser.add_argument("--output", "-o", help="Output directory for the project")
    parser.add_argument("--no-editor", action="store_true", help="Don't open the project in a code editor")
    parser.add_argument("--no-deploy", action="store_true", help="Don't deploy the project locally")
    parser.add_argument("--name", "-n", help="Project name (to avoid creating a new folder)")

    args = parser.parse_args()

    # Set output directory
    # Always use the output directory by default
    if args.output:
        # If a specific output directory is provided, use it
        output_dir = Path(args.output)
    else:
        # Otherwise, use the default output directory
        output_dir = OUTPUT_DIR

    # Run the oneshot function
    success = oneshot(
        description=args.description,
        output_dir=output_dir,
        open_editor=not args.no_editor,
        deploy=not args.no_deploy,
        project_name=args.name
    )

    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
