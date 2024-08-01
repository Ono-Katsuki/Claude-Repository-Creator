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

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ClaudeRepoCreator:
    def __init__(self, debug_mode=False):
        logger.info("Initializing ClaudeRepoCreator")
        self.config = self.load_config()
        self.claude_client = None
        self.repo_generator = RepoGenerator()
        self.cache_manager = CacheManager()
        self.vc_system = VersionControlFactory.create(self.config['version_control'])
        self.debug_mode = debug_mode
        if self.debug_mode:
            logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("ClaudeRepoCreator initialized")

    async def __aenter__(self):
        logger.debug("Entering context manager")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        logger.debug("Exiting context manager")
        if self.claude_client:
            logger.info("Closing Claude client")
            await self.claude_client.close()

    def load_config(self):
        logger.info("Loading configuration")
        config_manager = ConfigManager()
        config = config_manager.load_config()
        if not config.get('api_key'):
            logger.info("API key not found in config, prompting user")
            config['api_key'] = self.prompt_for_api_key()
            config_manager.save_config(config)
        logger.debug("Configuration loaded successfully")
        return config

    def prompt_for_api_key(self):
        logger.info("Prompting user for API key")
        while True:
            api_key = input("Please enter your Claude API key: ").strip()
            if api_key:
                confirm = input("Is this correct? (y/n): ").lower()
                if confirm == 'y':
                    logger.info("API key confirmed")
                    return api_key
            else:
                logger.warning("Empty API key entered")
                print("API key cannot be empty. Please try again.")

    def initialize_claude_client(self):
        logger.info("Initializing Claude client")
        if not self.claude_client:
            self.claude_client = anthropic.AsyncAnthropic(api_key=self.config['api_key'])
        logger.debug("Claude client initialized")

    async def generate_requirements(self, project_description):
        logger.info("Generating requirements")
        self.initialize_claude_client()
        cache_key = f"requirements_{hash(project_description)}"
        cached_requirements = self.cache_manager.get(cache_key)
        if cached_requirements:
            logger.info("Using cached requirements")
            return cached_requirements

        prompt = self.create_requirements_prompt(project_description)
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"Sending request to Claude API (attempt {attempt + 1}/{max_retries})")
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
                logger.debug(f"Full response from Claude API: {response}")
                logger.info(f"Received response from Claude API: {response[:100]}...")  # Log first 100 characters
                
                # Extract JSON from the response
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    requirements = json.loads(json_str)
                    logger.info("Successfully parsed requirements JSON")
                    self.validate_requirements(requirements)
                    self.cache_manager.set(cache_key, requirements)
                    return requirements
                else:
                    logger.error("No JSON found in the response")
                    raise ValueError("No JSON found in the response")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Claude's response as JSON: {e}")
                logger.error(f"Raw response: {response}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying... (Attempt {attempt + 2} of {max_retries})")
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise ValueError("Invalid response format from Claude API after multiple attempts.")
            except KeyError as e:
                logger.error(f"Missing required key in requirements: {str(e)}")
                raise ValueError("Incomplete requirements generated.")
            except Exception as e:
                logger.error(f"Error generating requirements: {str(e)}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying... (Attempt {attempt + 2} of {max_retries})")
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise

    def create_requirements_prompt(self, project_description):
        logger.debug("Creating requirements prompt")
        return f"""
        Based on the following project description, create a detailed requirements definition:

        {project_description}

        For the "tech_stack" field, please only use the following allowed values:
        ["python", "javascript", "java", "react", "react native", "html", "css", "ruby"]

        Make sure to use the full filename with its extension for the "name" field within "files".

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
        logger.info("Validating requirements")
        required_keys = ["project_name", "description", "features", "tech_stack", "folder_structure"]
        for key in required_keys:
            if key not in requirements:
                logger.error(f"Missing required key in requirements: {key}")
                raise KeyError(f"Missing required key: {key}")
        logger.debug("Requirements validation successful")
        logger.debug(f"Validated requirements: {json.dumps(requirements, indent=2)}")

    async def create_repository(self, requirements, update_existing=False):
        try:
            project_name = requirements['project_name']
            logger.info(f"Creating repository for project: {project_name}")
            self.repo_generator.create_repo_folder(project_name)
            
            if update_existing:
                logger.info("Updating existing repository")
                await self.update_existing_repository(requirements)
            else:
                logger.info("Creating new repository structure")
                self.repo_generator.create_structure(requirements['folder_structure'])
                self.repo_generator.create_readme(requirements)
                self.repo_generator.create_gitignore(requirements['tech_stack'])
            
            logger.info("Creating feature files")
            await self.create_feature_files(requirements['features'], requirements['tech_stack'], requirements['folder_structure'])
            
            logger.info("Initializing version control")
            self.vc_system.initialize(self.repo_generator.repo_folder)
            self.vc_system.add_all()
            self.vc_system.commit("Initial commit")
            
            logger.info(f"Repository for project: {project_name} has been {'updated' if update_existing else 'created'} successfully in folder: {self.repo_generator.repo_folder}")
        except Exception as e:
            logger.error(f"Error creating repository: {str(e)}", exc_info=True)
            raise

    async def update_existing_repository(self, requirements):
        try:
            logger.info("Updating existing repository structure")
            current_structure = self.repo_generator.get_current_structure()
            updated_structure = requirements['folder_structure']
            logger.debug(f"Current structure: {json.dumps(current_structure, indent=2)}")
            logger.debug(f"Updated structure: {json.dumps(updated_structure, indent=2)}")
            self.repo_generator.update_structure(current_structure, updated_structure)
            self.repo_generator.update_readme(requirements)
            self.repo_generator.update_gitignore(requirements['tech_stack'])
            logger.info("Existing repository updated successfully")
        except Exception as e:
            logger.error(f"Error updating existing repository: {str(e)}", exc_info=True)
            raise

    async def create_feature_files(self, features, tech_stack, folder_structure):
        try:
            logger.info("Creating feature files")
            logger.info(f"Folder structure: {json.dumps(folder_structure, indent=2)}")  # 1. フォルダ構造のログ
            self.initialize_claude_client()
            code_generator = CodeGenerator(self.config['api_key'], tech_stack)
            
            async def generate_code(file_info, file_path, feature=None):
                try:
                    logger.info(f"Generating code for {file_info['name']}")
                    feature_code = await code_generator.generate_feature_code(feature, file_info)
                    if feature_code is None:
                        logger.warning(f"No code generated for {file_info['name']}")
                        return file_info['name'], None
                    
                    logger.info(f"Writing code to file: {file_path}")
                    code_generator.write_code_to_file(file_path, feature_code)
                    logger.info(f"Code for {file_info['name']} generated and saved to {file_path}")
                    return file_info['name'], file_path
                except Exception as e:
                    logger.error(f"Error processing file {file_info['name']}: {str(e)}", exc_info=True)
                    return file_info['name'], None

            def process_folder(folder_content, current_path):
                logger.info(f"Starting to process folder: {current_path}")
                logger.info(f"Folder content: {json.dumps(folder_content, indent=2)}")
    
                tasks = []
                logger.info(f"Initial tasks list: {tasks}")
    
                files = folder_content.get('files', [])
                logger.info(f"Files to process in {current_path}: {[f['name'] for f in files]}")
    
                for file_info in files:
                    logger.info(f"Processing file: {file_info['name']}")
                    file_path = os.path.join(current_path, file_info['name'])
                    logger.info(f"Full file path: {file_path}")
        
                    feature = self._get_feature_for_file(features, file_info['name'])
                    logger.info(f"Feature for file {file_info['name']}: {feature['name'] if feature else 'None'}")
        
                    logger.info(f"Appending generate_code task for {file_info['name']}")
                    tasks.append(generate_code(file_info, file_path, feature))
    
                logger.info(f"Tasks after processing files: {len(tasks)}")
    
                subfolders = folder_content.get('subfolders', {})
                logger.info(f"Subfolders to process in {current_path}: {list(subfolders.keys())}")
    
                for subfolder_name, subfolder_content in subfolders.items():
                    logger.info(f"Processing subfolder: {subfolder_name}")
                    subfolder_path = os.path.join(current_path, subfolder_name)
                    logger.info(f"Creating subfolder: {subfolder_path}")
                    os.makedirs(subfolder_path, exist_ok=True)
        
                    logger.info(f"Recursively calling process_folder for {subfolder_name}")
                    subfolder_tasks = process_folder(subfolder_content, subfolder_path)
                    logger.info(f"Tasks returned from {subfolder_name}: {len(subfolder_tasks)}")
        
                    logger.info(f"Extending tasks with subfolder tasks from {subfolder_name}")
                    tasks.extend(subfolder_tasks)
    
                logger.info(f"Total tasks after processing {current_path}: {len(tasks)}")
                return tasks
                
            tasks = process_folder(folder_structure, self.repo_generator.repo_folder)

            logger.info(f"Starting to generate {len(tasks)} files")
            results = []
            for future in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Generating Files"):
                result = await future
                results.append(result)
            
            logger.info("All files generated successfully")
            logger.info(f"Generated files: {json.dumps(dict(results), indent=2)}")  # 4. 生成されたファイルのリストのログ
            return dict(results)
        except Exception as e:
            logger.error(f"Error creating files: {str(e)}", exc_info=True)
            raise

    def _get_feature_for_file(self, features, file_name):
        logger.debug(f"Getting feature for file: {file_name}")
        for feature in features:
            feature_name = feature['name'].lower().replace(' ', '_')
            if file_name.lower().startswith(feature_name):
                logger.debug(f"Feature found for file {file_name}: {feature['name']}")
                return feature
        logger.debug(f"No specific feature found for file: {file_name}")
        return None

    async def run(self):
        try:
            logger.info("Starting ClaudeRepoCreator")
            project_description = input("プロジェクトの説明を入力してください: ")
            logger.info("Generating requirements based on project description")
            requirements = await self.generate_requirements(project_description)
            
            update_existing = input("既存のリポジトリを更新しますか？ (y/n): ").lower() == 'y'
            logger.info(f"User chose to {'update existing' if update_existing else 'create new'} repository")
            await self.create_repository(requirements, update_existing)
            
            logger.info(f"プロジェクト: {requirements['project_name']} のリポジトリが{'更新' if update_existing else '作成'}されました。フォルダ: {self.repo_generator.repo_folder}")
        except Exception as e:
            logger.error(f"プログラム実行中にエラーが発生しました: {str(e)}", exc_info=True)
        finally:
            logger.info("Closing ClaudeRepoCreator")
            await self.__aexit__(None, None, None)

if __name__ == "__main__":
    debug_mode = os.environ.get('DEBUG', 'False').lower() == 'true'
    logger.info(f"Debug mode: {debug_mode}")
    
    async def main():
        logger.info("Starting main function")
        async with ClaudeRepoCreator(debug_mode=debug_mode) as creator:
            await creator.run()
        logger.info("Main function completed")

    asyncio.run(main())
