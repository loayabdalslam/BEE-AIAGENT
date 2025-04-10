"""
Package handler module for the AI Code Agent.
Handles creation and management of package files for different project types.
"""
import logging
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Union

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PackageHandler:
    """
    Handles package files for different project types.
    """
    
    def __init__(self, project_dir: Union[str, Path]):
        """
        Initialize the package handler.
        
        Args:
            project_dir: Path to the project directory
        """
        self.project_dir = Path(project_dir)
        
        if not self.project_dir.exists():
            self.project_dir.mkdir(parents=True, exist_ok=True)
    
    def ensure_package_files(self, structure: Dict) -> Dict:
        """
        Ensure that appropriate package files are created based on project type.
        
        Args:
            structure: Dictionary containing the project structure
            
        Returns:
            Dictionary with results
        """
        results = {
            "created_files": [],
            "errors": []
        }
        
        try:
            # Detect project type from structure
            project_type = structure.get("project_type", "").lower()
            technologies = structure.get("technologies", [])
            files = [Path(file_info.get("path", "")) for file_info in structure.get("files", [])]
            file_paths = [str(f) for f in files]
            
            # Check if package files already exist
            has_package_json = any("package.json" in str(f) for f in files) or (self.project_dir / "package.json").exists()
            has_requirements = any("requirements.txt" in str(f) for f in files) or (self.project_dir / "requirements.txt").exists()
            has_gemfile = any("Gemfile" in str(f) for f in files) or (self.project_dir / "Gemfile").exists()
            has_cargo_toml = any("Cargo.toml" in str(f) for f in files) or (self.project_dir / "Cargo.toml").exists()
            has_pom_xml = any("pom.xml" in str(f) for f in files) or (self.project_dir / "pom.xml").exists()
            has_build_gradle = any("build.gradle" in str(f) for f in files) or (self.project_dir / "build.gradle").exists()
            
            # Detect JavaScript/Node.js project
            is_js_project = project_type in ["javascript", "typescript", "node", "nodejs", "react", "vue", "angular", "nextjs", "nuxt"] or \
                           any(tech.lower() in ["javascript", "typescript", "node", "nodejs", "react", "vue", "angular", "nextjs", "nuxt"] 
                               for tech in technologies) or \
                           any(f.suffix in [".js", ".ts", ".jsx", ".tsx"] for f in files)
            
            # Detect Python project
            is_python_project = project_type in ["python", "flask", "django", "fastapi"] or \
                              any(tech.lower() in ["python", "flask", "django", "fastapi"] 
                                  for tech in technologies) or \
                              any(f.suffix == ".py" for f in files)
            
            # Detect Ruby project
            is_ruby_project = project_type in ["ruby", "rails"] or \
                             any(tech.lower() in ["ruby", "rails"] 
                                 for tech in technologies) or \
                             any(f.suffix == ".rb" for f in files)
            
            # Detect Rust project
            is_rust_project = project_type in ["rust"] or \
                             any(tech.lower() == "rust" 
                                 for tech in technologies) or \
                             any(f.suffix == ".rs" for f in files)
            
            # Detect Java project
            is_java_project = project_type in ["java", "spring", "springboot"] or \
                             any(tech.lower() in ["java", "spring", "springboot"] 
                                 for tech in technologies) or \
                             any(f.suffix == ".java" for f in files)
            
            # Create package.json if needed
            if is_js_project and not has_package_json:
                logger.info("Creating package.json for JavaScript/Node.js project")
                package_json = self._generate_package_json(structure)
                package_json_path = self.project_dir / "package.json"
                with open(package_json_path, "w", encoding='utf-8') as f:
                    f.write(package_json)
                results["created_files"].append(str(package_json_path))
            
            # Create requirements.txt if needed
            if is_python_project and not has_requirements:
                logger.info("Creating requirements.txt for Python project")
                requirements = self._generate_requirements_txt(structure)
                requirements_path = self.project_dir / "requirements.txt"
                with open(requirements_path, "w", encoding='utf-8') as f:
                    f.write(requirements)
                results["created_files"].append(str(requirements_path))
            
            # Create Gemfile if needed
            if is_ruby_project and not has_gemfile:
                logger.info("Creating Gemfile for Ruby project")
                gemfile = self._generate_gemfile(structure)
                gemfile_path = self.project_dir / "Gemfile"
                with open(gemfile_path, "w", encoding='utf-8') as f:
                    f.write(gemfile)
                results["created_files"].append(str(gemfile_path))
            
            # Create Cargo.toml if needed
            if is_rust_project and not has_cargo_toml:
                logger.info("Creating Cargo.toml for Rust project")
                cargo_toml = self._generate_cargo_toml(structure)
                cargo_toml_path = self.project_dir / "Cargo.toml"
                with open(cargo_toml_path, "w", encoding='utf-8') as f:
                    f.write(cargo_toml)
                results["created_files"].append(str(cargo_toml_path))
            
            # Create pom.xml or build.gradle if needed
            if is_java_project:
                if not has_pom_xml and not has_build_gradle:
                    # Default to Maven (pom.xml)
                    logger.info("Creating pom.xml for Java project")
                    pom_xml = self._generate_pom_xml(structure)
                    pom_xml_path = self.project_dir / "pom.xml"
                    with open(pom_xml_path, "w", encoding='utf-8') as f:
                        f.write(pom_xml)
                    results["created_files"].append(str(pom_xml_path))
            
            return results
        except Exception as e:
            logger.error(f"Error ensuring package files: {e}")
            results["errors"].append(str(e))
            return results
    
    def _generate_package_json(self, structure: Dict) -> str:
        """
        Generate a package.json file based on project structure.
        
        Args:
            structure: Dictionary containing the project structure
            
        Returns:
            Content for package.json file
        """
        project_name = structure.get("project_name", "my-project").lower().replace(" ", "-")
        description = structure.get("description", "A JavaScript project")
        technologies = structure.get("technologies", [])
        
        # Detect framework
        is_react = any(tech.lower() == "react" for tech in technologies)
        is_vue = any(tech.lower() == "vue" for tech in technologies)
        is_angular = any(tech.lower() == "angular" for tech in technologies)
        is_nextjs = any(tech.lower() == "nextjs" for tech in technologies)
        is_express = any(tech.lower() == "express" for tech in technologies)
        
        # Generate dependencies based on detected frameworks
        dependencies = {}
        dev_dependencies = {}
        scripts = {"start": "node index.js"}
        
        if is_react:
            dependencies["react"] = "^18.2.0"
            dependencies["react-dom"] = "^18.2.0"
            dev_dependencies["vite"] = "^4.4.0"
            scripts = {"dev": "vite", "build": "vite build", "preview": "vite preview"}
        
        if is_vue:
            dependencies["vue"] = "^3.3.4"
            dev_dependencies["@vitejs/plugin-vue"] = "^4.2.3"
            dev_dependencies["vite"] = "^4.4.0"
            scripts = {"dev": "vite", "build": "vite build", "preview": "vite preview"}
        
        if is_angular:
            dependencies["@angular/core"] = "^16.1.0"
            dependencies["@angular/common"] = "^16.1.0"
            dependencies["@angular/platform-browser"] = "^16.1.0"
            dependencies["rxjs"] = "^7.8.1"
            dev_dependencies["@angular/cli"] = "^16.1.0"
            dev_dependencies["typescript"] = "~5.1.3"
            scripts = {"ng": "ng", "start": "ng serve", "build": "ng build"}
        
        if is_nextjs:
            dependencies["next"] = "^13.4.7"
            dependencies["react"] = "^18.2.0"
            dependencies["react-dom"] = "^18.2.0"
            scripts = {"dev": "next dev", "build": "next build", "start": "next start"}
        
        if is_express:
            dependencies["express"] = "^4.18.2"
            dependencies["body-parser"] = "^1.20.2"
            scripts = {"start": "node server.js", "dev": "nodemon server.js"}
            dev_dependencies["nodemon"] = "^2.0.22"
        
        # Add some common dependencies if none detected
        if not dependencies:
            dependencies["lodash"] = "^4.17.21"
        
        package_json = {
            "name": project_name,
            "version": "1.0.0",
            "description": description,
            "main": "index.js",
            "scripts": scripts,
            "keywords": [],
            "author": "",
            "license": "ISC",
            "dependencies": dependencies,
            "devDependencies": dev_dependencies
        }
        
        return json.dumps(package_json, indent=2)
    
    def _generate_requirements_txt(self, structure: Dict) -> str:
        """
        Generate a requirements.txt file based on project structure.
        
        Args:
            structure: Dictionary containing the project structure
            
        Returns:
            Content for requirements.txt file
        """
        technologies = structure.get("technologies", [])
        
        # Detect framework
        is_flask = any(tech.lower() == "flask" for tech in technologies)
        is_django = any(tech.lower() == "django" for tech in technologies)
        is_fastapi = any(tech.lower() == "fastapi" for tech in technologies)
        
        requirements = []
        
        # Add framework-specific dependencies
        if is_flask:
            requirements.extend(["Flask>=2.3.2", "Werkzeug>=2.3.6", "Jinja2>=3.1.2"])
        
        if is_django:
            requirements.extend(["Django>=4.2.3", "djangorestframework>=3.14.0"])
        
        if is_fastapi:
            requirements.extend(["fastapi>=0.100.0", "uvicorn>=0.22.0", "pydantic>=2.0.3"])
        
        # Add some common dependencies if none detected
        if not requirements:
            requirements.extend(["requests>=2.31.0", "python-dotenv>=1.0.0"])
        
        return "\n".join(requirements)
    
    def _generate_gemfile(self, structure: Dict) -> str:
        """
        Generate a Gemfile based on project structure.
        
        Args:
            structure: Dictionary containing the project structure
            
        Returns:
            Content for Gemfile
        """
        technologies = structure.get("technologies", [])
        
        # Detect framework
        is_rails = any(tech.lower() == "rails" for tech in technologies)
        
        gemfile_content = ["source 'https://rubygems.org'"]
        
        if is_rails:
            gemfile_content.extend([
                "\n# Rails framework",
                "gem 'rails', '~> 7.0.6'",
                "gem 'puma', '~> 6.3'",
                "gem 'sqlite3', '~> 1.6'"
            ])
        else:
            gemfile_content.extend([
                "\n# Basic gems",
                "gem 'sinatra', '~> 3.0'",
                "gem 'rake', '~> 13.0'"
            ])
        
        return "\n".join(gemfile_content)
    
    def _generate_cargo_toml(self, structure: Dict) -> str:
        """
        Generate a Cargo.toml file based on project structure.
        
        Args:
            structure: Dictionary containing the project structure
            
        Returns:
            Content for Cargo.toml file
        """
        project_name = structure.get("project_name", "my-project").lower().replace(" ", "-")
        description = structure.get("description", "A Rust project")
        
        cargo_toml = f"""[package]
name = "{project_name}"
version = "0.1.0"
edition = "2021"
description = "{description}"

[dependencies]
serde = {{ version = "1.0", features = ["derive"] }}
serde_json = "1.0"

[dev-dependencies]
assert_cmd = "2.0"
predicates = "3.0"
"""
        
        return cargo_toml
    
    def _generate_pom_xml(self, structure: Dict) -> str:
        """
        Generate a pom.xml file based on project structure.
        
        Args:
            structure: Dictionary containing the project structure
            
        Returns:
            Content for pom.xml file
        """
        project_name = structure.get("project_name", "my-project").lower().replace(" ", "-")
        description = structure.get("description", "A Java project")
        
        pom_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0" 
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    
    <groupId>com.example</groupId>
    <artifactId>{project_name}</artifactId>
    <version>1.0-SNAPSHOT</version>
    <packaging>jar</packaging>
    
    <name>{project_name}</name>
    <description>{description}</description>
    
    <properties>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
        <maven.compiler.source>17</maven.compiler.source>
        <maven.compiler.target>17</maven.compiler.target>
    </properties>
    
    <dependencies>
        <dependency>
            <groupId>org.junit.jupiter</groupId>
            <artifactId>junit-jupiter</artifactId>
            <version>5.9.3</version>
            <scope>test</scope>
        </dependency>
    </dependencies>
    
    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <version>3.11.0</version>
            </plugin>
        </plugins>
    </build>
</project>
"""
        
        return pom_xml
