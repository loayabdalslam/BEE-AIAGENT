"""
Markdown logger for the AI Code Agent.
"""
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

class MarkdownLogger:
    """
    Logger that creates nicely formatted Markdown logs.
    """
    
    def __init__(self, project_dir: Optional[Path] = None, project_name: Optional[str] = None):
        """
        Initialize the Markdown logger.
        
        Args:
            project_dir: Project directory
            project_name: Project name
        """
        self.project_dir = project_dir
        self.project_name = project_name or "ai-code-agent"
        self.log_entries = []
        self.current_section = None
        self.current_subsection = None
        
        # Create log directory if it doesn't exist
        if self.project_dir:
            self.log_dir = self.project_dir / "logs"
            self.log_dir.mkdir(exist_ok=True, parents=True)
            self.log_file = self.log_dir / f"development_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        else:
            self.log_dir = None
            self.log_file = None
    
    def start_section(self, title: str) -> None:
        """
        Start a new section in the log.
        
        Args:
            title: Section title
        """
        self.current_section = title
        self.current_subsection = None
        self.log_entries.append({
            "type": "section",
            "title": title,
            "timestamp": datetime.now()
        })
    
    def start_subsection(self, title: str) -> None:
        """
        Start a new subsection in the log.
        
        Args:
            title: Subsection title
        """
        self.current_subsection = title
        self.log_entries.append({
            "type": "subsection",
            "title": title,
            "timestamp": datetime.now()
        })
    
    def log_text(self, text: str) -> None:
        """
        Log text.
        
        Args:
            text: Text to log
        """
        self.log_entries.append({
            "type": "text",
            "content": text,
            "timestamp": datetime.now()
        })
    
    def log_code(self, code: str, language: str = "") -> None:
        """
        Log code.
        
        Args:
            code: Code to log
            language: Programming language
        """
        self.log_entries.append({
            "type": "code",
            "content": code,
            "language": language,
            "timestamp": datetime.now()
        })
    
    def log_command(self, command: str, output: Optional[str] = None, success: bool = True) -> None:
        """
        Log a command execution.
        
        Args:
            command: Command that was executed
            output: Command output
            success: Whether the command was successful
        """
        self.log_entries.append({
            "type": "command",
            "command": command,
            "output": output,
            "success": success,
            "timestamp": datetime.now()
        })
    
    def log_file_creation(self, file_path: Union[str, Path], content_preview: Optional[str] = None) -> None:
        """
        Log file creation.
        
        Args:
            file_path: Path to the created file
            content_preview: Preview of the file content
        """
        self.log_entries.append({
            "type": "file_creation",
            "file_path": str(file_path),
            "content_preview": content_preview,
            "timestamp": datetime.now()
        })
    
    def log_plan(self, plan: Dict[str, Any]) -> None:
        """
        Log a project plan.
        
        Args:
            plan: Project plan
        """
        self.log_entries.append({
            "type": "plan",
            "plan": plan,
            "timestamp": datetime.now()
        })
    
    def log_tasks(self, tasks: List[Dict[str, Any]]) -> None:
        """
        Log tasks.
        
        Args:
            tasks: List of tasks
        """
        self.log_entries.append({
            "type": "tasks",
            "tasks": tasks,
            "timestamp": datetime.now()
        })
    
    def save(self) -> Optional[Path]:
        """
        Save the log to a Markdown file.
        
        Returns:
            Path to the log file or None if no log file is set
        """
        if not self.log_file:
            return None
        
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write(f"# {self.project_name} Development Log\n\n")
            f.write(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for entry in self.log_entries:
                entry_type = entry["type"]
                timestamp = entry["timestamp"].strftime("%H:%M:%S")
                
                if entry_type == "section":
                    f.write(f"\n## {entry['title']}\n\n")
                    f.write(f"*{timestamp}*\n\n")
                
                elif entry_type == "subsection":
                    f.write(f"\n### {entry['title']}\n\n")
                    f.write(f"*{timestamp}*\n\n")
                
                elif entry_type == "text":
                    f.write(f"{entry['content']}\n\n")
                
                elif entry_type == "code":
                    language = entry["language"]
                    f.write(f"```{language}\n{entry['content']}\n```\n\n")
                
                elif entry_type == "command":
                    f.write(f"**Command:** `{entry['command']}`\n\n")
                    if entry["success"]:
                        f.write("✅ Command executed successfully\n\n")
                    else:
                        f.write("❌ Command failed\n\n")
                    
                    if entry["output"]:
                        f.write("**Output:**\n\n")
                        f.write(f"```\n{entry['output']}\n```\n\n")
                
                elif entry_type == "file_creation":
                    f.write(f"**Created file:** `{entry['file_path']}`\n\n")
                    if entry["content_preview"]:
                        f.write("**Preview:**\n\n")
                        f.write(f"```\n{entry['content_preview']}\n```\n\n")
                
                elif entry_type == "plan":
                    f.write("**Project Plan:**\n\n")
                    if "raw_plan" in entry["plan"]:
                        f.write(entry["plan"]["raw_plan"])
                    else:
                        f.write("*Plan details not available*\n\n")
                
                elif entry_type == "tasks":
                    f.write("**Development Tasks:**\n\n")
                    for i, task in enumerate(entry["tasks"]):
                        task_name = task.get("task name", task.get("name", f"Task {i+1}"))
                        description = task.get("description", "No description")
                        complexity = task.get("complexity", "Unknown")
                        category = task.get("category", "Uncategorized")
                        
                        f.write(f"1. **{task_name}**\n")
                        f.write(f"   - Description: {description}\n")
                        f.write(f"   - Complexity: {complexity}\n")
                        f.write(f"   - Category: {category}\n\n")
        
        return self.log_file
    
    def get_markdown(self) -> str:
        """
        Get the log as a Markdown string.
        
        Returns:
            Markdown string
        """
        markdown = []
        markdown.append(f"# {self.project_name} Development Log\n")
        markdown.append(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        for entry in self.log_entries:
            entry_type = entry["type"]
            timestamp = entry["timestamp"].strftime("%H:%M:%S")
            
            if entry_type == "section":
                markdown.append(f"\n## {entry['title']}\n")
                markdown.append(f"*{timestamp}*\n")
            
            elif entry_type == "subsection":
                markdown.append(f"\n### {entry['title']}\n")
                markdown.append(f"*{timestamp}*\n")
            
            elif entry_type == "text":
                markdown.append(f"{entry['content']}\n")
            
            elif entry_type == "code":
                language = entry["language"]
                markdown.append(f"```{language}\n{entry['content']}\n```\n")
            
            elif entry_type == "command":
                markdown.append(f"**Command:** `{entry['command']}`\n")
                if entry["success"]:
                    markdown.append("✅ Command executed successfully\n")
                else:
                    markdown.append("❌ Command failed\n")
                
                if entry["output"]:
                    markdown.append("**Output:**\n")
                    markdown.append(f"```\n{entry['output']}\n```\n")
            
            elif entry_type == "file_creation":
                markdown.append(f"**Created file:** `{entry['file_path']}`\n")
                if entry["content_preview"]:
                    markdown.append("**Preview:**\n")
                    markdown.append(f"```\n{entry['content_preview']}\n```\n")
            
            elif entry_type == "plan":
                markdown.append("**Project Plan:**\n")
                if "raw_plan" in entry["plan"]:
                    markdown.append(entry["plan"]["raw_plan"])
                else:
                    markdown.append("*Plan details not available*\n")
            
            elif entry_type == "tasks":
                markdown.append("**Development Tasks:**\n")
                for i, task in enumerate(entry["tasks"]):
                    task_name = task.get("task name", task.get("name", f"Task {i+1}"))
                    description = task.get("description", "No description")
                    complexity = task.get("complexity", "Unknown")
                    category = task.get("category", "Uncategorized")
                    
                    markdown.append(f"1. **{task_name}**\n")
                    markdown.append(f"   - Description: {description}\n")
                    markdown.append(f"   - Complexity: {complexity}\n")
                    markdown.append(f"   - Category: {category}\n")
        
        return "\n".join(markdown)
