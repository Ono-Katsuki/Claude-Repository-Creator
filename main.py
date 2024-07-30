import os
import sys
import json
import logging
import re
import asyncio
from tkinter import Tk, scrolledtext, Button, Label, Entry, StringVar
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

    def load_config(self):
        config_manager = ConfigManager()
        config = config_manager.load_config()
        if not config.get('api_key'):
            config['api_key'] = self.prompt_for_api_key()
            config_manager.save_config(config)
        return config

    def prompt_for_api_key(self):
        print("API key is not set. How would you like to enter it?")
        print("1. GUI")
        print("2. Console")
        choice = input("Enter your choice (1 or 2): ")
        
        if choice == '1':
            return self.prompt_gui_input()
        elif choice == '2':
            return self.prompt_console_input()
        else:
            print("Invalid choice. Defaulting to console input.")
            return self.prompt_console_input()

    def prompt_gui_input(self):
        root = Tk()
        root.title("Enter API Key")
        
        api_key = StringVar()
        
        Label(root, text="Please enter your Claude API key:").pack(pady=10)
        Entry(root, textvariable=api_key, show="*", width=50).pack(pady=5)
        
        def save_and_exit():
            root.quit()
        
        Button(root, text="Save", command=save_and_exit).pack(pady=10)
        
        root.mainloop()
        root.destroy()
        
        return api_key.get()

    def prompt_console_input(self):
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
            
            await self.create_feature_files(requirements['features'], requirements['tech_stack'])

            self.vc_system.initialize(self.repo_generator.repo_folder)
            
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

    async def create_feature_files(self, features, tech_stack):
        try:
            self.initialize_claude_client()
            code_generator = CodeGenerator(self.config['api_key'], tech_stack)
            
            async def generate_and_test(feature):
                feature_code = await code_generator.generate_feature_code(feature)
                if feature_code is None:
                    return feature['name'], None
                
                code_tester = CodeTester(tech_stack)
                test_result = code_tester.test_code(feature_code)
                
                if test_result['success']:
                    edited_code = await self.show_code_editor(feature['name'], feature_code)
                    self.repo_generator.create_feature_files(feature['name'], edited_code, tech_stack)
                    return feature['name'], edited_code
                else:
                    logger.error(f"Generated code for {feature['name']} contains errors: {test_result['message']}")
                    await self.show_error_message(f"Error in {feature['name']}: {test_result['message']}")
                    return feature['name'], None

            tasks = [generate_and_test(feature) for feature in features]
            results = []
            
            for future in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Generating Features"):
                result = await future
                results.append(result)
            
            return dict(results)
        except Exception as e:
            logger.error(f"Error creating feature files: {str(e)}")
            raise

    async def show_code_editor(self, feature_name, code):
        return await asyncio.to_thread(self._show_code_editor_sync, feature_name, code)

    def _show_code_editor_sync(self, feature_name, code):
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

    async def show_error_message(self, message):
        await asyncio.to_thread(self._show_error_message_sync, message)

    def _show_error_message_sync(self, message):
        root = Tk()
        root.title("Error")
        
        label = Label(root, text=message)
        label.pack(padx=20, pady=20)

        ok_button = Button(root, text="OK", command=root.destroy)
        ok_button.pack(pady=10)

        root.mainloop()

    async def run(self):
        try:
            project_description = input("プロジェクトの説明を入力してください: ")
            requirements = await self.generate_requirements(project_description)
            
            update_existing = input("既存のリポジトリを更新しますか？ (y/n): ").lower() == 'y'
            await self.create_repository(requirements, update_existing)
            
            print(f"プロジェクト: {requirements['project_name']} のリポジトリが{'更新' if update_existing else '作成'}されました。フォルダ: {self.repo_generator.repo_folder}")
        except Exception as e:
            logger.error(f"プログラム実行中にエラーが発生しました: {str(e)}")
            sys.exit(1)

if __name__ == "__main__":
    debug_mode = os.environ.get('DEBUG', 'False').lower() == 'true'
    creator = ClaudeRepoCreator(debug_mode=debug_mode)
    asyncio.run(creator.run())
