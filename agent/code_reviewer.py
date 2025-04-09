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
    
    def review_file(self, file_path: Union[str, Path]) -> Dict:
        """
        Review a single file for code quality and issues.
        
        Args:
            file_path: Path to the file to review
            
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
            with open(file_path, 'r') as f:
                code = f.read()
            
            # Get file extension
            extension = file_path.suffix.lower()
            
            # Analyze the code
            analysis = self.gemini_client.analyze_code(code)
            
            return {
                "success": True,
                "file_path": str(file_path),
                "analysis": analysis
            }
        except Exception as e:
            logger.error(f"Error reviewing file {file_path}: {e}")
            return {
                "success": False,
                "file_path": str(file_path),
                "error": str(e)
            }
    
    def review_directory(self, directory_path: Union[str, Path], file_extensions: Optional[List[str]] = None) -> Dict:
        """
        Review all files in a directory.
        
        Args:
            directory_path: Path to the directory to review
            file_extensions: List of file extensions to include (None for all)
            
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
                        review = self.review_file(file_path)
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
        
        for review in review_results.get("reviews", []):
            file_path = review.get("file_path", "Unknown file")
            has_issues = review.get("has_issues", False)
            issues_count = review.get("issues_count", 0)
            
            report.append(f"### {file_path}")
            report.append("")
            
            if has_issues:
                report.append(f"**Issues found:** {issues_count}")
                report.append("")
                
                # Try to extract issues from the analysis
                analysis = review.get("analysis", {})
                if isinstance(analysis, dict) and "analysis" in analysis:
                    analysis_text = analysis["analysis"]
                    report.append("```")
                    report.append(analysis_text)
                    report.append("```")
            else:
                report.append("No issues found.")
            
            report.append("")
        
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
