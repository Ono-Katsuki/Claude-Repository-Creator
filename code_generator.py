import anthropic
import asyncio
import logging
import re
import os
from typing import Dict, List, Optional
from tqdm import tqdm
from repository_models import Requirements, Feature, File, Folder, FileContent
from prompts import create_code_generation_prompt, create_code_generation_system_prompt

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

    async def generate_feature_code(self, feature: Optional[Feature], file_content: FileContent, file_name: str, max_retries: int = 3) -> Optional[str]:
        language = self._normalize_language(self.tech_stack[0])

        prompt = create_code_generation_prompt(feature, file_content, file_name, language)
        system_prompt = create_code_generation_system_prompt(language)

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
                logger.warning(f"No valid code found in response for {file_name} (attempt {attempt + 1}/{max_retries})")
            except Exception as e:
                logger.error(f"Error occurred during code generation for {file_name} (attempt {attempt + 1}/{max_retries}): {str(e)}")
            
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        logger.error(f"Failed to generate code for {file_name} after {max_retries} attempts")
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

    def write_code_to_file(self, file_path: str, code: str) -> None:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(code)
            logger.info(f"Code written to file: {file_path}")
        except IOError as e:
            logger.error(f"Error writing code to file {file_path}: {str(e)}")
            raise

    def get_supported_languages(self) -> List[str]:
        return self.tech_stack

    def get_file_extension(self, language: str) -> str:
        extensions = {
            'python': '.py',
            'java': '.java',
            'javascript': '.js',
            'html': '.html',
            'css': '.css',
            'ruby': '.rb',
            'react': '.jsx',
            'react native': '.js',
        }
        normalized_language = self._normalize_language(language)
        return extensions.get(normalized_language, '.txt')

    async def generate_code_for_features(self, requirements: Requirements) -> Dict[str, Optional[str]]:
        async def process_folder(folder: Folder, feature: Optional[Feature] = None) -> Dict[str, Optional[str]]:
            results = {}
            for file in folder.files:
                if not self._is_image_or_audio_file(file.name):
                    file_feature = feature or next((f for f in requirements.features if f.name.lower().replace(' ', '_') == folder.name), None)
                    code = await self.generate_feature_code(file_feature, file.content, file.name)
                    results[file.name] = code

            for subfolder in folder.subfolders:
                subfolder_results = await process_folder(subfolder, feature)
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
            code_results = await self.generate_code_for_features(requirements)
            logger.info(f"Code generation completed for project: {requirements.project_name}")
            return code_results
        except Exception as e:
            logger.error(f"Error during project code generation: {str(e)}")
            raise
