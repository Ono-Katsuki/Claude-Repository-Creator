from abc import ABC, abstractmethod
import subprocess

class VersionControl(ABC):
    @abstractmethod
    def initialize(self, project_name):
        pass

class Git(VersionControl):
    def initialize(self, project_name):
        subprocess.run(["git", "init", project_name])
        subprocess.run(["git", "add", "."])
        subprocess.run(["git", "commit", "-m", "Initial commit"])

class Mercurial(VersionControl):
    def initialize(self, project_name):
        subprocess.run(["hg", "init", project_name])
        subprocess.run(["hg", "add"])
        subprocess.run(["hg", "commit", "-m", "Initial commit"])

class VersionControlFactory:
    @staticmethod
    def create(vc_type):
        if vc_type.lower() == 'git':
            return Git()
        elif vc_type.lower() == 'mercurial':
            return Mercurial()
        else:
            raise ValueError(f"Unsupported version control system: {vc_type}")
