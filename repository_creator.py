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

    async def create_repository(self, requirements: Requirements, update_existing: bool, project_path: str, repository_generator: Any, vc_system: Any) -> str:
        try:
            project_name = requirements.project_name
            repository_generator.create_repo_folder(project_path)
            
            if update_existing:
                await self.update_existing_repository(requirements, repository_generator)
            else:
                repository_generator.create_structure(requirements.folder_structure)
                repository_generator.create_readme(requirements)
                repository_generator.create_gitignore(requirements.tech_stack)
            
            await self.create_feature_files(requirements, repository_generator, project_path)
            
            vc_system.initialize(project_path)
            vc_system.add_all()
            vc_system.commit("Initial commit")
            
            logger.info(f"Repository for project: {project_name} has been {'updated' if update_existing else 'created'} successfully in folder: {repository_generator.repo_folder}")
        except Exception as e:
            logger.error(f"Error creating repository: {str(e)}")
            raise

    async def update_existing_repository(self, requirements: Requirements, repository_generator: Any):
        try:
            current_structure = repository_generator.get_current_structure()
            updated_structure = requirements.folder_structure
            repository_generator.update_structure(current_structure, updated_structure)
            repository_generator.update_readme(requirements)
            repository_generator.update_gitignore(requirements.tech_stack)
        except Exception as e:
            logger.error(f"Error updating existing repository: {str(e)}")
            raise

    async def create_feature_files(self, requirements: Requirements, repository_generator: Any, project_path: str):
        try:
            code_generator = CodeGenerator(self.api_key, requirements.tech_stack)
            
            # Generate code for the entire project
            code_results = await code_generator.generate_project_code(requirements)

            # Write generated code to files
            for file_path, code in code_results.items():
                if code is not None:
                    full_path = os.path.join(project_path, file_path)
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
