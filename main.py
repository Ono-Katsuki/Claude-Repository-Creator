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
from code_tester import CodeTester

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ClaudeRepoCreator:
    def __init__(self, debug_mode=False):
        self.config = self.load_config()
        self.claude_client = None
        self.repo_generator = RepoGenerator()
        self.cache_manager = CacheManager()
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

    async def generate_requirements(self, project_description):
        self.initialize_claude_client()
        cache_key = f"requirements_{hash(project_description)}"
        cached_requirements = self.cache_manager.get(cache_key)
        if cached_requirements:
            return cached_requirements

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
                logger.debug(f"Full response from Claude API: {response}")
                logger.info(f"Received response from Claude API: {response[:100]}...")  # Log first 100 characters
                
                # Extract JSON from the response
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    requirements = json.loads(json_str)
                    self.validate_requirements(requirements)
                    self.cache_manager.set(cache_key, requirements)
                    return requirements
                else:
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
        return f"""
        Based on the following project description, create a detailed requirements definition:

        {project_description}

        Provide the requirements in the following JSON format:
        For the "tech_stack" field, please only use the following allowed values:
        ["python", "javascript", "java", "react", "react native", "html", "css", "ruby"]

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
            self.repo_generator.create_repo_folder(project_name)
            
            if update_existing:
                await self.update_existing_repository(requirements)
            else:
                self.repo_generator.create_structure(requirements['folder_structure'])
                self.repo_generator.create_readme(requirements)
                self.repo_generator.create_gitignore(requirements['tech_stack'])
            
            feature_results = await self.create_feature_files(requirements['features'], requirements['tech_stack'], requirements['folder_structure'])
            
            self.vc_system.initialize(self.repo_generator.repo_folder)
            self.vc_system.add_all()
            self.vc_system.commit("Initial commit")
            
            print(f"Repository for project: {project_name} has been {'updated' if update_existing else 'created'} successfully in folder: {self.repo_generator.repo_folder}")
        except Exception as e:
            logger.error(f"Error creating repository: {str(e)}")
            raise

    async def update_existing_repository(self, requirements):
        try:
            current_structure = self.repo_generator.get_current_structure()
            updated_structure = requirements['folder_structure']
            self.repo_generator.update_structure(current_structure, updated_structure)
            self.repo_generator.update_readme(requirements)
            self.repo_generator.update_gitignore(requirements['tech_stack'])
        except Exception as e:
            logger.error(f"Error updating existing repository: {str(e)}")
            raise

    async def create_feature_files(self, features, tech_stack, folder_structure):
        try:
            self.initialize_claude_client()
            code_generator = CodeGenerator(self.config['api_key'], tech_stack)
            
            async def generate_and_test(feature, file_info, file_path):
                try:
                    feature_code = await code_generator.generate_feature_code(feature, file_info)
                    if feature_code is None:
                        logger.warning(f"No code generated for {feature['name']} - {file_info['name']}")
                        return f"{feature['name']} - {file_info['name']}", None
                    
                    code_tester = CodeTester(tech_stack)
                    test_result = code_tester.test_code(feature_code)
                    
                    if test_result['success']:
                        code_generator.write_code_to_file(file_path, feature_code)
                        logger.info(f"Code for {feature['name']} - {file_info['name']} passed tests and saved to {file_path}")
                        return f"{feature['name']} - {file_info['name']}", file_path
                    else:
                        logger.error(f"Generated code for {feature['name']} - {file_info['name']} contains errors: {test_result['message']}")
                        self.show_error_message(f"Error in {feature['name']} - {file_info['name']}: {test_result['message']}")
                        return f"{feature['name']} - {file_info['name']}", None
                except Exception as e:
                    logger.error(f"Error processing feature {feature['name']} - {file_info['name']}: {str(e)}")
                    return f"{feature['name']} - {file_info['name']}", None

            tasks = []
            for feature in features:
                feature_name = feature['name'].lower().replace(' ', '_')
                if feature_name in folder_structure:
                    for file_info in folder_structure[feature_name].get('files', []):
                        file_path = os.path.join(self.repo_generator.repo_folder, feature_name, file_info['name'])
                        tasks.append(generate_and_test(feature, file_info, file_path))
                else:
                    logger.warning(f"No matching folder found for feature: {feature['name']}")

            results = []
            for future in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Generating Features"):
                result = await future
                results.append(result)
            
            return dict(results)
        except Exception as e:
            logger.error(f"Error creating feature files: {str(e)}")
            raise

    def show_error_message(self, message):
        print(f"Error: {message}")

    async def run(self):
        try:
            project_description = input("プロジェクトの説明を入力してください: ")
            requirements = await self.generate_requirements(project_description)
            
            update_existing = input("既存のリポジトリを更新しますか？ (y/n): ").lower() == 'y'
            await self.create_repository(requirements, update_existing)
            
            print(f"プロジェクト: {requirements['project_name']} のリポジトリが{'更新' if update_existing else '作成'}されました。フォルダ: {self.repo_generator.repo_folder}")
        except Exception as e:
            logger.error(f"プログラム実行中にエラーが発生しました: {str(e)}")
        finally:
            await self.__aexit__(None, None, None)

if __name__ == "__main__":
    debug_mode = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    async def main():
        async with ClaudeRepoCreator(debug_mode=debug_mode) as creator:
            await creator.run()

    asyncio.run(main())
