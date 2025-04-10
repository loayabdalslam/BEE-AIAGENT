"""
Local deployment utilities for the AI Code Agent.
"""
import logging
import os
import platform
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Union

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LocalDeployer:
    """
    Responsible for deploying projects locally.
    """

    def __init__(self, project_dir: Union[str, Path]):
        """
        Initialize the local deployer.

        Args:
            project_dir: Path to the project directory
        """
        self.project_dir = Path(project_dir)

        if not self.project_dir.exists() or not self.project_dir.is_dir():
            raise ValueError(f"Project directory not found: {self.project_dir}")

    def detect_project_type(self) -> str:
        """
        Detect the type of project based on files in the directory.

        Returns:
            Project type (e.g., flask, react, django, etc.)
        """
        # Check for package.json (Node.js projects)
        if (self.project_dir / "package.json").exists():
            # Check for specific frameworks
            if (self.project_dir / "angular.json").exists():
                return "angular"
            elif (self.project_dir / "next.config.js").exists() or (self.project_dir / "next.config.ts").exists():
                return "nextjs"
            elif (self.project_dir / "vite.config.js").exists() or (self.project_dir / "vite.config.ts").exists():
                return "vite"
            elif (self.project_dir / "react-scripts").exists() or self._check_dependency("react-scripts"):
                return "react"
            else:
                return "nodejs"

        # Check for Python projects
        if (self.project_dir / "requirements.txt").exists() or list(self.project_dir.glob("*.py")):
            # Check for specific frameworks
            if (self.project_dir / "manage.py").exists():
                return "django"
            elif self._check_file_content("*.py", "flask"):
                return "flask"
            elif self._check_file_content("*.py", "fastapi"):
                return "fastapi"
            else:
                return "python"

        # Check for other project types
        if (self.project_dir / "pom.xml").exists():
            return "java-maven"
        elif (self.project_dir / "build.gradle").exists():
            return "java-gradle"
        elif (self.project_dir / "Cargo.toml").exists():
            return "rust"
        elif (self.project_dir / "go.mod").exists():
            return "go"

        # Default to unknown
        return "unknown"

    def _check_dependency(self, dependency: str) -> bool:
        """
        Check if a dependency is listed in package.json.

        Args:
            dependency: Dependency name to check

        Returns:
            True if the dependency is found, False otherwise
        """
        package_json_path = self.project_dir / "package.json"
        if not package_json_path.exists():
            return False

        try:
            import json
            with open(package_json_path, 'r') as f:
                package_data = json.load(f)

            dependencies = package_data.get("dependencies", {})
            dev_dependencies = package_data.get("devDependencies", {})

            return dependency in dependencies or dependency in dev_dependencies
        except Exception as e:
            logger.error(f"Error checking dependency {dependency}: {e}")
            return False

    def _check_file_content(self, file_pattern: str, content: str) -> bool:
        """
        Check if any file matching the pattern contains the specified content.

        Args:
            file_pattern: Glob pattern for files to check
            content: Content to search for

        Returns:
            True if the content is found in any matching file, False otherwise
        """
        try:
            for file_path in self.project_dir.glob(file_pattern):
                if file_path.is_file():
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        file_content = f.read()
                        if content.lower() in file_content.lower():
                            return True
            return False
        except Exception as e:
            logger.error(f"Error checking file content: {e}")
            return False

    def deploy_locally(self) -> Dict:
        """
        Deploy the project locally based on its type.
        Focuses on installing dependencies and providing start commands.

        Returns:
            Dictionary with deployment results
        """
        project_type = self.detect_project_type()
        logger.info(f"Detected project type: {project_type}")

        if project_type == "unknown":
            return {
                "success": False,
                "message": "Unknown project type. Could not determine how to deploy.",
                "project_type": project_type
            }

        # First, ensure package files exist
        self._ensure_package_files(project_type)

        # Deploy based on project type
        if project_type in ["react", "vite", "nextjs", "angular", "nodejs"]:
            return self._deploy_nodejs(project_type)
        elif project_type in ["flask", "fastapi", "django", "python"]:
            return self._deploy_python(project_type)
        elif project_type in ["java-maven", "java-gradle"]:
            return self._deploy_java(project_type)
        elif project_type == "rust":
            return self._deploy_rust()
        elif project_type == "go":
            return self._deploy_go()
        else:
            return {
                "success": False,
                "message": f"Deployment for {project_type} projects is not yet supported.",
                "project_type": project_type
            }

    def _ensure_package_files(self, project_type: str) -> None:
        """
        Ensure that appropriate package files exist for the project type.

        Args:
            project_type: Type of project
        """
        # Check for package files
        has_package_json = (self.project_dir / "package.json").exists()
        has_requirements = (self.project_dir / "requirements.txt").exists()
        has_gemfile = (self.project_dir / "Gemfile").exists()
        has_cargo_toml = (self.project_dir / "Cargo.toml").exists()
        has_pom_xml = (self.project_dir / "pom.xml").exists()
        has_build_gradle = (self.project_dir / "build.gradle").exists()

        # Create basic package files if they don't exist
        if project_type in ["react", "vite", "nextjs", "angular", "nodejs"] and not has_package_json:
            logger.info("Creating basic package.json file")
            package_json = {
                "name": self.project_dir.name,
                "version": "1.0.0",
                "description": "A JavaScript project",
                "main": "index.js",
                "scripts": {
                    "start": "node index.js"
                },
                "dependencies": {},
                "devDependencies": {}
            }

            # Add framework-specific settings
            if project_type == "react":
                package_json["dependencies"]["react"] = "^18.2.0"
                package_json["dependencies"]["react-dom"] = "^18.2.0"
                package_json["scripts"] = {"start": "react-scripts start", "build": "react-scripts build"}
            elif project_type == "vite":
                package_json["scripts"] = {"dev": "vite", "build": "vite build"}
            elif project_type == "nextjs":
                package_json["dependencies"]["next"] = "^13.4.7"
                package_json["dependencies"]["react"] = "^18.2.0"
                package_json["dependencies"]["react-dom"] = "^18.2.0"
                package_json["scripts"] = {"dev": "next dev", "build": "next build", "start": "next start"}
            elif project_type == "angular":
                package_json["scripts"] = {"ng": "ng", "start": "ng serve", "build": "ng build"}

            import json
            with open(self.project_dir / "package.json", "w", encoding='utf-8') as f:
                json.dump(package_json, f, indent=2)

        # Create requirements.txt for Python projects
        if project_type in ["flask", "fastapi", "django", "python"] and not has_requirements:
            logger.info("Creating basic requirements.txt file")
            requirements = []

            if project_type == "flask":
                requirements.extend(["Flask>=2.3.2", "Werkzeug>=2.3.6", "Jinja2>=3.1.2"])
            elif project_type == "django":
                requirements.extend(["Django>=4.2.3", "djangorestframework>=3.14.0"])
            elif project_type == "fastapi":
                requirements.extend(["fastapi>=0.100.0", "uvicorn>=0.22.0", "pydantic>=2.0.3"])
            else:
                requirements.extend(["requests>=2.31.0", "python-dotenv>=1.0.0"])

            with open(self.project_dir / "requirements.txt", "w", encoding='utf-8') as f:
                f.write("\n".join(requirements))

    def _deploy_nodejs(self, project_type: str) -> Dict:
        """
        Deploy a Node.js project locally by installing dependencies.

        Args:
            project_type: Specific Node.js project type

        Returns:
            Dictionary with deployment results
        """
        try:
            # Check if npm is installed
            try:
                subprocess.run(["npm", "--version"], check=True, capture_output=True)
            except Exception:
                return {
                    "success": False,
                    "message": "npm is not installed. Please install Node.js and npm.",
                    "project_type": project_type
                }

            # Install dependencies
            logger.info("Installing dependencies...")
            install_process = subprocess.run(
                ["npm", "install"],
                cwd=self.project_dir,
                capture_output=True,
                text=True
            )

            if install_process.returncode != 0:
                return {
                    "success": False,
                    "message": f"Failed to install dependencies: {install_process.stderr}",
                    "project_type": project_type,
                    "stderr": install_process.stderr
                }

            # Determine the start command based on project type
            if project_type == "nextjs":
                start_command = "npm run dev"
                url = "http://localhost:3000"
            elif project_type == "vite":
                start_command = "npm run dev"
                url = "http://localhost:5173"
            elif project_type == "angular":
                start_command = "ng serve"
                url = "http://localhost:4200"
            else:
                start_command = "npm start"
                url = "http://localhost:3000"  # Default for React and Node.js

            return {
                "success": True,
                "message": f"Dependencies installed successfully. To start the server, run: '{start_command}' in the project directory.",
                "project_type": project_type,
                "url": url,
                "start_command": start_command
            }
        except Exception as e:
            logger.error(f"Error deploying Node.js project: {e}")
            return {
                "success": False,
                "message": f"Error deploying Node.js project: {str(e)}",
                "project_type": project_type
            }

    def _deploy_python(self, project_type: str) -> Dict:
        """
        Deploy a Python project locally by setting up a virtual environment and installing dependencies.

        Args:
            project_type: Specific Python project type

        Returns:
            Dictionary with deployment results
        """
        try:
            # Check if Python is installed
            try:
                subprocess.run(["python", "--version"], check=True, capture_output=True)
                python_cmd = "python"
            except Exception:
                try:
                    subprocess.run(["python3", "--version"], check=True, capture_output=True)
                    python_cmd = "python3"
                except Exception:
                    return {
                        "success": False,
                        "message": "Python is not installed or not in PATH.",
                        "project_type": project_type
                    }

            # Create virtual environment
            logger.info("Setting up virtual environment...")
            venv_dir = self.project_dir / "venv"

            if not venv_dir.exists():
                subprocess.run(
                    [python_cmd, "-m", "venv", "venv"],
                    cwd=self.project_dir,
                    check=True,
                    capture_output=True
                )

            # Determine the pip and python commands
            if platform.system() == "Windows":
                pip_cmd = str(venv_dir / "Scripts" / "pip")
                python_interpreter = str(venv_dir / "Scripts" / "python")
            else:
                pip_cmd = str(venv_dir / "bin" / "pip")
                python_interpreter = str(venv_dir / "bin" / "python")

            # Install dependencies
            if (self.project_dir / "requirements.txt").exists():
                logger.info("Installing dependencies...")
                install_process = subprocess.run(
                    [pip_cmd, "install", "-r", "requirements.txt"],
                    cwd=self.project_dir,
                    capture_output=True,
                    text=True
                )

                if install_process.returncode != 0:
                    return {
                        "success": False,
                        "message": f"Failed to install dependencies: {install_process.stderr}",
                        "project_type": project_type,
                        "stderr": install_process.stderr
                    }

            # Determine the start command based on project type
            if project_type == "flask":
                # Find the Flask app file
                app_file = None
                for file_path in self.project_dir.glob("*.py"):
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if "Flask(__name__)" in content:
                            app_file = file_path.name
                            break

                if not app_file:
                    app_file = "app.py"  # Default Flask app file

                start_command = f"set FLASK_APP={app_file} && {python_interpreter} -m flask run" if platform.system() == "Windows" else f"FLASK_APP={app_file} {python_interpreter} -m flask run"
                url = "http://localhost:5000"
            elif project_type == "fastapi":
                # Find the FastAPI app file
                app_file = None
                for file_path in self.project_dir.glob("*.py"):
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if "FastAPI(" in content:
                            app_file = file_path.name
                            break

                if not app_file:
                    app_file = "main.py"  # Default FastAPI app file

                # Install uvicorn if not already installed
                subprocess.run(
                    [pip_cmd, "install", "uvicorn"],
                    cwd=self.project_dir,
                    capture_output=True
                )

                module_name = app_file.replace(".py", "")
                start_command = f"{python_interpreter} -m uvicorn {module_name}:app --reload"
                url = "http://localhost:8000"
            elif project_type == "django":
                start_command = f"{python_interpreter} manage.py runserver"
                url = "http://localhost:8000"
            else:
                # Find a Python file with a main function or if __name__ == "__main__" block
                main_file = None
                for file_path in self.project_dir.glob("*.py"):
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if "if __name__ == \"__main__\"" in content or "def main(" in content:
                            main_file = file_path.name
                            break

                if not main_file:
                    return {
                        "success": False,
                        "message": "Could not find a main Python file to run.",
                        "project_type": project_type
                    }

                start_command = f"{python_interpreter} {main_file}"
                url = None  # No URL for regular Python scripts

            return {
                "success": True,
                "message": f"Virtual environment created and dependencies installed successfully. To start the server, run: '{start_command}' in the project directory.",
                "project_type": project_type,
                "url": url,
                "start_command": start_command
            }
        except Exception as e:
            logger.error(f"Error deploying Python project: {e}")
            return {
                "success": False,
                "message": f"Error deploying Python project: {str(e)}",
                "project_type": project_type
            }

    def _deploy_java(self, project_type: str) -> Dict:
        """
        Deploy a Java project locally.

        Args:
            project_type: Specific Java project type (maven or gradle)

        Returns:
            Dictionary with deployment results
        """
        try:
            # Check if Java is installed
            try:
                subprocess.run(["java", "--version"], check=True, capture_output=True)
            except Exception:
                return {
                    "success": False,
                    "message": "Java is not installed or not in PATH.",
                    "project_type": project_type
                }

            # Build the project
            logger.info("Building the project...")

            if project_type == "java-maven":
                # Check if Maven is installed
                try:
                    subprocess.run(["mvn", "--version"], check=True, capture_output=True)
                except Exception:
                    return {
                        "success": False,
                        "message": "Maven is not installed or not in PATH.",
                        "project_type": project_type
                    }

                build_process = subprocess.run(
                    ["mvn", "clean", "package"],
                    cwd=self.project_dir,
                    capture_output=True,
                    text=True
                )
            else:  # java-gradle
                # Check if Gradle is installed
                try:
                    subprocess.run(["gradle", "--version"], check=True, capture_output=True)
                except Exception:
                    return {
                        "success": False,
                        "message": "Gradle is not installed or not in PATH.",
                        "project_type": project_type
                    }

                build_process = subprocess.run(
                    ["gradle", "build"],
                    cwd=self.project_dir,
                    capture_output=True,
                    text=True
                )

            if build_process.returncode != 0:
                return {
                    "success": False,
                    "message": f"Failed to build the project: {build_process.stderr}",
                    "project_type": project_type,
                    "stderr": build_process.stderr
                }

            # Find the JAR file
            jar_files = []
            if project_type == "java-maven":
                jar_dir = self.project_dir / "target"
            else:  # java-gradle
                jar_dir = self.project_dir / "build" / "libs"

            if jar_dir.exists():
                jar_files = list(jar_dir.glob("*.jar"))

            if not jar_files:
                return {
                    "success": False,
                    "message": "No JAR files found after building the project.",
                    "project_type": project_type
                }

            # Run the JAR file
            logger.info("Running the JAR file...")
            jar_file = str(jar_files[0])

            server_process = subprocess.Popen(
                ["java", "-jar", jar_file],
                cwd=self.project_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Wait a bit for the server to start
            time.sleep(5)

            # Check if the process is still running
            if server_process.poll() is not None:
                # Process has terminated
                stdout, stderr = server_process.communicate()
                return {
                    "success": False,
                    "message": f"Server process terminated: {stderr}",
                    "project_type": project_type,
                    "stdout": stdout,
                    "stderr": stderr
                }

            # Assume it's a Spring Boot application running on port 8080
            url = "http://localhost:8080"

            return {
                "success": True,
                "message": f"Java application started at {url}",
                "project_type": project_type,
                "url": url,
                "process_id": server_process.pid
            }
        except Exception as e:
            logger.error(f"Error deploying Java project: {e}")
            return {
                "success": False,
                "message": f"Error deploying Java project: {str(e)}",
                "project_type": project_type
            }

    def _deploy_rust(self) -> Dict:
        """
        Deploy a Rust project locally.

        Returns:
            Dictionary with deployment results
        """
        try:
            # Check if Rust is installed
            try:
                subprocess.run(["cargo", "--version"], check=True, capture_output=True)
            except Exception:
                return {
                    "success": False,
                    "message": "Rust is not installed or not in PATH.",
                    "project_type": "rust"
                }

            # Build the project
            logger.info("Building the project...")
            build_process = subprocess.run(
                ["cargo", "build", "--release"],
                cwd=self.project_dir,
                capture_output=True,
                text=True
            )

            if build_process.returncode != 0:
                return {
                    "success": False,
                    "message": f"Failed to build the project: {build_process.stderr}",
                    "project_type": "rust",
                    "stderr": build_process.stderr
                }

            # Run the project
            logger.info("Running the project...")
            server_process = subprocess.Popen(
                ["cargo", "run", "--release"],
                cwd=self.project_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Wait a bit for the server to start
            time.sleep(5)

            # Check if the process is still running
            if server_process.poll() is not None:
                # Process has terminated
                stdout, stderr = server_process.communicate()
                return {
                    "success": False,
                    "message": f"Process terminated: {stderr}",
                    "project_type": "rust",
                    "stdout": stdout,
                    "stderr": stderr
                }

            # Try to determine the URL by checking for common web frameworks
            url = None
            if self._check_dependency("actix-web") or self._check_dependency("rocket") or self._check_dependency("warp"):
                url = "http://localhost:8080"  # Common default port for Rust web servers

            return {
                "success": True,
                "message": f"Rust application started at {url}" if url else "Rust application is running",
                "project_type": "rust",
                "url": url,
                "process_id": server_process.pid
            }
        except Exception as e:
            logger.error(f"Error deploying Rust project: {e}")
            return {
                "success": False,
                "message": f"Error deploying Rust project: {str(e)}",
                "project_type": "rust"
            }

    def _deploy_go(self) -> Dict:
        """
        Deploy a Go project locally.

        Returns:
            Dictionary with deployment results
        """
        try:
            # Check if Go is installed
            try:
                subprocess.run(["go", "version"], check=True, capture_output=True)
            except Exception:
                return {
                    "success": False,
                    "message": "Go is not installed or not in PATH.",
                    "project_type": "go"
                }

            # Build the project
            logger.info("Building the project...")
            build_process = subprocess.run(
                ["go", "build", "-o", "app"],
                cwd=self.project_dir,
                capture_output=True,
                text=True
            )

            if build_process.returncode != 0:
                return {
                    "success": False,
                    "message": f"Failed to build the project: {build_process.stderr}",
                    "project_type": "go",
                    "stderr": build_process.stderr
                }

            # Run the project
            logger.info("Running the project...")
            app_path = self.project_dir / "app"
            if platform.system() == "Windows":
                app_path = self.project_dir / "app.exe"

            if not app_path.exists():
                return {
                    "success": False,
                    "message": "Built application not found.",
                    "project_type": "go"
                }

            server_process = subprocess.Popen(
                [str(app_path)],
                cwd=self.project_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Wait a bit for the server to start
            time.sleep(5)

            # Check if the process is still running
            if server_process.poll() is not None:
                # Process has terminated
                stdout, stderr = server_process.communicate()
                return {
                    "success": False,
                    "message": f"Process terminated: {stderr}",
                    "project_type": "go",
                    "stdout": stdout,
                    "stderr": stderr
                }

            # Try to determine if it's a web server by checking for common web frameworks
            url = None
            if self._check_file_content("*.go", "http.ListenAndServe") or self._check_file_content("*.go", "gin.New") or self._check_file_content("*.go", "echo.New"):
                url = "http://localhost:8080"  # Common default port for Go web servers

            return {
                "success": True,
                "message": f"Go application started at {url}" if url else "Go application is running",
                "project_type": "go",
                "url": url,
                "process_id": server_process.pid
            }
        except Exception as e:
            logger.error(f"Error deploying Go project: {e}")
            return {
                "success": False,
                "message": f"Error deploying Go project: {str(e)}",
                "project_type": "go"
            }
