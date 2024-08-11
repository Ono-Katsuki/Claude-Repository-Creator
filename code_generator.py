import anthropic
import asyncio
import logging
import re
import os
from typing import Dict, List, Optional, Tuple
from tqdm import tqdm
from repository_models import Requirements, Feature, File, Folder, FileContent
from prompt_manager import prompt_manager

logger = logging.getLogger(__name__)

class CodeGenerator:
    def __init__(self, api_key: str, tech_stack: List[str]):
        self.api_key = api_key
        self.tech_stack = [self._normalize_language(lang) for lang in tech_stack]
        self.client = anthropic.AsyncAnthropic(api_key=self.api_key)

    def _normalize_language(self, language: str) -> str:
        language = language.lower()
        if language in ['react', 'react.js', 'reactjs']:
            return 'react'
        if language in ['react native', 'react-native', 'reactnative']:
            return 'react native'
        return language

    def _select_prompt(self, prompt_category):
        prompts = prompt_manager.list_prompts()
        category_prompts = [p for p in prompts if p[0] == prompt_category]
        
        print(f"\nAvailable {prompt_category} prompts:")
        for i, (_, name) in enumerate(category_prompts, 1):
            print(f"{i}. {name}.md")
        
        while True:
            try:
                choice = int(input("Enter the number of the prompt you want to use: ")) - 1
                if 0 <= choice < len(category_prompts):
                    return category_prompts[choice][1]
                else:
                    print("Invalid choice. Please try again.")
            except ValueError:
                print("Please enter a number.")

    def _features_to_text(self, features: List[Feature]) -> str:
        feature_texts = []
        for feature in features:
            feature_text = f"Feature: {feature.name}\n"
            feature_text += f"Description: {feature.description}\n"
            feature_text += "Acceptance Criteria:\n"
            for criterion in feature.acceptance_criteria:
                feature_text += f"- {criterion}\n"
            feature_texts.append(feature_text)
        return "\n".join(feature_texts)
        
    async def generate_feature_code(self, features: List[Feature], file: File, prompts: Tuple[str, str], max_retries: int = 3) -> Optional[str]:
        code_prompt_name, system_prompt_name = prompts

        features_text = self._features_to_text(features)

        prompt = prompt_manager.get_prompt('create_code_generation_prompt', code_prompt_name, 
                                           tech_stack=self.tech_stack,
                                           features=features_text,
                                           file_name=file.name,
                                           file_content=file.content.model_dump() if file.content else None)
        
        # Print the final prompt for debugging
        print("===== Final Prompt =====")
        print(prompt)
        print("===== End of Prompt =====")
        
        system_prompt = prompt_manager.get_prompt('create_code_generation_system_prompt', system_prompt_name, tech_stack=self.tech_stack)

        for attempt in range(max_retries):
            try:
                message = await self.client.messages.create(
                    model="claude-3-5-sonnet-20240620",
                    max_tokens=4096,
                    temperature=0,
                    system=system_prompt,
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
                processed_code = self._process_code_response(response)
                if processed_code:
                    return processed_code
                logger.warning(f"No valid code found in response for {file.name} (attempt {attempt + 1}/{max_retries})")
            except Exception as e:
                logger.error(f"Error occurred during code generation for {file.name} (attempt {attempt + 1}/{max_retries}): {str(e)}")
            
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        logger.error(f"Failed to generate code for {file.name} after {max_retries} attempts")
        return None

    def _process_code_response(self, response: str) -> Optional[str]:
        code = re.sub(r'```[\w]*\n|```', '', response).strip()
        
        if not code:
            return None
        
        code = code.strip()
        
        lines = code.split('\n')
        clean_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(('/*', '*', '*/', '//', '#', '"""', "'''")):
                clean_lines.append(line)
            elif stripped:
                clean_lines.append(line)
                break
        
        clean_lines.extend(lines[len(clean_lines):])
        
        return '\n'.join(clean_lines)

    def get_supported_languages(self) -> List[str]:
        return self.tech_stack

    def get_file_extension(self, file_name: str) -> str:
        _, ext = os.path.splitext(file_name)
        if ext:
            return ext
        # If no extension, try to infer from the tech stack
        for lang in self.tech_stack:
            if lang in ['python', 'py']:
                return '.py'
            elif lang in ['javascript', 'js', 'typescript', 'ts']:
                return '.js'
            elif lang in ['java']:
                return '.java'
            elif lang in ['html']:
                return '.html'
            elif lang in ['css']:
                return '.css'
            elif lang in ['ruby', 'rb']:
                return '.rb'
            elif lang in ['react']:
                return '.jsx'
            elif lang in ['react native']:
                return '.js'
            # Add more language-specific extensions as needed
        return ''  # Default to empty string if unable to determine

    async def generate_code_for_features(self, requirements: Requirements, prompts: Tuple[str, str]) -> Dict[str, Optional[str]]:
        async def process_folder(folder: Folder, path: str = "") -> Dict[str, Optional[str]]:
            results = {}
            for file in folder.files:
                if not self._is_image_or_audio_file(file.name):
                    file_path = os.path.join(path, file.name)
                    code = await self.generate_feature_code(requirements.features, file, prompts)
                    results[file_path] = code
            for subfolder in folder.subfolders:
                subfolder_path = os.path.join(path, subfolder.name)
                subfolder_results = await process_folder(subfolder, subfolder_path)
                results.update(subfolder_results)
            return results

        total_files = self._count_valid_files(requirements.folder_structure)
        
        with tqdm(total=total_files, desc="Generating Code", unit="file") as pbar:
            async def generate_with_progress(folder: Folder) -> Dict[str, Optional[str]]:
                folder_results = await process_folder(folder)
                pbar.update(len(folder_results))
                return folder_results

            results = await generate_with_progress(requirements.folder_structure)

        return results

    def _is_image_or_audio_file(self, filename: str) -> bool:
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg']
        audio_extensions = ['.mp3', '.wav', '.ogg', '.flac', '.aac']
        _, ext = os.path.splitext(filename.lower())
        return ext in image_extensions or ext in audio_extensions

    def _count_valid_files(self, folder: Folder) -> int:
        count = sum(1 for file in folder.files if not self._is_image_or_audio_file(file.name))
        for subfolder in folder.subfolders:
            count += self._count_valid_files(subfolder)
        return count

    async def generate_project_code(self, requirements: Requirements) -> Dict[str, Optional[str]]:
        try:
            logger.info(f"Starting code generation for project: {requirements.project_name}")
            
            # Select prompts
            code_prompt_name = self._select_prompt('create_code_generation_prompt')
            system_prompt_name = self._select_prompt('create_code_generation_system_prompt')
            prompts = (code_prompt_name, system_prompt_name)
            
            # Generate code using the selected prompts
            code_results = await self.generate_code_for_features(requirements, prompts)
            
            logger.info(f"Code generation completed for project: {requirements.project_name}")
            return code_results
        except Exception as e:
            logger.error(f"Error during project code generation: {str(e)}")
            raise

    def write_code_to_file(self, file_path: str, code: str):
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w') as f:
                f.write(code)
            logger.info(f"Successfully wrote code to file: {file_path}")
        except Exception as e:
            logger.error(f"Error writing code to file {file_path}: {str(e)}")
            raise
