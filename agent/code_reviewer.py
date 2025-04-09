"""
Code review module for the AI Code Agent.
"""
import logging
import os
import json
from typing import Dict, List, Optional, Union
from pathlib import Path

from models.gemini_client import GeminiClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CodeReviewer:
    """
    Responsible for reviewing code quality and providing suggestions.
    """

    def __init__(self, gemini_client: Optional[GeminiClient] = None):
        """
        Initialize the code reviewer.

        Args:
            gemini_client: GeminiClient instance for AI capabilities
        """
        self.gemini_client = gemini_client or GeminiClient()

    def review_file(self, file_path: Union[str, Path], auto_fix: bool = False) -> Dict:
        """
        Review a single file for code quality and issues.

        Args:
            file_path: Path to the file to review
            auto_fix: Whether to automatically fix issues

        Returns:
            Dictionary with review results
        """
        file_path = Path(file_path)

        if not file_path.exists():
            return {
                "success": False,
                "message": f"File not found: {file_path}"
            }

        try:
            # Read the file
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()

            # Get file extension
            extension = file_path.suffix.lower()
            language = extension[1:] if extension else ""  # Remove the dot

            # Analyze the code
            analysis = self.gemini_client.analyze_code(code)

            result = {
                "success": True,
                "file_path": str(file_path),
                "analysis": analysis,
                "fixed": False,
                "changes": []
            }

            # Auto-fix issues if requested
            if auto_fix and "issues" in analysis:
                issues = analysis["issues"]
                if issues and len(issues) > 0:
                    # Generate improved code
                    improved_code = self._generate_improved_code(code, analysis, language)

                    if improved_code and improved_code != code:
                        # Backup the original file
                        backup_path = str(file_path) + ".bak"
                        with open(backup_path, 'w', encoding='utf-8') as f:
                            f.write(code)

                        # Write the improved code
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(improved_code)

                        result["fixed"] = True
                        result["changes"].append({
                            "file": str(file_path),
                            "backup": backup_path,
                            "issues_fixed": len(issues)
                        })

            return result
        except Exception as e:
            logger.error(f"Error reviewing file {file_path}: {e}")
            return {
                "success": False,
                "file_path": str(file_path),
                "error": str(e)
            }

    def _generate_improved_code(self, code: str, analysis: Dict, language: str) -> Optional[str]:
        """
        Generate improved code based on analysis.

        Args:
            code: Original code
            analysis: Code analysis results
            language: Programming language

        Returns:
            Improved code or None if no improvements could be made
        """
        try:
            # Extract issues from analysis
            issues = analysis.get("issues", [])
            if not issues:
                return None

            # Create a prompt for code improvement
            issues_text = "\n".join([f"- {issue.get('severity', 'unknown')} issue: {issue.get('description', 'No description')}" for issue in issues])

            improvement_prompt = f"""
            I need you to improve the following {language} code by fixing these issues:

            ISSUES TO FIX:
            {issues_text}

            ORIGINAL CODE:
            ```{language}
            {code}
            ```

            Please provide ONLY the improved code without any explanations or markdown formatting.
            Maintain the same overall structure and functionality while fixing the issues.
            Make sure the code is complete and properly formatted.
            """

            # Generate improved code
            improved_code = self.gemini_client.generate_text(improvement_prompt)

            # Clean up the response (remove markdown code blocks if present)
            if improved_code.startswith("```"):
                # Find the language identifier and skip it
                first_line_end = improved_code.find("\n")
                if first_line_end > 0:
                    # Find the closing code block
                    closing_block = improved_code.rfind("```")
                    if closing_block > first_line_end:
                        improved_code = improved_code[first_line_end+1:closing_block].strip()

            return improved_code
        except Exception as e:
            logger.error(f"Error generating improved code: {e}")
            return None

    def review_directory(self, directory_path: Union[str, Path], file_extensions: Optional[List[str]] = None, auto_fix: bool = False) -> Dict:
        """
        Review all files in a directory.

        Args:
            directory_path: Path to the directory to review
            file_extensions: List of file extensions to include (None for all)
            auto_fix: Whether to automatically fix issues

        Returns:
            Dictionary with review results
        """
        directory_path = Path(directory_path)

        if not directory_path.exists() or not directory_path.is_dir():
            return {
                "success": False,
                "message": f"Directory not found: {directory_path}"
            }

        # Default file extensions to review
        if file_extensions is None:
            file_extensions = ['.py', '.js', '.ts', '.html', '.css', '.java', '.c', '.cpp', '.go', '.rs', '.rb', '.php']

        results = {
            "success": True,
            "directory_path": str(directory_path),
            "files_reviewed": 0,
            "files_with_issues": 0,
            "reviews": []
        }

        try:
            # Find all files with the specified extensions
            for root, _, files in os.walk(directory_path):
                for file in files:
                    file_path = Path(root) / file

                    # Check if the file has one of the specified extensions
                    if file_path.suffix.lower() in file_extensions:
                        # Review the file
                        review = self.review_file(file_path, auto_fix=auto_fix)
                        results["files_reviewed"] += 1

                        # Check if the file has issues
                        if review["success"] and "analysis" in review:
                            analysis = review["analysis"]

                            # Try to parse issues from the analysis
                            issues = []
                            try:
                                if isinstance(analysis, dict) and "analysis" in analysis:
                                    # Try to parse JSON from the analysis text
                                    analysis_text = analysis["analysis"]
                                    json_start = analysis_text.find('{')
                                    json_end = analysis_text.rfind('}') + 1

                                    if json_start >= 0 and json_end > json_start:
                                        json_str = analysis_text[json_start:json_end]
                                        analysis_json = json.loads(json_str)

                                        if "issues" in analysis_json and analysis_json["issues"]:
                                            issues = analysis_json["issues"]
                            except Exception as e:
                                logger.warning(f"Error parsing analysis JSON: {e}")

                            if issues:
                                results["files_with_issues"] += 1

                            # Add the review to the results
                            results["reviews"].append({
                                "file_path": str(file_path),
                                "has_issues": bool(issues),
                                "issues_count": len(issues),
                                "analysis": analysis
                            })

            return results
        except Exception as e:
            logger.error(f"Error reviewing directory {directory_path}: {e}")
            return {
                "success": False,
                "directory_path": str(directory_path),
                "error": str(e)
            }

    def generate_review_report(self, review_results: Dict) -> str:
        """
        Generate a human-readable report from review results.

        Args:
            review_results: Dictionary with review results

        Returns:
            Formatted review report
        """
        if not review_results.get("success", False):
            return f"Review failed: {review_results.get('error', 'Unknown error')}"

        report = []
        report.append("# Code Review Report")
        report.append("")

        # Add summary
        report.append("## Summary")
        report.append("")
        report.append(f"- Directory: {review_results.get('directory_path', 'N/A')}")
        report.append(f"- Files reviewed: {review_results.get('files_reviewed', 0)}")
        report.append(f"- Files with issues: {review_results.get('files_with_issues', 0)}")
        report.append("")

        # Add file reviews
        report.append("## File Reviews")
        report.append("")

        # Track fixed files
        fixed_files = 0

        for review in review_results.get("reviews", []):
            file_path = review.get("file_path", "Unknown file")
            has_issues = review.get("has_issues", False)
            issues_count = review.get("issues_count", 0)
            fixed = review.get("fixed", False)
            changes = review.get("changes", [])

            report.append(f"### {file_path}")
            report.append("")

            if fixed:
                fixed_files += 1
                report.append(f"**✅ Issues fixed:** {issues_count}")
                report.append("")
                report.append("The following issues were automatically fixed:")
                report.append("")

                # Add details about changes
                for change in changes:
                    report.append(f"- Fixed {change.get('issues_fixed', 0)} issues in {change.get('file', 'unknown file')}")
                    report.append(f"  (Original backed up to {change.get('backup', 'unknown location')})")
                report.append("")

            if has_issues:
                if fixed:
                    report.append(f"**Original issues found:** {issues_count}")
                else:
                    report.append(f"**Issues found:** {issues_count}")
                report.append("")

                # Try to extract issues from the analysis
                analysis = review.get("analysis", {})
                if isinstance(analysis, dict):
                    if "issues" in analysis and isinstance(analysis["issues"], list):
                        for i, issue in enumerate(analysis["issues"]):
                            severity = issue.get("severity", "unknown")
                            description = issue.get("description", "No description")
                            line = issue.get("line", "unknown")
                            suggestion = issue.get("suggestion", "No suggestion")

                            report.append(f"**Issue {i+1}:** {severity.upper()} at line {line}")
                            report.append(f"- Description: {description}")
                            report.append(f"- Suggestion: {suggestion}")
                            report.append("")
                    elif "analysis" in analysis:
                        analysis_text = analysis["analysis"]
                        report.append("```")
                        report.append(analysis_text)
                        report.append("```")
            else:
                report.append("No issues found.")

            report.append("")

        # Add summary of fixed files
        if fixed_files > 0:
            report.insert(6, f"- **Files automatically fixed:** {fixed_files}")
            report.insert(7, "")

        return "\n".join(report)

    def suggest_improvements(self, code: str, language: str = "python") -> Dict:
        """
        Suggest improvements for a code snippet.

        Args:
            code: Code snippet to improve
            language: Programming language of the code

        Returns:
            Dictionary with improvement suggestions
        """
        improvement_prompt = f"""
        Suggest improvements for the following {language} code:

        ```{language}
        {code}
        ```

        Focus on:
        1. Code quality and readability
        2. Performance optimizations
        3. Security considerations
        4. Best practices for {language}
        5. Potential bugs or edge cases

        Provide specific, actionable suggestions with code examples where appropriate.
        """

        try:
            suggestions = self.gemini_client.generate_text(improvement_prompt)

            return {
                "success": True,
                "language": language,
                "suggestions": suggestions
            }
        except Exception as e:
            logger.error(f"Error generating improvement suggestions: {e}")
            return {
                "success": False,
                "error": str(e)
            }
