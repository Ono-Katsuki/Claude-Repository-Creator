import os
import asyncio
from tqdm import tqdm
from code_generator import CodeGenerator
import logging

logger = logging.getLogger(__name__)

class RepositoryCreator:
    def __init__(self, api_key):
        self.api_key = api_key

    async def create_repository(self, requirements, update_existing, current_project_folder, repo_generator, vc_system):
        try:
            project_name = requirements['project_name']
            repo_generator.create_repo_folder(current_project_folder)
            
            if update_existing:
                await self.update_existing_repository(requirements, repo_generator)
            else:
                repo_generator.create_structure(requirements['folder_structure'])
                repo_generator.create_readme(requirements)
                repo_generator.create_gitignore(requirements['tech_stack'])
            
            await self.create_feature_files(requirements['features'], requirements['tech_stack'], requirements['folder_structure'], repo_generator)
            
            vc_system.initialize(repo_generator.repo_folder)
            vc_system.add_all()
            vc_system.commit("Initial commit")
            
            print(f"Repository for project: {project_name} has been {'updated' if update_existing else 'created'} successfully in folder: {repo_generator.repo_folder}")
        except Exception as e:
            print(f"Error creating repository: {str(e)}")
            raise

    async def update_existing_repository(self, requirements, repo_generator):
        try:
            current_structure = repo_generator.get_current_structure()
            updated_structure = requirements['folder_structure']
            repo_generator.update_structure(current_structure, updated_structure)
            repo_generator.update_readme(requirements)
            repo_generator.update_gitignore(requirements['tech_stack'])
        except Exception as e:
            print(f"Error updating existing repository: {str(e)}")
            raise

    async def create_feature_files(self, features, tech_stack, folder_structure, repo_generator):
        try:
            code_generator = CodeGenerator(self.api_key, tech_stack)
            
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

            tasks = await process_structure(folder_structure, repo_generator.repo_folder)
            
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
