from abc import ABC, abstractmethod
import subprocess
import os

class VersionControl(ABC):
    @abstractmethod
    def initialize(self, project_path):
        pass

    @abstractmethod
    def add_all(self):
        pass

    @abstractmethod
    def commit(self, message):
        pass

class Git(VersionControl):
    def __init__(self):
        self.repo_path = None

    def initialize(self, project_path):
        self.repo_path = project_path
        subprocess.run(["git", "init", self.repo_path], check=True)

    def add_all(self):
        if not self.repo_path:
            raise ValueError("Repository not initialized")
        subprocess.run(["git", "-C", self.repo_path, "add", "."], check=True)

    def commit(self, message):
        if not self.repo_path:
            raise ValueError("Repository not initialized")
        subprocess.run(["git", "-C", self.repo_path, "commit", "-m", message], check=True)

class Mercurial(VersionControl):
    def __init__(self):
        self.repo_path = None

    def initialize(self, project_path):
        self.repo_path = project_path
        subprocess.run(["hg", "init", self.repo_path], check=True)

    def add_all(self):
        if not self.repo_path:
            raise ValueError("Repository not initialized")
        subprocess.run(["hg", "-R", self.repo_path, "add"], check=True)

    def commit(self, message):
        if not self.repo_path:
            raise ValueError("Repository not initialized")
        subprocess.run(["hg", "-R", self.repo_path, "commit", "-m", message], check=True)

class VersionControlFactory:
    @staticmethod
    def create(vc_type):
        if vc_type.lower() == 'git':
            return Git()
        elif vc_type.lower() == 'mercurial':
            return Mercurial()
        else:
            raise ValueError(f"Unsupported version control system: {vc_type}")
