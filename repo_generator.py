import os
import logging
import shutil
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class RepoGenerator:
    def __init__(self):
        self.gitignore_templates = {
            "python": [
                "*.pyc",
                "__pycache__/",
                "venv/",
                "*.egg-info/",
                "dist/",
                "build/",
            ],
            "javascript": [
                "node_modules/",
                "npm-debug.log",
                "yarn-error.log",
                "dist/",
                "*.log",
            ],
            "java": [
                "*.class",
                "*.jar",
                "target/",
                ".gradle/",
                "build/",
            ],
            "react": [
                "node_modules/",
                "build/",
                ".env",
                "*.log",
            ],
            "react native": [
                "node_modules/",
                ".expo/",
                "npm-debug.*",
                "*.jks",
                "*.p8",
                "*.p12",
                "*.key",
                "*.mobileprovision",
                "*.orig.*",
                "web-build/",
            ],
            "html": [
                "*.log",
                "*.tmp",
            ],
            "css": [
                "*.map",
                "*.css.map",
            ],
            "ruby": [
                "*.gem",
                "*.rbc",
                "/.config",
                "/coverage/",
                "/InstalledFiles",
                "/pkg/",
                "/spec/reports/",
                "/spec/examples.txt",
                "/test/tmp/",
                "/test/version_tmp/",
                "/tmp/",
                "/.yardoc/",
                "_yardoc/",
                "/doc/",
                "/rdoc/",
            ],
        }
        self.repo_folder = None

    def _normalize_language(self, language: str) -> str:
        """Normalizes the language name."""
        language = language.lower()
        if language in ['react', 'react.js', 'reactjs']:
            return 'react'
        if language in ['react native', 'react-native', 'reactnative']:
            return 'react native'
        return language

    def create_repo_folder(self, project_name: str):
        """Creates a new folder for the repository"""
        self.repo_folder = os.path.join(os.getcwd(), project_name)
        os.makedirs(self.repo_folder, exist_ok=True)
        logger.info(f"Created new repository folder: {self.repo_folder}")

    def create_structure(self, folder_structure: Dict[str, Any], base_path: str = None):
        """Creates folder structure and files based on the Requirements model."""
        base_path = base_path or self.repo_folder
        
        for file in folder_structure.get('files', []):
            file_path = os.path.join(base_path, file['name'])
            with open(file_path, 'w') as f:
                content = file.get('content', {})
                f.write(f"# TODO: Implement {file['name']}\n")
                f.write(f"# Description: {content.get('description', 'No description provided')}\n")
                
                file_type = content.get('type')
                if file_type == 'class':
                    f.write("\nclass ClassName:\n")
                    for prop in content.get('properties', []):
                        f.write(f"    {prop} = None\n")
                    for method in content.get('methods', []):
                        params = ", ".join(method.get('params', []))
                        f.write(f"    def {method['name']}({params}):\n")
                        f.write(f"        # TODO: Implement {method['name']}\n")
                        f.write(f"        # {method.get('description', 'No description provided')}\n")
                        f.write(f"        pass\n\n")
                elif file_type == 'function':
                    for method in content.get('methods', []):
                        params = ", ".join(method.get('params', []))
                        f.write(f"\ndef {method['name']}({params}):\n")
                        f.write(f"    # TODO: Implement {method['name']}\n")
                        f.write(f"    # {method.get('description', 'No description provided')}\n")
                        f.write("    pass\n")
                elif file_type == 'component':
                    f.write("\nclass Component:\n")
                    f.write("    def __init__(self):\n")
                    for prop in content.get('properties', []):
                        f.write(f"        self.{prop} = None\n")
                    for method in content.get('methods', []):
                        params = ", ".join(method.get('params', []))
                        f.write(f"    def {method['name']}({params}):\n")
                        f.write(f"        # TODO: Implement {method['name']}\n")
                        f.write(f"        # {method.get('description', 'No description provided')}\n")
                        f.write("        pass\n")
                else:
                    f.write(f"# Unknown file type: {file_type}\n")
                
            logger.info(f"Created file: {file_path}")
        
        for subfolder in folder_structure.get('subfolders', []):
            subfolder_path = os.path.join(base_path, subfolder['name'])
            os.makedirs(subfolder_path, exist_ok=True)
            self.create_structure(subfolder, subfolder_path)

    def create_readme(self, requirements: Dict[str, Any]):
        """Creates a README.md file with project information."""
        try:
            readme_path = os.path.join(self.repo_folder, "README.md")
            with open(readme_path, "w", encoding='utf-8') as f:
                f.write(f"# {requirements['project_name']}\n\n")
                f.write(f"{requirements['description']}\n\n")
                f.write("## Features\n\n")
                for feature in requirements['features']:
                    f.write(f"### {feature['name']}\n")
                    f.write(f"{feature['description']}\n\n")
                    f.write("Acceptance Criteria:\n")
                    for criteria in feature['acceptance_criteria']:
                        f.write(f"- {criteria}\n")
                    f.write("\n")
            logger.info("README.md created successfully.")
        except IOError as e:
            logger.error(f"Error occurred while creating README.md: {str(e)}")

    def create_gitignore(self, tech_stack: List[str]):
        """Creates a .gitignore file based on the technology stack."""
        try:
            gitignore_path = os.path.join(self.repo_folder, ".gitignore")
            with open(gitignore_path, "w", encoding='utf-8') as f:
                for tech in tech_stack:
                    tech_lower = self._normalize_language(tech)
                    if tech_lower in self.gitignore_templates:
                        f.write(f"# {tech}-specific ignore patterns\n")
                        for pattern in self.gitignore_templates[tech_lower]:
                            f.write(f"{pattern}\n")
                        f.write("\n")
                f.write("# General ignore patterns\n")
                f.write(".DS_Store\n")
                f.write(".idea/\n")
                f.write(".vscode/\n")
            logger.info(".gitignore created successfully.")
        except IOError as e:
            logger.error(f"Error occurred while creating .gitignore: {str(e)}")

    def get_current_structure(self, base_path: str = None) -> Dict[str, Any]:
        """Recursively gets the current folder structure."""
        base_path = base_path or self.repo_folder
        structure = {"files": [], "subfolders": []}
        for item in os.listdir(base_path):
            item_path = os.path.join(base_path, item)
            if os.path.isdir(item_path):
                subfolder = {
                    "name": item,
                    **self.get_current_structure(item_path)
                }
                structure["subfolders"].append(subfolder)
            else:
                structure["files"].append({
                    "name": item,
                    "content": {
                        "type": "file",
                        "description": "Auto-generated file"
                    }
                })
        return structure

    def update_structure(self, current_structure: Dict[str, Any], updated_structure: Dict[str, Any], base_path: str = None):
        """Updates the existing structure based on the updated structure."""
        base_path = base_path or self.repo_folder
        
        # Update files
        current_files = {f['name']: f for f in current_structure.get('files', [])}
        for file in updated_structure.get('files', []):
            if file['name'] not in current_files:
                self.create_structure({"files": [file]}, base_path)
        
        # Remove files not in the updated structure
        for file in current_files.values():
            if file['name'] not in [f['name'] for f in updated_structure.get('files', [])]:
                os.remove(os.path.join(base_path, file['name']))
                logger.info(f"Removed file: {file['name']}")
        
        # Update subfolders
        current_subfolders = {f['name']: f for f in current_structure.get('subfolders', [])}
        for subfolder in updated_structure.get('subfolders', []):
            if subfolder['name'] in current_subfolders:
                self.update_structure(
                    current_subfolders[subfolder['name']],
                    subfolder,
                    os.path.join(base_path, subfolder['name'])
                )
            else:
                os.makedirs(os.path.join(base_path, subfolder['name']), exist_ok=True)
                self.create_structure(subfolder, os.path.join(base_path, subfolder['name']))
        
        # Remove subfolders not in the updated structure
        for subfolder in current_subfolders.values():
            if subfolder['name'] not in [f['name'] for f in updated_structure.get('subfolders', [])]:
                shutil.rmtree(os.path.join(base_path, subfolder['name']))
                logger.info(f"Removed folder: {subfolder['name']}")

    def update_readme(self, requirements: Dict[str, Any]):
        """Updates the existing README.md file."""
        try:
            readme_path = os.path.join(self.repo_folder, "README.md")
            if not os.path.exists(readme_path):
                return self.create_readme(requirements)
            
            with open(readme_path, "r+", encoding='utf-8') as f:
                content = f.read()
                f.seek(0)
                f.write(f"# {requirements['project_name']}\n\n")
                f.write(f"{requirements['description']}\n\n")
                f.write("## Features\n\n")
                for feature in requirements['features']:
                    f.write(f"### {feature['name']}\n")
                    f.write(f"{feature['description']}\n\n")
                    f.write("Acceptance Criteria:\n")
                    for criteria in feature['acceptance_criteria']:
                        f.write(f"- {criteria}\n")
                    f.write("\n")
                f.write(content.split("## Features")[1] if "## Features" in content else "")
                f.truncate()
            logger.info("README.md updated successfully.")
        except IOError as e:
            logger.error(f"Error occurred while updating README.md: {str(e)}")

    def update_gitignore(self, tech_stack: List[str]):
        """Updates the existing .gitignore file."""
        try:
            gitignore_path = os.path.join(self.repo_folder, ".gitignore")
            if not os.path.exists(gitignore_path):
                return self.create_gitignore(tech_stack)
            
            with open(gitignore_path, "r+", encoding='utf-8') as f:
                content = f.read()
                f.seek(0)
                for tech in tech_stack:
                    tech_lower = self._normalize_language(tech)
                    if tech_lower in self.gitignore_templates:
                        f.write(f"# {tech}-specific ignore patterns\n")
                        for pattern in self.gitignore_templates[tech_lower]:
                            f.write(f"{pattern}\n")
                        f.write("\n")
                f.write("# General ignore patterns\n")
                f.write(".DS_Store\n")
                f.write(".idea/\n")
                f.write(".vscode/\n")
                f.write(content.split("# General ignore patterns")[1] if "# General ignore patterns" in content else "")
                f.truncate()
            logger.info(".gitignore updated successfully.")
        except IOError as e:
            logger.error(f"Error occurred while updating .gitignore: {str(e)}")
