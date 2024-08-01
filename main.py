import os
import sys
import json
import logging
import re
import asyncio
import anthropic
from tqdm import tqdm
from repo_generator import RepoGenerator
from config_manager import ConfigManager
from cache_manager import CacheManager
from version_control import VersionControlFactory
from code_generator import CodeGenerator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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

    def initialize_claude_client(self):
        if not self.claude_client:
            self.claude_client = anthropic.AsyncAnthropic(api_key=self.config['api_key'])

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

    async def generate_requirements(self, project_description):
        self.initialize_claude_client()
        cache_key = f"requirements_{hash(project_description)}"

        prompt = self.create_requirements_prompt(project_description)
        max_retries = 3
        for attempt in range(max_retries):
            try:
                message = await self.claude_client.messages.create(
                    model="claude-3-5-sonnet-20240620",
                    max_tokens=4096,
                    temperature=0,
                    system="You are an AI assistant specialized in software development and repository creation. Provide detailed and structured responses.",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": prompt
                                }
                            ]
                        }
                    ]
                )
                response = message.content[0].text
                
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    requirements = json.loads(json_str)
                    self.validate_requirements(requirements)
                    improved_requirements = await self.evaluate_and_improve_requirements(requirements, project_description)
                    self.cache_manager.set(cache_key, improved_requirements)
                    return improved_requirements
                else:
                    raise ValueError("No JSON found in the response")
            except json.JSONDecodeError as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise ValueError("Invalid response format from Claude API after multiple attempts.")
            except KeyError as e:
                raise ValueError("Incomplete requirements generated.")
            except Exception as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise

    async def evaluate_and_improve_requirements(self, requirements, project_description):
        prompt = f"""
        Evaluate and improve the following project requirements:
        Provide the improved requirements in the same JSON format as the input.
        It is absolutely crucial that you generate a complete and perfect JSON without any omissions or abbreviations. Every field must be properly filled, and there should be no placeholder values or TODO comments.
        
        For the "tech_stack" field, please only use the following allowed values:
        ["python", "javascript", "java", "react", "react native", "html", "css", "ruby"]
        
        Project Description:
        {project_description}

        Current Requirements:
        {json.dumps(requirements, indent=2)}

        Please analyze these requirements and make the following improvements:
        1. Ensure there is a main file (e.g., main.py, index.js) in the appropriate location.
        2. Check that all necessary dependencies are included.
        3. Verify that the folder structure is logical and follows best practices for the chosen tech stack.
        4. Make sure all function and method calls are correct and consistent.
        5. Add any missing critical components for the project to function properly.
        6. Ensure the tech stack is appropriate for the project description.
        7. Verify that all features have clear and testable acceptance criteria.

        """

        message = await self.claude_client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=4096,
            temperature=0,
            system="You are an AI assistant specialized in software development and repository creation. Provide detailed and structured responses.",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )
        response = message.content[0].text
        
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            improved_requirements = json.loads(json_str)
            self.validate_requirements(improved_requirements)
            return improved_requirements
        else:
            raise ValueError("No JSON found in the improved requirements response")

    def create_requirements_prompt(self, project_description):
        return f"""
        Based on the following project description, create a detailed requirements definition:

        It is absolutely crucial that you generate a complete and perfect JSON without any omissions or abbreviations. Every field must be properly filled, and there should be no placeholder values or TODO comments.

        {project_description}

        For the "tech_stack" field, please only use the following allowed values:
        ["python", "javascript", "java", "react", "react native", "html", "css", "ruby"]

        Make sure to use the full filename with its extension for the "name" field within "files".
        
        Ensure that ALL fields are properly filled and that there are NO empty arrays or objects.
        Include at least one item in each array (features, tech_stack, files, etc.).
        For the folder structure, provide a realistic and comprehensive structure that reflects the project's complexity.
        Include a main file (e.g., main.py, index.js) in the appropriate location.

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
                    "files": [
                        {{
                            "name": "string",
                            "type": "class|function|component",
                            "description": "string",
                            "properties": ["string"],
                            "methods": [
                                {{
                                    "name": "string",
                                    "params": ["string"],
                                    "return_type": "string",
                                    "description": "string"
                                }}
                            ]
                        }}
                    ]
                }}
            }}
        }}
        """

    def validate_requirements(self, requirements):
        required_keys = ["project_name", "description", "features", "tech_stack", "folder_structure"]
        for key in required_keys:
            if key not in requirements:
                raise KeyError(f"Missing required key: {key}")

    async def create_repository(self, requirements, update_existing=False):
        try:
            project_name = requirements['project_name']
            self.create_project_folder(project_name)
            self.repo_generator.create_repo_folder(self.current_project_folder)
            
            if update_existing:
                await self.update_existing_repository(requirements)
            else:
                self.repo_generator.create_structure(requirements['folder_structure'])
                self.repo_generator.create_readme(requirements)
                self.repo_generator.create_gitignore(requirements['tech_stack'])
            
            await self.create_feature_files(requirements['features'], requirements['tech_stack'], requirements['folder_structure'])
            
            self.vc_system.initialize(self.repo_generator.repo_folder)
            self.vc_system.add_all()
            self.vc_system.commit("Initial commit")
            
            print(f"Repository for project: {project_name} has been {'updated' if update_existing else 'created'} successfully in folder: {self.repo_generator.repo_folder}")
        except Exception as e:
            print(f"Error creating repository: {str(e)}")
            raise

    async def update_existing_repository(self, requirements):
        try:
            current_structure = self.repo_generator.get_current_structure()
            updated_structure = requirements['folder_structure']
            self.repo_generator.update_structure(current_structure, updated_structure)
            self.repo_generator.update_readme(requirements)
            self.repo_generator.update_gitignore(requirements['tech_stack'])
        except Exception as e:
            print(f"Error updating existing repository: {str(e)}")
            raise

    async def create_feature_files(self, features, tech_stack, folder_structure):
        try:
            self.initialize_claude_client()
            code_generator = CodeGenerator(self.config['api_key'], tech_stack)
            
            async def generate_code(file_info, file_path, feature=None):
                try:
                    feature_code = await code_generator.generate_feature_code(feature, file_info)
                    if feature_code is None:
                        return file_info['name'], None
                    
                    code_generator.write_code_to_file(file_path, feature_code)
                    return file_info['name'], file_path
                except Exception as e:
                    print(f"Error processing file {file_info['name']}: {str(e)}")
                    return file_info['name'], None

            async def process_structure(structure, base_path):
                tasks = []
                for folder, contents in structure.items():
                    folder_path = os.path.join(base_path, folder)
                    os.makedirs(folder_path, exist_ok=True)
                    
                    for file_info in contents.get("files", []):
                        file_path = os.path.join(folder_path, file_info['name'])
                        feature = self._get_feature_for_file(features, file_info['name'])
                        tasks.append(generate_code(file_info, file_path, feature))
                    
                    if "subfolders" in contents:
                        subfolder_tasks = await process_structure(contents["subfolders"], folder_path)
                        tasks.extend(subfolder_tasks)
                
                return tasks

            tasks = await process_structure(folder_structure, self.repo_generator.repo_folder)
            
            print(f"Starting to generate {len(tasks)} files")
            results = []
            for future in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Generating Files"):
                result = await future
                results.append(result)
            
            print("All files generated successfully")
            return dict(results)
        except Exception as e:
            print(f"Error creating files: {str(e)}")
            raise

    def _get_feature_for_file(self, features, file_name):
        for feature in features:
            feature_name = feature['name'].lower().replace(' ', '_')
            if file_name.lower().startswith(feature_name):
                return feature
        return None

    async def run(self):
        try:
            project_description = input("Enter the project description: ")
            project_name = input("Enter the project name: ")
            self.create_project_folder(project_name)
            
            requirements = await self.generate_requirements(project_description)
            
            update_existing = input("Do you want to update an existing repository? (y/n): ").lower() == 'y'
            await self.create_repository(requirements, update_existing)
            
            print(f"Repository for project: {project_name} has been {'updated' if update_existing else 'created'} in folder: {self.repo_generator.repo_folder}")
        except Exception as e:
            print(f"An error occurred during program execution: {str(e)}")
        finally:
            await self.__aexit__(None, None, None)


if __name__ == "__main__":
    debug_mode = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    async def main():
        async with ClaudeRepoCreator(debug_mode=debug_mode) as creator:
            await creator.run()

    asyncio.run(main())
