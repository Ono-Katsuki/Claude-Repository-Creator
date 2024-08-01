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

logger = logging.getLogger(__name__)

class ClaudeRepoCreator:
    def __init__(self, debug_mode=False):
        self.config = self.load_config()
        self.claude_client = None
        self.repo_generator = RepoGenerator()
        self.projects_folder = os.path.join(os.getcwd(), "claude_projects")
        self.current_project_folder = None
        self.cache_folder = os.path.join(self.projects_folder, "information_management", "cache")
        self.create_cache_structure()
        self.cache_manager = None
        self.vc_system = VersionControlFactory.create(self.config['version_control'])
        self.debug_mode = debug_mode
        if self.debug_mode:
            logging.getLogger().setLevel(logging.DEBUG)
        self.requirements_generator = RequirementsGenerator(self.config['api_key'])
        self.repository_creator = RepositoryCreator(self.config['api_key'])

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

    def create_cache_structure(self):
        os.makedirs(self.cache_folder, exist_ok=True)
        global_cache_path = os.path.join(self.cache_folder, 'global_cache.json')
        if os.path.exists(global_cache_path):
            with open(global_cache_path, 'r') as f:
                global_cache_data = json.load(f)
            os.remove(global_cache_path)
            logger.info(f"Removed global cache file: {global_cache_path}")
            return global_cache_data
        return {}

    def create_project_folder(self, project_name):
        os.makedirs(self.projects_folder, exist_ok=True)
        self.current_project_folder = os.path.join(self.projects_folder, project_name)
        os.makedirs(self.current_project_folder, exist_ok=True)
        
        project_cache_path = os.path.join(self.cache_folder, f'{project_name}_cache.json')
        if not os.path.exists(project_cache_path):
            global_cache_data = self.create_cache_structure()
            with open(project_cache_path, 'w') as f:
                json.dump(global_cache_data, f)
        
        self.cache_manager = CacheManager(project_cache_path)
        logger.info(f"Created project folder: {self.current_project_folder}")
        logger.info(f"Using project cache: {project_cache_path}")

    async def run(self):
        temp_project_name = "temp_project"
        temp_cache_path = os.path.join(self.cache_folder, f'{temp_project_name}_cache.json')
        try:
            project_description = input("Enter the project description: ")
            
            # Ensure cache folder exists
            os.makedirs(self.cache_folder, exist_ok=True)
            
            # Create temporary cache file
            with open(temp_cache_path, 'w') as f:
                json.dump({}, f)
            
            self.cache_manager = CacheManager(temp_cache_path)
            
            requirements = await self.requirements_generator.generate_requirements(project_description)
            
            # Save requirements to cache
            self.cache_manager.set("requirements", requirements)
            
            new_project_name = requirements['project_name']
            new_cache_path = os.path.join(self.cache_folder, f'{new_project_name}_cache.json')
            
            # Ensure all cache data is written to disk
            self.cache_manager.save_cache()
            
            # Copy temp cache file to project-specific cache file
            shutil.copy2(temp_cache_path, new_cache_path)
            
            # Remove temp cache file
            os.remove(temp_cache_path)
            
            self.cache_manager = CacheManager(new_cache_path)
            
            self.create_project_folder(new_project_name)
            
            update_existing = input("Do you want to update an existing repository? (y/n): ").lower() == 'y'
            await self.repository_creator.create_repository(requirements, update_existing, self.current_project_folder, self.repo_generator, self.vc_system)
            
            print(f"Repository for project: {new_project_name} has been {'updated' if update_existing else 'created'} in folder: {self.repo_generator.repo_folder}")
        except Exception as e:
            logger.error(f"An error occurred during program execution: {str(e)}")
            if os.path.exists(temp_cache_path):
                os.remove(temp_cache_path)
            if self.current_project_folder and os.path.exists(self.current_project_folder):
                shutil.rmtree(self.current_project_folder)
        finally:
            await self.__aexit__(None, None, None)
