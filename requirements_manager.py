import os
import json
from datetime import datetime

class RequirementsManager:
    def __init__(self, base_path, cache_path):
        self.base_path = base_path
        self.cache_path = cache_path

    def save_requirements(self, project_name, requirements, is_json=False, version=None):
        project_path = os.path.join(self.base_path, project_name)
        cache_project_path = os.path.join(self.cache_path, project_name)
        os.makedirs(project_path, exist_ok=True)
        os.makedirs(cache_project_path, exist_ok=True)

        if version is None:
            version = self.get_next_version(project_path if not is_json else cache_project_path, is_json)

        if is_json:
            filename = f"requirements_v{version}.json"
            file_path = os.path.join(cache_project_path, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(requirements, f, ensure_ascii=False, indent=2)
        else:
            filename = f"requirements_v{version}.txt"
            file_path = os.path.join(project_path, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(requirements)

        return version

    def get_next_version(self, project_path, is_json=False):
        extension = ".json" if is_json else ".txt"
        existing_files = [f for f in os.listdir(project_path) if f.startswith("requirements_v") and f.endswith(extension)]
        if not existing_files:
            return 1
        versions = [int(f.split('_v')[1].split('.')[0]) for f in existing_files]
        return max(versions) + 1

    def get_latest_requirements(self, project_name, is_json=False):
        path = os.path.join(self.cache_path if is_json else self.base_path, project_name)
        if not os.path.exists(path):
            return None

        extension = ".json" if is_json else ".txt"
        existing_files = [f for f in os.listdir(path) if f.startswith("requirements_v") and f.endswith(extension)]
        if not existing_files:
            return None

        latest_file = max(existing_files, key=lambda f: int(f.split('_v')[1].split('.')[0]))
        file_path = os.path.join(path, latest_file)

        if is_json:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()

    def get_all_versions(self, project_name, is_json=False):
        path = os.path.join(self.cache_path if is_json else self.base_path, project_name)
        if not os.path.exists(path):
            return []

        extension = ".json" if is_json else ".txt"
        existing_files = [f for f in os.listdir(path) if f.startswith("requirements_v") and f.endswith(extension)]
        return sorted(existing_files, key=lambda f: int(f.split('_v')[1].split('.')[0]))

    def get_requirements_by_version(self, project_name, version, is_json=False):
        path = os.path.join(self.cache_path if is_json else self.base_path, project_name)
        extension = ".json" if is_json else ".txt"
        file_path = os.path.join(path, f"requirements_v{version}{extension}")

        if not os.path.exists(file_path):
            return None

        if is_json:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
