#!/usr/bin/env python3
"""
Fix Project Script for AI Code Agent.

This script analyzes an existing project, identifies issues based on a problem description,
and makes necessary edits to fix the problems.
"""
import sys
import logging
import argparse
from pathlib import Path
from typing import Optional, Dict, List

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from main import CodeAgent
from agent.code_reviewer import CodeReviewer
from agent.executor import Executor
from agent.deployer import LocalDeployer
from agent.package_handler import PackageHandler
from models.ai_client_factory import AIClientFactory
from config import OUTPUT_DIR

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fix_project.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize console for rich output
console = Console()

def analyze_project(project_dir: Path, ai_client) -> Dict:
    """
    Analyze the project structure and files.

    Args:
        project_dir: Path to the project directory
        ai_client: AI client for generating analysis

    Returns:
        Dictionary with project analysis
    """
    console.print("[bold yellow]Analyzing project structure...[/bold yellow]")

    # Get list of files and directories
    files = []
    directories = []

    for item in project_dir.glob("**/*"):
        if item.is_file():
            # Skip common non-code files and directories
            if any(part.startswith('.') for part in item.parts):
                continue
            if any(part in ['node_modules', 'venv', '__pycache__', 'dist', 'build'] for part in item.parts):
                continue

            # Skip large files
            if item.stat().st_size > 1000000:  # Skip files larger than 1MB
                continue

            files.append(str(item.relative_to(project_dir)))
        elif item.is_dir():
            # Skip common non-code directories
            if any(part.startswith('.') for part in item.parts):
                continue
            if any(part in ['node_modules', 'venv', '__pycache__', 'dist', 'build'] for part in item.parts):
                continue

            directories.append(str(item.relative_to(project_dir)))

    # Read content of key files
    file_contents = {}
    for file_path in files[:50]:  # Limit to first 50 files to avoid token limits
        try:
            with open(project_dir / file_path, 'r', encoding='utf-8', errors='ignore') as f:
                file_contents[file_path] = f.read()
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")

    # Detect project type
    project_type = "unknown"
    technologies = []

    # Check for package.json (Node.js projects)
    if (project_dir / "package.json").exists():
        project_type = "nodejs"
        technologies.append("nodejs")

        # Check for specific frameworks
        if (project_dir / "angular.json").exists():
            project_type = "angular"
            technologies.append("angular")
        elif (project_dir / "next.config.js").exists() or (project_dir / "next.config.ts").exists():
            project_type = "nextjs"
            technologies.append("nextjs")
            technologies.append("react")
        elif (project_dir / "vite.config.js").exists() or (project_dir / "vite.config.ts").exists():
            project_type = "vite"
            technologies.append("vite")
            if any("react" in file for file in files):
                technologies.append("react")
            if any("vue" in file for file in files):
                technologies.append("vue")
        elif any("react" in file for file in files):
            project_type = "react"
            technologies.append("react")

    # Check for Python projects
    if (project_dir / "requirements.txt").exists() or any(file.endswith(".py") for file in files):
        project_type = "python"
        technologies.append("python")

        # Check for specific frameworks
        if (project_dir / "manage.py").exists():
            project_type = "django"
            technologies.append("django")
        elif any("flask" in file_contents.get(file, "").lower() for file in file_contents):
            project_type = "flask"
            technologies.append("flask")
        elif any("fastapi" in file_contents.get(file, "").lower() for file in file_contents):
            project_type = "fastapi"
            technologies.append("fastapi")

    # Generate project analysis using AI
    analysis_prompt = f"""
    Analyze the following project structure and provide a detailed understanding of the project.

    Project Type: {project_type}
    Technologies: {', '.join(technologies)}

    Directories:
    {', '.join(directories[:20])}

    Files:
    {', '.join(files[:50])}

    Key File Contents:
    {', '.join(list(file_contents.keys())[:10])}

    Based on this information, provide:
    1. A brief description of what this project does
    2. The main components and their purposes
    3. The project architecture
    4. Any potential issues or areas for improvement you can identify

    Format your response as a structured analysis that can be used to understand the project.
    """

    try:
        analysis_text = ai_client.generate_text(analysis_prompt)

        return {
            "success": True,
            "project_type": project_type,
            "technologies": technologies,
            "directories": directories,
            "files": files,
            "analysis": analysis_text
        }
    except Exception as e:
        logger.error(f"Error generating project analysis: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def identify_issues(project_dir: Path, problem_description: str, project_analysis: Dict, ai_client) -> Dict:
    """
    Identify issues in the project based on the problem description.

    Args:
        project_dir: Path to the project directory
        problem_description: Description of the problem to fix
        project_analysis: Analysis of the project
        ai_client: AI client for generating issue identification

    Returns:
        Dictionary with identified issues
    """
    console.print("[bold yellow]Identifying issues based on problem description...[/bold yellow]")

    # Generate issue identification using AI
    issue_prompt = f"""
    I need to fix issues in a project based on the following problem description:

    PROBLEM DESCRIPTION:
    {problem_description}

    PROJECT ANALYSIS:
    {project_analysis.get('analysis', '')}

    Project Type: {project_analysis.get('project_type', 'unknown')}
    Technologies: {', '.join(project_analysis.get('technologies', []))}

    Based on this information, identify:
    1. The specific issues that need to be fixed
    2. The files that need to be modified
    3. The changes that need to be made to each file
    4. Any additional files that need to be created
    5. Any dependencies that need to be installed

    Format your response as a structured plan with the following sections:

    IDENTIFIED ISSUES:
    - List each issue with a brief description

    FILES TO MODIFY:
    - For each file, list the specific changes needed

    FILES TO CREATE:
    - For each new file, provide the file path and purpose

    DEPENDENCIES TO INSTALL:
    - List any dependencies that need to be installed

    IMPLEMENTATION PLAN:
    - Step-by-step plan for fixing the issues
    """

    try:
        issues_text = ai_client.generate_text(issue_prompt)

        return {
            "success": True,
            "issues_text": issues_text
        }
    except Exception as e:
        logger.error(f"Error identifying issues: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def generate_fixes(project_dir: Path, problem_description: str, project_analysis: Dict, issues: Dict, ai_client) -> Dict:
    """
    Generate fixes for the identified issues.

    Args:
        project_dir: Path to the project directory
        problem_description: Description of the problem to fix
        project_analysis: Analysis of the project
        issues: Identified issues
        ai_client: AI client for generating fixes

    Returns:
        Dictionary with generated fixes
    """
    console.print("[bold yellow]Generating fixes for identified issues...[/bold yellow]")

    # Get list of files to modify
    files_to_modify = []
    for file in project_analysis.get('files', []):
        try:
            with open(project_dir / file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                # Only include files that are likely to be relevant
                if len(content) < 50000:  # Skip very large files
                    files_to_modify.append({
                        "file_path": file,
                        "content": content
                    })
        except Exception as e:
            logger.error(f"Error reading file {file}: {e}")

    # Generate fixes using AI
    fixes_prompt = f"""
    I need to fix issues in a project based on the following problem description and identified issues:

    PROBLEM DESCRIPTION:
    {problem_description}

    PROJECT ANALYSIS:
    {project_analysis.get('analysis', '')}

    IDENTIFIED ISSUES:
    {issues.get('issues_text', '')}

    For each file that needs to be modified, provide the exact changes that need to be made.
    For each new file that needs to be created, provide the complete file content.

    Format your response as a JSON object with the following structure:

    {{
        "files_to_modify": [
            {{
                "file_path": "path/to/file",
                "changes": [
                    {{
                        "type": "replace",
                        "old_code": "code to replace",
                        "new_code": "replacement code"
                    }}
                ]
            }}
        ],
        "files_to_create": [
            {{
                "file_path": "path/to/new/file",
                "content": "complete file content"
            }}
        ],
        "dependencies_to_install": [
            {{
                "name": "dependency-name",
                "version": "version-spec",
                "type": "npm/pip/etc"
            }}
        ]
    }}

    Include only the JSON output without any additional text.
    """

    try:
        fixes_text = ai_client.generate_text(fixes_prompt)

        # Try to parse the JSON response
        import json
        try:
            # Find JSON in the response
            json_start = fixes_text.find('{')
            json_end = fixes_text.rfind('}') + 1

            if json_start >= 0 and json_end > json_start:
                json_str = fixes_text[json_start:json_end]
                fixes_json = json.loads(json_str)

                return {
                    "success": True,
                    "fixes": fixes_json,
                    "raw_response": fixes_text
                }
            else:
                return {
                    "success": False,
                    "error": "Could not find JSON in the response",
                    "raw_response": fixes_text
                }
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Error parsing JSON: {e}",
                "raw_response": fixes_text
            }
    except Exception as e:
        logger.error(f"Error generating fixes: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def apply_fixes(project_dir: Path, fixes: Dict) -> Dict:
    """
    Apply the generated fixes to the project.

    Args:
        project_dir: Path to the project directory
        fixes: Generated fixes

    Returns:
        Dictionary with results of applying fixes
    """
    console.print("[bold yellow]Applying fixes to the project...[/bold yellow]")

    results = {
        "modified_files": [],
        "created_files": [],
        "errors": []
    }

    # Apply modifications to existing files
    for file_to_modify in fixes.get("files_to_modify", []):
        file_path = file_to_modify.get("file_path")
        changes = file_to_modify.get("changes", [])

        if not file_path or not changes:
            continue

        try:
            full_path = project_dir / file_path

            # Ensure the parent directory exists
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Read the current content
            current_content = ""
            if full_path.exists():
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    current_content = f.read()

            # Apply changes
            new_content = current_content
            for change in changes:
                change_type = change.get("type")

                if change_type == "replace":
                    old_code = change.get("old_code", "")
                    new_code = change.get("new_code", "")

                    if old_code in new_content:
                        new_content = new_content.replace(old_code, new_code)
                    else:
                        # If exact match not found, try to find a close match
                        import difflib
                        close_matches = difflib.get_close_matches(old_code, [new_content[i:i+len(old_code)+20] for i in range(0, len(new_content), 10)], n=1, cutoff=0.7)

                        if close_matches:
                            new_content = new_content.replace(close_matches[0], new_code)
                        else:
                            results["errors"].append(f"Could not find code to replace in {file_path}")

            # Write the new content
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            results["modified_files"].append(file_path)
            console.print(f"[green]Modified file:[/green] {file_path}")
        except Exception as e:
            error_msg = f"Error modifying file {file_path}: {e}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
            console.print(f"[red]Error:[/red] {error_msg}")

    # Create new files
    for file_to_create in fixes.get("files_to_create", []):
        file_path = file_to_create.get("file_path")
        content = file_to_create.get("content", "")

        if not file_path:
            continue

        try:
            full_path = project_dir / file_path

            # Ensure the parent directory exists
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Write the content
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)

            results["created_files"].append(file_path)
            console.print(f"[green]Created file:[/green] {file_path}")
        except Exception as e:
            error_msg = f"Error creating file {file_path}: {e}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
            console.print(f"[red]Error:[/red] {error_msg}")

    # Install dependencies
    dependencies_to_install = fixes.get("dependencies_to_install", [])
    if dependencies_to_install:
        console.print("[bold yellow]Installing dependencies...[/bold yellow]")

        # Group dependencies by type
        npm_deps = []
        pip_deps = []
        other_deps = []

        for dep in dependencies_to_install:
            dep_name = dep.get("name", "")
            dep_version = dep.get("version", "")
            dep_type = dep.get("type", "").lower()

            if not dep_name:
                continue

            if dep_version:
                dep_str = f"{dep_name}@{dep_version}" if dep_type in ["npm", "yarn"] else f"{dep_name}=={dep_version}"
            else:
                dep_str = dep_name

            if dep_type in ["npm", "yarn"]:
                npm_deps.append(dep_str)
            elif dep_type in ["pip", "python"]:
                pip_deps.append(dep_str)
            else:
                other_deps.append((dep_str, dep_type))

        # Install npm dependencies
        if npm_deps:
            try:
                import subprocess

                console.print("[yellow]Installing npm dependencies...[/yellow]")
                cmd = ["npm", "install", "--save"]
                cmd.extend(npm_deps)

                process = subprocess.run(
                    cmd,
                    cwd=project_dir,
                    capture_output=True,
                    text=True
                )

                if process.returncode == 0:
                    console.print("[green]Successfully installed npm dependencies[/green]")
                else:
                    error_msg = f"Error installing npm dependencies: {process.stderr}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)
                    console.print(f"[red]Error:[/red] {error_msg}")
            except Exception as e:
                error_msg = f"Error installing npm dependencies: {e}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
                console.print(f"[red]Error:[/red] {error_msg}")

        # Install pip dependencies
        if pip_deps:
            try:
                import subprocess

                console.print("[yellow]Installing pip dependencies...[/yellow]")
                cmd = ["pip", "install"]
                cmd.extend(pip_deps)

                process = subprocess.run(
                    cmd,
                    cwd=project_dir,
                    capture_output=True,
                    text=True
                )

                if process.returncode == 0:
                    console.print("[green]Successfully installed pip dependencies[/green]")
                else:
                    error_msg = f"Error installing pip dependencies: {process.stderr}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)
                    console.print(f"[red]Error:[/red] {error_msg}")
            except Exception as e:
                error_msg = f"Error installing pip dependencies: {e}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
                console.print(f"[red]Error:[/red] {error_msg}")

    return results

def fix_project(project_dir: Path, problem_description: str, open_editor: bool = True, deploy: bool = True) -> bool:
    """
    Fix issues in an existing project based on a problem description.

    Args:
        project_dir: Path to the project directory
        problem_description: Description of the problem to fix
        open_editor: Whether to open the project in a code editor
        deploy: Whether to deploy the project locally

    Returns:
        True if successful, False otherwise
    """
    console.print(Panel(f"[bold blue]AI Code Agent - Fix Project Mode[/bold blue]"))
    console.print(f"Project directory: [bold]{project_dir}[/bold]")
    console.print(f"Problem description: [italic]{problem_description}[/italic]")
    console.print("")

    try:
        # Initialize AI client
        ai_client = AIClientFactory.create_client()

        # Step 1: Analyze the project
        console.print("[bold yellow]Step 1: Analyzing project...[/bold yellow]")
        analysis_result = analyze_project(project_dir, ai_client)

        if not analysis_result["success"]:
            console.print(f"[bold red]Error analyzing project:[/bold red] {analysis_result.get('error', 'Unknown error')}")
            return False

        console.print("[bold green]Project analysis complete[/bold green]")
        console.print(f"Project type: [bold]{analysis_result.get('project_type', 'unknown')}[/bold]")
        console.print(f"Technologies: [bold]{', '.join(analysis_result.get('technologies', []))}[/bold]")
        console.print("")
        console.print(Markdown(analysis_result.get('analysis', '')))

        # Step 2: Identify issues
        console.print("\n[bold yellow]Step 2: Identifying issues...[/bold yellow]")
        issues_result = identify_issues(project_dir, problem_description, analysis_result, ai_client)

        if not issues_result["success"]:
            console.print(f"[bold red]Error identifying issues:[/bold red] {issues_result.get('error', 'Unknown error')}")
            return False

        console.print("[bold green]Issues identified[/bold green]")
        console.print(Markdown(issues_result.get('issues_text', '')))

        # Step 3: Generate fixes
        console.print("\n[bold yellow]Step 3: Generating fixes...[/bold yellow]")
        fixes_result = generate_fixes(project_dir, problem_description, analysis_result, issues_result, ai_client)

        if not fixes_result["success"]:
            console.print(f"[bold red]Error generating fixes:[/bold red] {fixes_result.get('error', 'Unknown error')}")
            return False

        console.print("[bold green]Fixes generated[/bold green]")

        # Step 4: Apply fixes
        console.print("\n[bold yellow]Step 4: Applying fixes...[/bold yellow]")
        apply_result = apply_fixes(project_dir, fixes_result.get("fixes", {}))

        if apply_result["errors"]:
            console.print(f"[bold red]Errors occurred while applying fixes:[/bold red]")
            for error in apply_result["errors"]:
                console.print(f"- {error}")

        console.print("[bold green]Fixes applied[/bold green]")
        console.print(f"Modified files: [bold]{len(apply_result.get('modified_files', []))}[/bold]")
        console.print(f"Created files: [bold]{len(apply_result.get('created_files', []))}[/bold]")

        # Step 5: Deploy locally (if requested)
        if deploy:
            console.print("\n[bold yellow]Step 5: Deploying project locally...[/bold yellow]")

            # Create a deployer
            deployer = LocalDeployer(project_dir)

            # Deploy the project
            deploy_result = deployer.deploy_locally()

            if not deploy_result["success"]:
                console.print(f"[bold red]Error deploying project:[/bold red] {deploy_result.get('message', 'Unknown error')}")
            else:
                console.print(f"[bold green]{deploy_result['message']}[/bold green]")
                if "url" in deploy_result and deploy_result["url"]:
                    console.print(f"URL: [bold blue]{deploy_result['url']}[/bold blue]")
                if "start_command" in deploy_result:
                    console.print(f"Start command: [bold yellow]{deploy_result['start_command']}[/bold yellow]")

        # Step 6: Open in code editor (if requested)
        if open_editor:
            console.print("\n[bold yellow]Step 6: Opening project in code editor...[/bold yellow]")

            # Create a code agent
            agent = CodeAgent(None)
            agent.project_dir = project_dir

            # Open the project in a code editor
            agent.open_in_editor()

        # Final summary
        console.print("\n[bold green]Project fixes complete![/bold green]")
        console.print(f"Project directory: [bold]{project_dir}[/bold]")

        return True
    except Exception as e:
        logger.error(f"Error in fix_project: {e}")
        console.print(f"[bold red]Error in fix_project:[/bold red] {str(e)}")
        return False

def main():
    """Main entry point for the fix project script."""
    parser = argparse.ArgumentParser(description="Fix issues in an existing project.")
    parser.add_argument("project_dir", help="Path to the project directory")
    parser.add_argument("problem", help="Description of the problem to fix")
    parser.add_argument("--no-editor", action="store_true", help="Don't open the project in a code editor")
    parser.add_argument("--no-deploy", action="store_true", help="Don't deploy the project locally")
    parser.add_argument("--output", "-o", help="Output directory for fixed files (defaults to the project directory)")

    args = parser.parse_args()

    # Determine the project directory
    if args.output:
        # If output directory is specified, use it
        project_dir = Path(args.output) / Path(args.project_dir).name
        # Copy the project to the output directory if it doesn't exist
        if not project_dir.exists():
            import shutil
            console.print(f"Copying project to output directory: [bold]{project_dir}[/bold]")
            shutil.copytree(args.project_dir, project_dir)
    else:
        # Check if the project is already in the output directory
        project_path = Path(args.project_dir)
        if OUTPUT_DIR in project_path.parents or project_path == OUTPUT_DIR:
            # Project is already in the output directory
            project_dir = project_path
        else:
            # Copy the project to the output directory
            project_dir = OUTPUT_DIR / project_path.name
            if not project_dir.exists():
                import shutil
                console.print(f"Copying project to output directory: [bold]{project_dir}[/bold]")
                shutil.copytree(args.project_dir, project_dir)

    # Run the fix_project function
    success = fix_project(
        project_dir=project_dir,
        problem_description=args.problem,
        open_editor=not args.no_editor,
        deploy=not args.no_deploy
    )

    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
