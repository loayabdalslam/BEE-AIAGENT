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

    def generate_plan(self, project_description: str) -> Dict:
        """
        Generate a comprehensive project plan from a description.

        Args:
            project_description: Description of the project

        Returns:
            Dictionary containing the project plan
        """
        logger.info("Generating project plan")

        planning_prompt = f"""
        Create a comprehensive software development plan for the following project:

        PROJECT DESCRIPTION:
        {project_description}

        Your plan should include:

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

        5. Development Tasks:
           - Ordered list of specific tasks
           - Estimated complexity for each task (Low/Medium/High)

        6. Testing Strategy:
           - Unit testing approach
           - Integration testing approach
           - Manual testing requirements

        7. Deployment Considerations:
           - Recommended deployment platform
           - Configuration requirements
           - CI/CD pipeline suggestions

        Format your response as a structured plan that can be followed step by step.
        """

        try:
            plan_text = self.gemini_client.generate_text(
                planning_prompt,
                temperature=PLANNING_TEMPERATURE
            )

            # Parse the plan text into a structured format
            # In a real implementation, you might want to use a more sophisticated parsing approach
            plan_sections = self._parse_plan(plan_text)

            return {
                "raw_plan": plan_text,
                "structured_plan": plan_sections
            }
        except Exception as e:
            logger.error(f"Error generating plan: {e}")
            return {"error": str(e)}

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
        tasks_prompt = f"""
        Based on the following project plan, generate a list of specific, actionable development tasks:

        {project_plan.get('raw_plan', '')}

        For each task, provide:
        1. Task ID
        2. Task name
        3. Description
        4. Estimated complexity (Low/Medium/High)
        5. Dependencies (IDs of tasks that must be completed first)
        6. Category (Setup, Backend, Frontend, Testing, Deployment, etc.)

        Format your response as a list of tasks with clear separation between tasks.
        Use the following format for each task:

        Task ID: 1
        Task name: Example task name
        Description: Detailed description of the task
        Estimated complexity: Low/Medium/High
        Dependencies: None or comma-separated IDs
        Category: Category name
        """

        try:
            # Generate tasks text
            tasks_text = self.gemini_client.generate_text(tasks_prompt)

            if not tasks_text or len(tasks_text.strip()) < 10:
                logger.error(f"Empty or very short response from API: '{tasks_text}'")
                # Create a fallback task list based on the project plan
                return self._generate_fallback_tasks(project_plan)

            # Parse tasks
            tasks = []
            current_task = {}
            task_lines = []

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

            # If we still couldn't parse any tasks, use the fallback
            if not tasks:
                logger.warning("Could not parse any tasks from the API response")
                return self._generate_fallback_tasks(project_plan)

            # Ensure all tasks have the minimum required fields
            for task in tasks:
                if "task name" not in task and "id" in task:
                    task["task name"] = f"Task {task['id']}"
                if "description" not in task:
                    task["description"] = task.get("task name", f"Task {task.get('id', 'unknown')}")

            logger.info(f"Successfully generated {len(tasks)} tasks")
            return tasks
        except Exception as e:
            logger.error(f"Error generating tasks: {e}")
            # Return fallback tasks instead of empty list
            return self._generate_fallback_tasks(project_plan)

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
