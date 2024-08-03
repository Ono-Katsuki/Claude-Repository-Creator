import os
from datetime import datetime

class RequirementsManager:
    def __init__(self, base_path):
        self.base_path = base_path

    def save_requirements(self, project_name, requirements, version=None):
        project_path = os.path.join(self.base_path, project_name)
        os.makedirs(project_path, exist_ok=True)

        if version is None:
            version = self.get_next_version(project_path)

        filename = f"requirements_v{version}.txt"
        file_path = os.path.join(project_path, filename)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(requirements)

        return version

    def get_next_version(self, project_path):
        existing_files = [f for f in os.listdir(project_path) if f.startswith("requirements_v") and f.endswith(".txt")]
        if not existing_files:
            return 1
        versions = [int(f.split('_v')[1].split('.')[0]) for f in existing_files]
        return max(versions) + 1

    def get_latest_requirements(self, project_name):
        project_path = os.path.join(self.base_path, project_name)
        if not os.path.exists(project_path):
            return None

        existing_files = [f for f in os.listdir(project_path) if f.startswith("requirements_v") and f.endswith(".txt")]
        if not existing_files:
            return None

        latest_file = max(existing_files, key=lambda f: int(f.split('_v')[1].split('.')[0]))
        file_path = os.path.join(project_path, latest_file)

        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def get_all_versions(self, project_name):
        project_path = os.path.join(self.base_path, project_name)
        if not os.path.exists(project_path):
            return []

        existing_files = [f for f in os.listdir(project_path) if f.startswith("requirements_v") and f.endswith(".txt")]
        return sorted(existing_files, key=lambda f: int(f.split('_v')[1].split('.')[0]))

    def get_requirements_by_version(self, project_name, version):
        project_path = os.path.join(self.base_path, project_name)
        file_path = os.path.join(project_path, f"requirements_v{version}.txt")

        if not os.path.exists(file_path):
            return None

        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
