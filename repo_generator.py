import os
import logging
import shutil

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

    def create_repo_folder(self, project_name):
        """Creates a new folder for the repository"""
        self.repo_folder = os.path.join(os.getcwd(), project_name)
        os.makedirs(self.repo_folder, exist_ok=True)
        logger.info(f"Created new repository folder: {self.repo_folder}")

    def create_structure(self, structure, base_path=None):
        """Creates folder structure and files."""
        base_path = base_path or self.repo_folder
        for folder, contents in structure.items():
            folder_path = os.path.join(base_path, folder)
            os.makedirs(folder_path, exist_ok=True)
            
            for file_info in contents.get("files", []):
                file_path = os.path.join(folder_path, file_info['name'])
                with open(file_path, 'w') as f:
                    f.write(f"# TODO: Implement {file_info['name']}\n")
                    f.write(f"# Type: {file_info['type']}\n")
                    f.write(f"# Description: {file_info['description']}\n")
                logger.info(f"Created file: {file_path}")
            
            self.create_structure(contents.get("subfolders", {}), folder_path)

    def create_readme(self, requirements):
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

    def create_gitignore(self, tech_stack):
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

    def get_current_structure(self, base_path=None):
        """Recursively gets the current folder structure."""
        base_path = base_path or self.repo_folder
        structure = {}
        for item in os.listdir(base_path):
            item_path = os.path.join(base_path, item)
            if os.path.isdir(item_path):
                structure[item] = {
                    "subfolders": self.get_current_structure(item_path),
                    "files": []
                }
            else:
                if "files" not in structure:
                    structure["files"] = []
                structure["files"].append({"name": item, "type": "file", "description": "Auto-generated file"})
        return structure

    def update_structure(self, current_structure, updated_structure, base_path=None):
        """Updates the existing structure based on the updated structure."""
        base_path = base_path or self.repo_folder
        for folder, contents in updated_structure.items():
            folder_path = os.path.join(base_path, folder)
            if folder not in current_structure:
                os.makedirs(folder_path, exist_ok=True)
                logger.info(f"Created new folder: {folder_path}")
            
            for file_info in contents.get("files", []):
                file_path = os.path.join(folder_path, file_info['name'])
                if not os.path.exists(file_path):
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(f"# TODO: Implement {file_info['name']}\n")
                        f.write(f"# Type: {file_info['type']}\n")
                        f.write(f"# Description: {file_info['description']}\n")
                    logger.info(f"Created new file: {file_path}")
            
            self.update_structure(
                current_structure.get(folder, {}).get("subfolders", {}),
                contents.get("subfolders", {}),
                folder_path
            )
        
        # Remove folders and files not in the updated structure
        for folder in current_structure:
            if folder not in updated_structure:
                folder_path = os.path.join(base_path, folder)
                shutil.rmtree(folder_path)
                logger.info(f"Removed folder: {folder_path}")

    def update_readme(self, requirements):
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

    def update_gitignore(self, tech_stack):
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

    def _get_file_extension(self, language):
        extensions = {
            'python': '.py',
            'javascript': '.js',
            'react': '.jsx',
            'react native': '.js',
            'html': '.html',
            'css': '.css',
            'ruby': '.rb',
            'java': '.java'
        }
        return extensions.get(language, '.txt')
