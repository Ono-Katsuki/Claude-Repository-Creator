import os
import asyncio
from tqdm import tqdm
from typing import Dict, Any, List 
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
            
            await self.create_feature_files(requirements, repo_generator)
            
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

    async def create_feature_files(self, requirements: Requirements, repo_generator: Any):
        try:
            code_generator = CodeGenerator(self.api_key, requirements.tech_stack)
            
            # Generate code for the entire project
            code_results = await code_generator.generate_project_code(requirements)

            # Write generated code to files
            for file_path, code in code_results.items():
                if code is not None:
                    full_path = os.path.join(repo_generator.repo_folder, file_path)
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    code_generator.write_code_to_file(full_path, code)

            logger.info(f"Generated and wrote code for {len(code_results)} files")
            return code_results
        except Exception as e:
            logger.error(f"Error creating files: {str(e)}")
            raise

    def _get_feature_for_file(self, features: List[Feature], file_name: str) -> Feature:
        for feature in features:
            feature_name = feature.name.lower().replace(' ', '_')
            if file_name.lower().startswith(feature_name):
                return feature
        return None
