"""
Project planning module for the AI Code Agent.
"""
import logging
from typing import Dict, List, Optional
from models.gemini_client import GeminiClient
from config import PLANNING_TEMPERATURE

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Planner:
    """
    Responsible for generating project plans from descriptions.
    """

    def __init__(self, gemini_client: Optional[GeminiClient] = None):
        """
        Initialize the planner.

        Args:
            gemini_client: GeminiClient instance for AI capabilities
        """
        self.gemini_client = gemini_client or GeminiClient()

    def generate_plan_and_tasks(self, project_description: str) -> Dict:
        """
        Generate a comprehensive project plan and tasks from a description in a single request.

        Args:
            project_description: Description of the project

        Returns:
            Dictionary containing the project plan and tasks
        """
        logger.info("Generating project plan and tasks")

        # Combined prompt for both plan and tasks to reduce API calls
        combined_prompt = f"""
        Create a comprehensive software development plan for the following project:

        PROJECT DESCRIPTION:
        {project_description}

        Your response should have TWO PARTS:

        PART 1: PROJECT PLAN
        Create a structured plan with the following sections:

        1. Project Overview:
           - Main objectives
           - Key features
           - Target users/audience

        2. Technical Architecture:
           - Recommended technologies and frameworks
           - System architecture diagram (describe in text)
           - Data models and relationships

        3. Development Phases:
           - Phase 1: Setup and foundation
           - Phase 2: Core functionality
           - Phase 3: Additional features
           - Phase 4: Testing and refinement

        4. Implementation Details:
           - Directory structure
           - Key files and their purposes
           - External dependencies

        5. Testing Strategy:
           - Unit testing approach
           - Integration testing approach
           - Manual testing requirements

        6. Deployment Considerations:
           - Recommended deployment platform
           - Configuration requirements
           - CI/CD pipeline suggestions

        PART 2: DEVELOPMENT TASKS
        Create a list of specific, actionable development tasks. For each task, provide:
        1. Task ID (numeric)
        2. Task name (short, descriptive)
        3. Description (detailed explanation)
        4. Estimated complexity (Low/Medium/High)
        5. Dependencies (IDs of tasks that must be completed first)
        6. Category (Setup, Backend, Frontend, Testing, Deployment, etc.)

        IMPORTANT GUIDELINES FOR TASKS:
        - DO NOT include tasks that use external code generators like 'create-react-app', 'npx create-next-app', etc.
        - Instead, create tasks for manually writing all necessary code files
        - Include tasks for creating configuration files (package.json, webpack.config.js, etc.) manually
        - Only include commands for necessary package installations (npm install, pip install, etc.)
        - Break down the project into smaller, manageable tasks for creating a complete project structure

        Format each task as follows:

        Task ID: 1
        Task name: Example task name
        Description: Detailed description of the task
        Estimated complexity: Low/Medium/High
        Dependencies: None or comma-separated IDs
        Category: Category name

        Provide at least 5-10 tasks that cover the entire development process.
        """

        try:
            # Make a single API call for both plan and tasks
            combined_response = self.gemini_client.generate_text(
                combined_prompt,
                temperature=PLANNING_TEMPERATURE
            )

            # Split the response into plan and tasks sections
            plan_text, tasks_text = self._split_combined_response(combined_response)

            # Parse the plan text into a structured format
            plan_sections = self._parse_plan(plan_text)

            # Parse the tasks text into a structured format
            tasks = self._parse_tasks(tasks_text)

            return {
                "raw_plan": plan_text,
                "structured_plan": plan_sections,
                "tasks": tasks
            }
        except Exception as e:
            logger.error(f"Error generating plan and tasks: {e}")
            return {"error": str(e)}

    def _split_combined_response(self, combined_response: str) -> tuple:
        """
        Split the combined response into plan and tasks sections.

        Args:
            combined_response: Combined response from the AI

        Returns:
            Tuple of (plan_text, tasks_text)
        """
        # Look for clear section markers
        part2_markers = ["PART 2:", "DEVELOPMENT TASKS:", "# DEVELOPMENT TASKS", "## DEVELOPMENT TASKS"]

        for marker in part2_markers:
            if marker in combined_response:
                parts = combined_response.split(marker, 1)
                return parts[0].strip(), marker + parts[1].strip()

        # If no clear marker, try to find task patterns
        if "Task ID: 1" in combined_response:
            index = combined_response.find("Task ID: 1")
            return combined_response[:index].strip(), combined_response[index:].strip()

        # If all else fails, assume the first 70% is the plan and the rest is tasks
        split_point = int(len(combined_response) * 0.7)
        return combined_response[:split_point].strip(), combined_response[split_point:].strip()

    def generate_plan(self, project_description: str) -> Dict:
        """
        Generate a comprehensive project plan from a description.

        Args:
            project_description: Description of the project

        Returns:
            Dictionary containing the project plan
        """
        logger.info("Generating project plan")

        # Use the combined method but only return the plan part
        result = self.generate_plan_and_tasks(project_description)

        if "error" in result:
            return result

        return {
            "raw_plan": result.get("raw_plan", ""),
            "structured_plan": result.get("structured_plan", {})
        }

    def _parse_plan(self, plan_text: str) -> Dict:
        """
        Parse the generated plan text into a structured format.

        Args:
            plan_text: Raw plan text from the AI

        Returns:
            Dictionary with structured plan sections
        """
        # Simple parsing logic - in a real implementation, this would be more robust
        sections = {}
        current_section = None
        current_content = []

        for line in plan_text.split('\n'):
            line = line.strip()

            # Skip empty lines
            if not line:
                continue

            # Check if this is a section header
            if any(header in line.lower() for header in [
                "project overview", "technical architecture", "development phases",
                "implementation details", "development tasks", "testing strategy",
                "deployment considerations"
            ]):
                # Save the previous section if it exists
                if current_section:
                    sections[current_section] = '\n'.join(current_content)

                # Start a new section
                current_section = line
                current_content = []
            else:
                # Add content to the current section
                if current_section:
                    current_content.append(line)

        # Add the last section
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content)

        return sections

    def generate_tasks(self, project_plan: Dict) -> List[Dict]:
        """
        Extract actionable tasks from a project plan.

        Args:
            project_plan: The project plan dictionary

        Returns:
            List of task dictionaries
        """
        # Check if we already have tasks from the combined call
        if "tasks" in project_plan and project_plan["tasks"]:
            logger.info(f"Using {len(project_plan['tasks'])} tasks from combined plan and tasks generation")
            return project_plan["tasks"]

        # If we don't have tasks yet, try to extract them from the plan
        try:
            # Try to extract tasks from the plan directly without making another API call
            raw_plan = project_plan.get('raw_plan', '')

            # Look for task sections in the plan
            task_section_markers = ["DEVELOPMENT TASKS", "TASKS", "Task 1:", "Task ID: 1"]
            tasks_text = ""

            for marker in task_section_markers:
                if marker in raw_plan:
                    parts = raw_plan.split(marker, 1)
                    if len(parts) > 1:
                        tasks_text = marker + parts[1]
                        break

            # If we found a tasks section, parse it
            if tasks_text:
                tasks = self._parse_tasks(tasks_text)
                if tasks:
                    logger.info(f"Extracted {len(tasks)} tasks from the plan without additional API call")
                    return tasks

            # If we couldn't extract tasks, use the fallback
            logger.warning("Could not extract tasks from the plan, using fallback")
            return self._generate_fallback_tasks(project_plan)
        except Exception as e:
            logger.error(f"Error extracting tasks from plan: {e}")
            # Return fallback tasks
            return self._generate_fallback_tasks(project_plan)

    def _parse_tasks(self, tasks_text: str) -> List[Dict]:
        """
        Parse tasks from text.

        Args:
            tasks_text: Text containing task descriptions

        Returns:
            List of task dictionaries
        """
        # Parse tasks
        tasks = []
        current_task = {}

        # First, split by potential task boundaries
        sections = tasks_text.split("\n\n")

        for section in sections:
            lines = section.strip().split("\n")
            task_data = {}

            # Check if this section looks like a task
            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Try to parse key-value pairs
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip().lower()
                    value = value.strip()

                    # Map common key variations
                    if "task id" in key or "id" == key:
                        task_data["id"] = value
                    elif "task name" in key or "name" == key:
                        task_data["task name"] = value
                    elif "description" in key:
                        task_data["description"] = value
                    elif "complexity" in key:
                        task_data["complexity"] = value
                    elif "dependencies" in key:
                        task_data["dependencies"] = value
                    elif "category" in key:
                        task_data["category"] = value

            # If we found at least an ID and name, consider it a valid task
            if "id" in task_data and ("task name" in task_data or "description" in task_data):
                tasks.append(task_data)

        # If we couldn't parse any tasks using the section approach, try line-by-line
        if not tasks:
            current_task = {}

            for line in tasks_text.split('\n'):
                line = line.strip()

                # Skip empty lines
                if not line:
                    continue

                # Check if this is a new task
                if line.startswith("Task ID:") or line.startswith("1.") or (line.lower().startswith("task") and "id" in line.lower()):
                    # Save the previous task if it exists
                    if current_task and "id" in current_task:
                        tasks.append(current_task)

                    # Start a new task
                    current_task = {}

                    # Extract ID if possible
                    if ":" in line:
                        current_task["id"] = line.split(":", 1)[1].strip()
                    else:
                        # Try to extract a number
                        import re
                        numbers = re.findall(r'\d+', line)
                        if numbers:
                            current_task["id"] = numbers[0]
                        else:
                            current_task["id"] = line
                elif ":" in line:
                    # Add property to the current task
                    key, value = line.split(":", 1)
                    key = key.strip().lower()

                    # Map common key variations
                    if "task name" in key or "name" == key:
                        current_task["task name"] = value.strip()
                    elif "description" in key:
                        current_task["description"] = value.strip()
                    elif "complexity" in key:
                        current_task["complexity"] = value.strip()
                    elif "dependencies" in key:
                        current_task["dependencies"] = value.strip()
                    elif "category" in key:
                        current_task["category"] = value.strip()

            # Add the last task
            if current_task and "id" in current_task:
                tasks.append(current_task)

        # Ensure all tasks have the minimum required fields
        for task in tasks:
            if "task name" not in task and "id" in task:
                task["task name"] = f"Task {task['id']}"
            if "description" not in task:
                task["description"] = task.get("task name", f"Task {task.get('id', 'unknown')}")

        logger.info(f"Successfully parsed {len(tasks)} tasks")
        return tasks

    def _generate_fallback_tasks(self, project_plan: Dict) -> List[Dict]:
        """
        Generate fallback tasks when the API fails.

        Args:
            project_plan: The project plan dictionary

        Returns:
            List of basic task dictionaries
        """
        logger.info("Generating fallback tasks")

        # Extract development phases from the plan if possible
        phases = []
        raw_plan = project_plan.get('raw_plan', '')

        # Look for development phases section
        import re
        phases_section = re.search(r'(?:##\s*Development\s*Phases|Development\s*Phases:)(.*?)(?:##|$)',
                                  raw_plan, re.IGNORECASE | re.DOTALL)

        if phases_section:
            # Extract phases as bullet points
            phase_text = phases_section.group(1)
            phase_items = re.findall(r'(?:^|\n)(?:[-*]|\d+\.)\s*([^\n]+)', phase_text)

            if phase_items:
                phases = [item.strip() for item in phase_items]

        # If no phases found, use default phases
        if not phases:
            phases = [
                "Setup and foundation",
                "Core functionality",
                "Additional features",
                "Testing and refinement"
            ]

        # Create tasks based on phases
        tasks = []
        for i, phase in enumerate(phases):
            task_id = str(i + 1)
            task_name = phase

            # Create a description based on the phase name
            if "setup" in phase.lower() or "foundation" in phase.lower():
                description = "Set up the project structure and install dependencies"
            elif "core" in phase.lower() or "functionality" in phase.lower():
                description = "Implement the core functionality of the application"
            elif "additional" in phase.lower() or "feature" in phase.lower():
                description = "Add additional features and enhancements"
            elif "test" in phase.lower() or "refine" in phase.lower():
                description = "Test the application and refine based on results"
            else:
                description = f"Implement {phase}"

            # Determine complexity
            if i == 0:
                complexity = "Low"
            elif i == len(phases) - 1:
                complexity = "Medium"
            else:
                complexity = "High"

            # Determine dependencies
            dependencies = "None" if i == 0 else str(i)

            # Determine category
            if "setup" in phase.lower():
                category = "Setup"
            elif "test" in phase.lower():
                category = "Testing"
            else:
                category = "Development"

            tasks.append({
                "id": task_id,
                "task name": task_name,
                "description": description,
                "complexity": complexity,
                "dependencies": dependencies,
                "category": category
            })

        logger.info(f"Generated {len(tasks)} fallback tasks")
        return tasks
