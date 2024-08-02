import os
import json
import logging
import shutil
from config_manager import ConfigManager
from cache_manager import CacheManager
from version_control import VersionControlFactory
from repo_generator import RepoGenerator
from requirements_generator import RequirementsGenerator
from repository_creator import RepositoryCreator
from markdown_generator import MarkdownGenerator

logger = logging.getLogger(__name__)

class ClaudeRepoCreator:
    def __init__(self, debug_mode=False):
        self.config = self.load_config()
        self.claude_client = None
        self.repo_generator = RepoGenerator()
        self.projects_folder = os.path.join(os.getcwd(), "claude_projects")
        self.current_project_folder = None
        self.cache_folder = os.path.join(self.projects_folder, "information_management", "cache")
        self.markdown_folder = os.path.join(self.projects_folder, "information_management", "markdown")
        self.create_folder_structure()
        self.vc_system = VersionControlFactory.create(self.config['version_control'])
        self.debug_mode = debug_mode
        if self.debug_mode:
            logging.getLogger().setLevel(logging.DEBUG)
        self.requirements_generator = RequirementsGenerator(self.config['api_key'])
        self.repository_creator = RepositoryCreator(self.config['api_key'])
        self.markdown_generator = MarkdownGenerator()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.claude_client:
            await self.claude_client.close()

    def load_config(self):
        config_manager = ConfigManager()
        config = config_manager.load_config()
        if not config.get('api_key'):
            config['api_key'] = self.prompt_for_api_key()
            config_manager.save_config(config)
        return config

    def prompt_for_api_key(self):
        while True:
            api_key = input("Please enter your Claude API key: ").strip()
            if api_key:
                confirm = input("Is this correct? (y/n): ").lower()
                if confirm == 'y':
                    return api_key
            else:
                print("API key cannot be empty. Please try again.")

    def create_folder_structure(self):
        os.makedirs(self.cache_folder, exist_ok=True)
        os.makedirs(self.markdown_folder, exist_ok=True)

    def create_project_folder(self, project_name):
        os.makedirs(self.projects_folder, exist_ok=True)
        self.current_project_folder = os.path.join(self.projects_folder, project_name)
        os.makedirs(self.current_project_folder, exist_ok=True)
        logger.info(f"Created project folder: {self.current_project_folder}")

    def save_requirements(self, requirements, file_path):
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(requirements, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved requirements to: {file_path}")

    def create_project_summary(self, requirements):
        summary_filename = f"{requirements['project_name']}_summary.md"
        summary_path = os.path.join(self.markdown_folder, summary_filename)
        self.markdown_generator.create_project_summary(requirements, self.repo_generator.repo_folder, summary_path)
        logger.info(f"Created project summary: {summary_path}")

    async def run(self):
        try:
            project_description = input("Enter the project description: ")
            
            # Ensure cache folder exists
            os.makedirs(self.cache_folder, exist_ok=True)
            
            requirements = await self.requirements_generator.generate_requirements(project_description)
            
            new_project_name = requirements['project_name']
            new_cache_path = os.path.join(self.cache_folder, f'{new_project_name}_requirements.json')
            
            # Save requirements directly to JSON file
            self.save_requirements(requirements, new_cache_path)
            
            self.create_project_folder(new_project_name)
            
            update_existing = input("Do you want to update an existing repository? (y/n): ").lower() == 'y'
            await self.repository_creator.create_repository(requirements, update_existing, self.current_project_folder, self.repo_generator, self.vc_system)
            
            print(f"Repository for project: {new_project_name} has been {'updated' if update_existing else 'created'} in folder: {self.repo_generator.repo_folder}")
            
            # Create and save project summary with full code
            self.create_project_summary(requirements)
            
            print(f"Project summary with full code has been created in the markdown folder.")
        except Exception as e:
            logger.error(f"An error occurred during program execution: {str(e)}")
            if self.current_project_folder and os.path.exists(self.current_project_folder):
                shutil.rmtree(self.current_project_folder)
        finally:
            await self.__aexit__(None, None, None)
