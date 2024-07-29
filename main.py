import os
import sys
import json
import logging
from tkinter import Tk, scrolledtext, Button, Label
from claude_api import ClaudeAPI
from repo_generator import RepoGenerator
from config_manager import ConfigManager
from cache_manager import CacheManager
from version_control import VersionControlFactory
from code_generator import CodeGenerator
from code_tester import CodeTester

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ClaudeRepoCreator:
    def __init__(self):
        self.config = self.load_config()
        self.claude_api = ClaudeAPI(self.config['api_key'])
        self.repo_generator = RepoGenerator()
        self.cache_manager = CacheManager()
        self.vc_system = VersionControlFactory.create(self.config['version_control'])

    def load_config(self):
        config_manager = ConfigManager()
        config = config_manager.load_config()
        if not config.get('api_key'):
            raise ValueError("API key is not set in the configuration file.")
        return config

    def generate_requirements(self, project_description):
        cache_key = f"requirements_{hash(project_description)}"
        cached_requirements = self.cache_manager.get(cache_key)
        if cached_requirements:
            return cached_requirements

        prompt = self.create_requirements_prompt(project_description)
        try:
            response = self.claude_api.generate_response(prompt)
            requirements = json.loads(response)
            self.validate_requirements(requirements)
            self.cache_manager.set(cache_key, requirements)
            return requirements
        except json.JSONDecodeError:
            logger.error("Failed to parse Claude's response as JSON.")
            raise ValueError("Invalid response format from Claude API.")
        except KeyError as e:
            logger.error(f"Missing required key in requirements: {str(e)}")
            raise ValueError("Incomplete requirements generated.")
        except Exception as e:
            logger.error(f"Error generating requirements: {str(e)}")
            raise

    def create_requirements_prompt(self, project_description):
        return f"""
        Based on the following project description, create a detailed requirements definition:

        {project_description}

        Provide the requirements in the following JSON format:
        {{
            "project_name": "string",
            "description": "string",
            "features": [
                {{
                    "name": "string",
                    "description": "string",
                    "acceptance_criteria": ["string"]
                }}
            ],
            "tech_stack": ["string"],
            "folder_structure": {{
                "folder_name": {{
                    "subfolders": {{}},
                    "files": ["string"]
                }}
            }}
        }}
        """

    def validate_requirements(self, requirements):
        required_keys = ["project_name", "description", "features", "tech_stack", "folder_structure"]
        for key in required_keys:
            if key not in requirements:
                raise KeyError(f"Missing required key: {key}")

    def create_repository(self, requirements, update_existing=False):
        try:
            if update_existing:
                self.update_existing_repository(requirements)
            else:
                self.repo_generator.create_structure(requirements['folder_structure'])
                self.repo_generator.create_readme(requirements)
                self.repo_generator.create_gitignore(requirements['tech_stack'])
            
            for feature in requirements['features']:
                self.create_feature_files(feature, requirements['tech_stack'])

            self.vc_system.initialize(requirements['project_name'])
        except Exception as e:
            logger.error(f"Error creating repository: {str(e)}")
            raise

    def update_existing_repository(self, requirements):
        try:
            current_structure = self.repo_generator.get_current_structure()
            updated_structure = requirements['folder_structure']
            self.repo_generator.update_structure(current_structure, updated_structure)
            self.repo_generator.update_readme(requirements)
            self.repo_generator.update_gitignore(requirements['tech_stack'])
        except Exception as e:
            logger.error(f"Error updating existing repository: {str(e)}")
            raise

    def create_feature_files(self, feature, tech_stack):
        try:
            code_generator = CodeGenerator(self.claude_api, tech_stack)
            feature_code = code_generator.generate_feature_code(feature)
            
            code_tester = CodeTester(tech_stack)
            test_result = code_tester.test_code(feature_code)
            
            if test_result['success']:
                edited_code = self.show_code_editor(feature['name'], feature_code)
                self.repo_generator.create_feature_files(feature['name'], edited_code)
            else:
                logger.error(f"Generated code contains errors: {test_result['message']}")
                self.show_error_message(test_result['message'])
        except Exception as e:
            logger.error(f"Error creating feature files: {str(e)}")
            raise

    def show_code_editor(self, feature_name, code):
        root = Tk()
        root.title(f"Code Editor - {feature_name}")
        
        editor = scrolledtext.ScrolledText(root, width=100, height=30)
        editor.insert("1.0", code)
        editor.pack()

        edited_code = [code]

        def save_and_exit():
            edited_code[0] = editor.get("1.0", "end-1c")
            root.quit()

        save_button = Button(root, text="Save and Close", command=save_and_exit)
        save_button.pack()

        root.mainloop()
        root.destroy()

        return edited_code[0]

    def show_error_message(self, message):
        root = Tk()
        root.title("Error")
        
        label = Label(root, text=message)
        label.pack(padx=20, pady=20)

        ok_button = Button(root, text="OK", command=root.destroy)
        ok_button.pack(pady=10)

        root.mainloop()

    def run(self):
        try:
            project_description = input("Enter project description: ")
            requirements = self.generate_requirements(project_description)
            
            update_existing = input("Update existing repository? (y/n): ").lower() == 'y'
            self.create_repository(requirements, update_existing)
            
            print(f"Repository for project: {requirements['project_name']} has been {'updated' if update_existing else 'created'} successfully.")
        except Exception as e:
            logger.error(f"An error occurred during program execution: {str(e)}")
            sys.exit(1)

if __name__ == "__main__":
    creator = ClaudeRepoCreator()
    creator.run()
