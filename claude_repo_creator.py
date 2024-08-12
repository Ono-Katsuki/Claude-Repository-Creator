import os
import json
import logging
import shutil
from datetime import datetime
from tqdm import tqdm
from config_manager import ConfigManager
from cache_manager import CacheManager
from version_control import VersionControlFactory
from repository_generator import RepoGenerator
from requirements_generator import RequirementsGenerator
from repository_creator import RepositoryCreator
from markdown_generator import MarkdownGenerator
from requirements_manager import RequirementsManager
from repository_models import Requirements

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
            self.config.get('claude_api_key'),
            self.config.get('openai_api_key')
        )
        self.repository_creator = RepositoryCreator(self.config.get('claude_api_key'))
        self.markdown_generator = MarkdownGenerator()
        self.requirements_manager = RequirementsManager(self.requirements_folder, self.cache_folder)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.claude_client:
            await self.claude_client.close()

    def load_config(self):
        config = self.config_manager.load_config()
        if not config.get('claude_api_key') or not config.get('openai_api_key'):
            self.update_api_keys(config)
        return config

    def update_api_keys(self, config):
        print("\nCurrent API key status:")
        print(f"Claude API key: {'Set' if config.get('claude_api_key') else 'Not set'}")
        print(f"OpenAI API key: {'Set' if config.get('openai_api_key') else 'Not set'}")

        while True:
            choice = input("\nWhich API key would you like to update? (1: Claude, 2: OpenAI, 3: Both, 4: Skip): ")
            if choice == '1':
                config['claude_api_key'] = self.prompt_for_api_key('Claude')
                break
            elif choice == '2':
                config['openai_api_key'] = self.prompt_for_api_key('OpenAI')
                break
            elif choice == '3':
                config['claude_api_key'] = self.prompt_for_api_key('Claude')
                config['openai_api_key'] = self.prompt_for_api_key('OpenAI')
                break
            elif choice == '4':
                break
            else:
                print("Invalid choice. Please enter 1, 2, 3, or 4.")

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

    def save_requirements(self, requirements: Requirements, project_name: str):
        json_requirements = requirements.model_dump()
        version = self.requirements_manager.save_requirements(project_name, json_requirements, is_json=True)
        logger.info(f"Saved JSON requirements to cache: {project_name}, version {version}")
        return version
        
    def create_project_summary(self, requirements: Requirements, project_name: str, version: str):
        project_markdown_folder = os.path.join(self.markdown_folder, project_name)
        os.makedirs(project_markdown_folder, exist_ok=True)
        
        summary_filename = f"{requirements.project_name}_summary_v{version}.md"
        summary_path = os.path.join(project_markdown_folder, summary_filename)
        
        self.markdown_generator.create_project_summary(requirements.model_dump(), self.repo_generator.repo_folder, summary_path)
        logger.info(f"Created project summary: {summary_path}")

    def prompt_user_action(self):
        while True:
            action = input("\nWhat would you like to do? (1: Generate a new project, 2: Continue from a stage, 3: Update API keys, 4: Exit): ")
            if action in ['1', '2', '3', '4']:
                return action
            else:
                print("Invalid choice. Please enter 1, 2, 3, or 4.")

    def prompt_continue_stage(self):
        while True:
            stage = input("\nFrom which stage would you like to continue? (1: Upgrade text requirements, 2: Generate JSON from text, 3: Upgrade JSON requirements, 4: Generate project from JSON): ")
            if stage in ['1', '2', '3', '4']:
                return stage
            else:
                print("Invalid choice. Please enter 1, 2, 3, or 4.")

    def select_project(self):
        projects = [d for d in os.listdir(self.projects_folder) if os.path.isdir(os.path.join(self.projects_folder, d)) and d != "information_management"]
        if not projects:
            print("No existing projects found.")
            return None
        print("\nAvailable projects:")
        for i, project in enumerate(projects, 1):
            print(f"{i}: {project}")
        while True:
            choice = input("Select a project number: ")
            try:
                index = int(choice) - 1
                if 0 <= index < len(projects):
                    return projects[index]
                else:
                    print("Invalid choice. Please enter a valid project number.")
            except ValueError:
                print("Invalid input. Please enter a number.")
                
    def select_version(self, project_name, is_json=False):
        versions = self.requirements_manager.get_all_versions(project_name, is_json)
        if not versions:
            print("No versions found for this project.")
            return None
        print("\nAvailable versions:")
        for i, version in enumerate(versions, 1):
            print(f"{i}: {version}")
        while True:
            choice = input("Select a version number: ")
            try:
                index = int(choice) - 1
                if 0 <= index < len(versions):
                    return versions[index].split('_v')[1].split('.')[0]
                else:
                    print("Invalid choice. Please enter a valid version number.")
            except ValueError:
                print("Invalid input. Please enter a number.")

    async def generate_project(self):
        try:
            project_description = input("Enter the project description: ")
            
            progress_bar = tqdm(total=7, desc="Project Creation Progress", unit="step")

            # Generate detailed text requirements
            progress_bar.set_description("Generating detailed requirements")
            detailed_requirements = await self.requirements_generator.generate_text_requirements(project_description)
            progress_bar.update(1)
            
            # Generate temporary project name
            temp_project_name = f"temp_project_{datetime.now().strftime('%Y%m%d%H%M%S')}"

            # Save initial text requirements
            progress_bar.set_description("Saving initial text requirements")
            version = self.requirements_manager.save_requirements(temp_project_name, detailed_requirements)
            progress_bar.update(1)

            # Text requirements loop
            detailed_requirements = await self.text_requirements_loop(temp_project_name, detailed_requirements)
            progress_bar.update(1)

            # Generate structured requirements
            progress_bar.set_description("Generating structured requirements")
            requirements = await self.requirements_generator.generate_structured_requirements(detailed_requirements)
            progress_bar.update(1)
            
            # Save initial JSON requirements
            progress_bar.set_description("Saving initial JSON requirements")
            self.save_requirements(requirements, temp_project_name)
            progress_bar.update(1)

            # JSON requirements loop
            updated_requirements = await self.json_requirements_loop(temp_project_name, requirements, detailed_requirements)
            progress_bar.update(1)
        
            new_project_name = updated_requirements.project_name
            
            self.create_project_folder(new_project_name)
            
            # Update temporary project name to actual project name
            os.rename(os.path.join(self.requirements_folder, temp_project_name),
                      os.path.join(self.requirements_folder, new_project_name))
            os.rename(os.path.join(self.cache_folder, temp_project_name),
                      os.path.join(self.cache_folder, new_project_name))
            
            # Create repository
            progress_bar.set_description("Creating repository")
            await self.create_project_from_requirements(new_project_name, updated_requirements)
            progress_bar.update(1)
            
            progress_bar.close()

        except Exception as e:
            logger.error(f"An error occurred during project generation: {str(e)}")
            if self.current_project_folder and os.path.exists(self.current_project_folder):
                shutil.rmtree(self.current_project_folder)

    async def text_requirements_loop(self, project_name, detailed_requirements):
        while True:
            print("\nCurrent text requirements:")
            print(detailed_requirements)
            
            user_choice = input("\nDo you want to update the text requirements? (1: Yes, 2: No): ")
            
            if user_choice == '1':
                user_feedback = input("Please provide feedback to improve the requirements: ")
                updated_requirements = await self.requirements_generator.update_text_requirements(detailed_requirements, user_feedback)
                print("\nUpdated text requirements:")
                print(updated_requirements)
                # Save updated requirements
                version = self.requirements_manager.save_requirements(project_name, updated_requirements)
                detailed_requirements = updated_requirements
            elif user_choice == '2':
                break
            else:
                print("Invalid choice. Please enter 1 or 2.")
        
        return detailed_requirements

    async def json_requirements_loop(self, project_name, requirements, detailed_requirements):
        while True:
            print("\nCurrent JSON requirements:")
            print(json.dumps(requirements.model_dump(), indent=2))
            
            user_choice = input("\nDo you want to update the JSON requirements? (1: Yes, 2: No): ")
            
            if user_choice == '1':
                user_feedback = input("Please provide feedback to improve the requirements: ")
                updated_requirements = await self.requirements_generator.update_structured_requirements(requirements, detailed_requirements, user_feedback)
                print("\nUpdated JSON requirements:")
                print(json.dumps(updated_requirements.model_dump(), indent=2))
                # Save updated requirements
                self.save_requirements(updated_requirements, project_name)
                requirements = updated_requirements
            elif user_choice == '2':
                break
            else:
                print("Invalid choice. Please enter 1 or 2.")
        
        return requirements

    async def continue_from_stage(self):
        project_name = self.select_project()
        if not project_name:
            return

        stage = self.prompt_continue_stage()
        
        # Initialize variables
        text_requirements = None
        json_requirements = None
        requirements = None
        
        while stage in ['1', '2', '3', '4']:
            if stage == '1':  # Upgrade text requirements
                version = self.select_version(project_name, is_json=False)
                if not version:
                    break
                text_requirements = self.requirements_manager.get_requirements_by_version(project_name, version, is_json=False)
                updated_text = await self.text_requirements_loop(project_name, text_requirements)
                new_version = self.requirements_manager.save_requirements(project_name, updated_text, is_json=False)
                print(f"Updated text requirements saved as version {new_version}")
                text_requirements = updated_text

            if stage <= '2':  # Generate JSON from text
                if text_requirements is None:
                    version = self.select_version(project_name, is_json=False)
                    if not version:
                        break
                    text_requirements = self.requirements_manager.get_requirements_by_version(project_name, version, is_json=False)
                json_requirements = await self.requirements_generator.generate_structured_requirements(text_requirements)
                new_version = self.save_requirements(json_requirements, project_name)
                print(f"Generated JSON requirements saved as version {new_version}")
                requirements = json_requirements

            if stage <= '3':  # Upgrade JSON requirements
                if requirements is None:
                    version = self.select_version(project_name, is_json=True)
                    if not version:
                        break
                    json_requirements = self.requirements_manager.get_requirements_by_version(project_name, version, is_json=True)
                    requirements = Requirements(**json_requirements)
                updated_requirements = await self.json_requirements_loop(project_name, requirements, "")
                new_version = self.save_requirements(updated_requirements, project_name)
                print(f"Updated JSON requirements saved as version {new_version}")
                requirements = updated_requirements

            if stage <= '4':  # Generate project from JSON
                if requirements is None:
                    version = self.select_version(project_name, is_json=True)
                    if not version:
                        break
                    json_requirements = self.requirements_manager.get_requirements_by_version(project_name, version, is_json=True)
                    requirements = Requirements(**json_requirements)
                await self.create_project_from_requirements(project_name, requirements)

            # Ask if the user wants to continue to the next stage
            next_stage = int(stage) + 1
            if next_stage <= 4:
                if input(f"Do you want to continue to stage {next_stage}? (y/n): ").lower() == 'y':
                    stage = str(next_stage)
                else:
                    break
            else:
                break

        # Clean up variables after the loop
        del text_requirements
        del json_requirements
        del requirements

    async def create_project_from_requirements(self, project_name, requirements):
        version = datetime.now().strftime('%Y%m%d%H%M%S')
        self.current_project_folder = os.path.join(self.projects_folder, project_name, f"v{version}")
        os.makedirs(self.current_project_folder, exist_ok=True)

        progress_bar = tqdm(total=2, desc="Project Creation Progress", unit="step")

        # Create repository
        progress_bar.set_description("Creating repository")
        await self.repository_creator.create_repository(requirements, False, self.current_project_folder, self.repo_generator, self.vc_system)
        progress_bar.update(1)
    
        print(f"\nRepository for project: {project_name} has been created in folder: {self.current_project_folder}")
    
        # Create and save project summary with full code
        self.create_project_summary(requirements, project_name, version)
        print(f"\nProject summary with full code has been created in the markdown folder.")
        progress_bar.update(1)
        
        progress_bar.close()

    async def run(self):
        print("Welcome to Claude Repo Creator!")
        while True:
            action = self.prompt_user_action()
            
            if action == '1':
                await self.generate_project()
            elif action == '2':
                await self.continue_from_stage()
            elif action == '3':
                self.config = self.update_api_keys(self.config)
                self.requirements_generator = RequirementsGenerator(
                    self.config.get('claude_api_key'),
                    self.config.get('openai_api_key')
                )
                self.repository_creator = RepositoryCreator(self.config.get('claude_api_key'))
                print("\nAPI keys updated.")
            elif action == '4':
                print("Exiting the program. Goodbye!")
                break

        await self.__aexit__(None, None, None)
