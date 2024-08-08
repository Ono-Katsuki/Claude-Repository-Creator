import os
import asyncio
from tqdm import tqdm
from typing import Dict, Any
import logging
from code_generator import CodeGenerator
from repository_models import Requirements, Feature, Folder, File

logger = logging.getLogger(__name__)

class RepositoryCreator:
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def create_repository(self, requirements: Requirements, update_existing: bool, current_project_folder: str, repo_generator: Any, vc_system: Any):
        try:
            project_name = requirements.project_name
            repo_generator.create_repo_folder(current_project_folder)
            
            if update_existing:
                await self.update_existing_repository(requirements, repo_generator)
            else:
                repo_generator.create_structure(requirements.folder_structure)
                repo_generator.create_readme(requirements)
                repo_generator.create_gitignore(requirements.tech_stack)
            
            await self.create_feature_files(requirements.features, requirements.tech_stack, requirements.folder_structure, repo_generator)
            
            vc_system.initialize(repo_generator.repo_folder)
            vc_system.add_all()
            vc_system.commit("Initial commit")
            
            logger.info(f"Repository for project: {project_name} has been {'updated' if update_existing else 'created'} successfully in folder: {repo_generator.repo_folder}")
        except Exception as e:
            logger.error(f"Error creating repository: {str(e)}")
            raise

    async def update_existing_repository(self, requirements: Requirements, repo_generator: Any):
        try:
            current_structure = repo_generator.get_current_structure()
            updated_structure = requirements.folder_structure
            repo_generator.update_structure(current_structure, updated_structure)
            repo_generator.update_readme(requirements)
            repo_generator.update_gitignore(requirements.tech_stack)
        except Exception as e:
            logger.error(f"Error updating existing repository: {str(e)}")
            raise

    async def create_feature_files(self, features: List[Feature], tech_stack: List[str], folder_structure: Folder, repo_generator: Any):
        try:
            code_generator = CodeGenerator(self.api_key, tech_stack)
            
            async def generate_code(file: File, file_path: str, feature: Feature = None):
                try:
                    feature_code = await code_generator.generate_feature_code(feature, file.content)
                    if feature_code is None:
                        return file.name, None
                    
                    code_generator.write_code_to_file(file_path, feature_code)
                    return file.name, file_path
                except Exception as e:
                    logger.error(f"Error processing file {file.name}: {str(e)}")
                    return file.name, None

            async def process_structure(structure: Folder, base_path: str):
                tasks = []
                for subfolder in structure.subfolders:
                    folder_path = os.path.join(base_path, subfolder.name)
                    os.makedirs(folder_path, exist_ok=True)
                    
                    for file in subfolder.files:
                        file_path = os.path.join(folder_path, file.name)
                        feature = self._get_feature_for_file(features, file.name)
                        tasks.append(generate_code(file, file_path, feature))
                    
                    subfolder_tasks = await process_structure(subfolder, folder_path)
                    tasks.extend(subfolder_tasks)
                
                return tasks

            tasks = await process_structure(folder_structure, repo_generator.repo_folder)
            
            logger.info(f"Starting to generate {len(tasks)} files")
            results = []
            for future in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Generating Files"):
                result = await future
                results.append(result)
            
            logger.info("All files generated successfully")
            return dict(results)
        except Exception as e:
            logger.error(f"Error creating files: {str(e)}")
            raise

    def _get_feature_for_file(self, features: List[Feature], file_name: str) -> Feature:
        for feature in features:
            feature_name = feature.name.lower().replace(' ', '_')
            if file_name.lower().startswith(feature_name):
                return feature
        return None
