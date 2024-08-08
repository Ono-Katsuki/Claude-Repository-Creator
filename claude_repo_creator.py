import os
import json
import logging
import shutil
from datetime import datetime
from tqdm import tqdm
from config_manager import ConfigManager
from cache_manager import CacheManager
from version_control import VersionControlFactory
from repo_generator import RepoGenerator
from requirements_generator import RequirementsGenerator
from repository_creator import RepositoryCreator
from markdown_generator import MarkdownGenerator
from requirements_manager import RequirementsManager

logger = logging.getLogger(__name__)

class ClaudeRepoCreator:
    def __init__(self, debug_mode=False):
        self.config_manager = ConfigManager()
        self.config = self.load_config()
        self.claude_client = None
        self.repo_generator = RepoGenerator()
        self.projects_folder = os.path.join(os.getcwd(), "claude_projects")
        self.current_project_folder = None
        self.cache_folder = os.path.join(self.projects_folder, "information_management", "cache")
        self.markdown_folder = os.path.join(self.projects_folder, "information_management", "markdown")
        self.requirements_folder = os.path.join(self.projects_folder, "information_management", "requirements")
        self.create_folder_structure()
        self.vc_system = VersionControlFactory.create(self.config['version_control'])
        self.debug_mode = debug_mode
        if self.debug_mode:
            logging.getLogger().setLevel(logging.DEBUG)
        self.requirements_generator = RequirementsGenerator(
            self.config['claude_api_key'],
            self.config['openai_api_key']
        )
        self.repository_creator = RepositoryCreator(self.config['claude_api_key'])
        self.markdown_generator = MarkdownGenerator()
        self.requirements_manager = RequirementsManager(self.requirements_folder)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.claude_client:
            await self.claude_client.close()

    def load_config(self):
        config = self.config_manager.load_config()
        if not config.get('claude_api_key'):
            config['claude_api_key'] = self.prompt_for_api_key('Claude')
            self.config_manager.save_config(config)
        if not config.get('openai_api_key'):
            config['openai_api_key'] = self.prompt_for_api_key('OpenAI')
            self.config_manager.save_config(config)
        return config

    def prompt_for_api_key(self, api_type):
        while True:
            api_key = input(f"Please enter your {api_type} API key: ").strip()
            if api_key:
                confirm = input("Is this correct? (y/n): ").lower()
                if confirm == 'y':
                    return api_key
            else:
                print("API key cannot be empty. Please try again.")

    def create_folder_structure(self):
        os.makedirs(self.cache_folder, exist_ok=True)
        os.makedirs(self.markdown_folder, exist_ok=True)
        os.makedirs(self.requirements_folder, exist_ok=True)

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

    def prompt_user_action(self):
        while True:
            action = input("\nWhat would you like to do? (1: Generate a new project, 2: Change API keys, 3: Exit): ")
            if action in ['1', '2', '3']:
                return action
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")

    async def generate_project(self):
        try:
            project_description = input("Enter the project description: ")
            
            progress_bar = tqdm(total=6, desc="Project Creation Progress", unit="step")

            # Generate detailed text requirements
            progress_bar.set_description("Generating detailed requirements")
            detailed_requirements = await self.requirements_generator.generate_text_requirements(project_description)
            progress_bar.update(1)
            
            # Generate temporary project name
            temp_project_name = f"temp_project_{datetime.now().strftime('%Y%m%d%H%M%S')}"

            # Save initial requirements
            progress_bar.set_description("Saving initial requirements")
            version = self.requirements_manager.save_requirements(temp_project_name, detailed_requirements)
            progress_bar.update(1)

            # Display and confirm requirements
            print("\nGenerated detailed requirements:")
            print(detailed_requirements)
            
            while True:
                user_choice = input("\nDo you want to proceed? (1: Continue, 2: Update requirements, 3: Abort): ")
                
                if user_choice == '1':
                    break
                elif user_choice == '2':
                    # Get the latest version of requirements
                    latest_requirements = self.requirements_manager.get_latest_requirements(temp_project_name)
                    if latest_requirements is None:
                        print("Error: Could not retrieve the latest requirements.")
                        continue

                    user_feedback = input("Please provide feedback to improve the requirements: ")
                    updated_requirements = await self.requirements_generator.update_text_requirements(latest_requirements, user_feedback)
                    print("\nUpdated detailed requirements:")
                    print(updated_requirements)
                    # Save updated requirements
                    version = self.requirements_manager.save_requirements(temp_project_name, updated_requirements)
                    detailed_requirements = updated_requirements  # Update the current working requirements
                elif user_choice == '3':
                    print("Process aborted.")
                    return
                else:
                    print("Invalid choice. Please enter 1, 2, or 3.")

            # Generate JSON requirements
            progress_bar.set_description("Generating JSON requirements")
            json_requirements = await self.requirements_generator.generate_json_requirements(detailed_requirements)
            progress_bar.update(1)
            
            # Update JSON requirements using _create_json_update_prompt
            progress_bar.set_description("Refining JSON requirements")
            updated_json_requirements = await self.requirements_generator.update_json_requirements(json_requirements, detailed_requirements)
            progress_bar.update(1)
             
            print("Debug: Updated JSON requirements:")
            print(updated_json_requirements)  # Add this line
            print("Debug: Type of updated_json_requirements:", type(updated_json_requirements))  # Add this line
        
            # Ensure updated_json_requirements is a dict, not a coroutine
            if isinstance(updated_json_requirements, dict):
                new_project_name = updated_json_requirements['project_name']
                new_cache_path = os.path.join(self.cache_folder, f'{new_project_name}_requirements.json')
                
                # Save updated requirements to JSON file
                self.save_requirements(updated_json_requirements, new_cache_path)
                
                self.create_project_folder(new_project_name)
                
                # Update temporary project name to actual project name
                os.rename(os.path.join(self.requirements_folder, temp_project_name),
                          os.path.join(self.requirements_folder, new_project_name))
                
                # Create repository
                progress_bar.set_description("Creating repository")
                await self.repository_creator.create_repository(updated_json_requirements, False, self.current_project_folder, self.repo_generator, self.vc_system)
                progress_bar.update(1)
                
                print(f"\nRepository for project: {new_project_name} has been created in folder: {self.repo_generator.repo_folder}")
                
                # Create and save project summary with full code
                progress_bar.set_description("Generating project summary")
                self.create_project_summary(updated_json_requirements)
                progress_bar.update(1)
                
                print(f"\nProject summary with full code has been created in the markdown folder.")
            else:
                raise ValueError("Invalid JSON requirements format")
            
            progress_bar.close()

        except Exception as e:
            logger.error(f"An error occurred during project generation: {str(e)}")
            if self.current_project_folder and os.path.exists(self.current_project_folder):
                shutil.rmtree(self.current_project_folder)

    async def run(self):
        print("Welcome to Claude Repo Creator!")
        while True:
            action = self.prompt_user_action()
            
            if action == '1':
                await self.generate_project()
            elif action == '2':
                self.config['claude_api_key'] = self.prompt_for_api_key('Claude')
                self.config['openai_api_key'] = self.prompt_for_api_key('OpenAI')
                self.config_manager.save_config(self.config)
                self.requirements_generator = RequirementsGenerator(
                    self.config['claude_api_key'],
                    self.config['openai_api_key']
                )
                self.repository_creator = RepositoryCreator(self.config['claude_api_key'])
                print("\nAPI keys updated.")
            elif action == '3':
                print("Exiting the program. Goodbye!")
                break

        await self.__aexit__(None, None, None)
