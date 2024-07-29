import os
import logging
import shutil

logger = logging.getLogger(__name__)

class RepoGenerator:
    def __init__(self):
        self.gitignore_templates = {
            "python": [
                "*.pyc",
                "__pycache__/",
                "venv/",
                "*.egg-info/",
                "dist/",
                "build/",
            ],
            "javascript": [
                "node_modules/",
                "npm-debug.log",
                "yarn-error.log",
                "dist/",
                "*.log",
            ],
            "java": [
                "*.class",
                "*.jar",
                "target/",
                ".gradle/",
                "build/",
            ],
            "react": [
                "node_modules/",
                "build/",
                ".env",
                "*.log",
            ],
            "react native": [
                "node_modules/",
                ".expo/",
                "npm-debug.*",
                "*.jks",
                "*.p8",
                "*.p12",
                "*.key",
                "*.mobileprovision",
                "*.orig.*",
                "web-build/",
            ],
            "html": [
                "*.log",
                "*.tmp",
            ],
            "css": [
                "*.map",
                "*.css.map",
            ],
            "ruby": [
                "*.gem",
                "*.rbc",
                "/.config",
                "/coverage/",
                "/InstalledFiles",
                "/pkg/",
                "/spec/reports/",
                "/spec/examples.txt",
                "/test/tmp/",
                "/test/version_tmp/",
                "/tmp/",
                "/.yardoc/",
                "_yardoc/",
                "/doc/",
                "/rdoc/",
            ],
        }
        self.repo_folder = None

    def _normalize_language(self, language: str) -> str:
        """言語名を正規化します。"""
        language = language.lower()
        if language in ['react', 'react.js', 'reactjs']:
            return 'react'
        if language in ['react native', 'react-native', 'reactnative']:
            return 'react native'
        return language

    def create_repo_folder(self, project_name):
        """リポジトリ用の新しいフォルダを作成します"""
        self.repo_folder = os.path.join(os.getcwd(), project_name)
        os.makedirs(self.repo_folder, exist_ok=True)
        logger.info(f"新しいリポジトリフォルダを作成しました: {self.repo_folder}")

    def create_structure(self, structure, base_path=None):
        """フォルダ構造とファイルを作成します。"""
        base_path = base_path or self.repo_folder
        for folder, contents in structure.items():
            folder_path = os.path.join(base_path, folder)
            os.makedirs(folder_path, exist_ok=True)
            
            for file in contents.get("files", []):
                open(os.path.join(folder_path, file), 'w').close()
            
            self.create_structure(contents.get("subfolders", {}), folder_path)

    def create_readme(self, requirements):
        """プロジェクト情報を含むREADME.mdファイルを作成します。"""
        try:
            readme_path = os.path.join(self.repo_folder, "README.md")
            with open(readme_path, "w") as f:
                f.write(f"# {requirements['project_name']}\n\n")
                f.write(f"{requirements['description']}\n\n")
                f.write("## 機能\n\n")
                for feature in requirements['features']:
                    f.write(f"### {feature['name']}\n")
                    f.write(f"{feature['description']}\n\n")
                    f.write("受け入れ基準:\n")
                    for criteria in feature['acceptance_criteria']:
                        f.write(f"- {criteria}\n")
                    f.write("\n")
            logger.info("README.mdが正常に作成されました。")
        except IOError as e:
            logger.error(f"README.mdの作成中にエラーが発生しました: {str(e)}")

    def create_gitignore(self, tech_stack):
        """技術スタックに基づいて.gitignoreファイルを作成します。"""
        try:
            gitignore_path = os.path.join(self.repo_folder, ".gitignore")
            with open(gitignore_path, "w") as f:
                for tech in tech_stack:
                    tech_lower = self._normalize_language(tech)
                    if tech_lower in self.gitignore_templates:
                        f.write(f"# {tech}固有の無視パターン\n")
                        for pattern in self.gitignore_templates[tech_lower]:
                            f.write(f"{pattern}\n")
                        f.write("\n")
                f.write("# 一般的な無視パターン\n")
                f.write(".DS_Store\n")
                f.write(".idea/\n")
                f.write(".vscode/\n")
            logger.info(".gitignoreが正常に作成されました。")
        except IOError as e:
            logger.error(f".gitignoreの作成中にエラーが発生しました: {str(e)}")

    def get_current_structure(self, base_path=None):
        """現在のフォルダ構造を再帰的に取得します。"""
        base_path = base_path or self.repo_folder
        structure = {}
        for item in os.listdir(base_path):
            item_path = os.path.join(base_path, item)
            if os.path.isdir(item_path):
                structure[item] = {
                    "subfolders": self.get_current_structure(item_path),
                    "files": []
                }
            else:
                if "files" not in structure:
                    structure["files"] = []
                structure["files"].append(item)
        return structure

    def update_structure(self, current_structure, updated_structure, base_path=None):
        """更新された構造に基づいて既存の構造を更新します。"""
        base_path = base_path or self.repo_folder
        for folder, contents in updated_structure.items():
            folder_path = os.path.join(base_path, folder)
            if folder not in current_structure:
                os.makedirs(folder_path, exist_ok=True)
                logger.info(f"新しいフォルダを作成しました: {folder_path}")
            
            for file in contents.get("files", []):
                file_path = os.path.join(folder_path, file)
                if not os.path.exists(file_path):
                    open(file_path, 'w').close()
                    logger.info(f"新しいファイルを作成しました: {file_path}")
            
            self.update_structure(
                current_structure.get(folder, {}).get("subfolders", {}),
                contents.get("subfolders", {}),
                folder_path
            )
        
        # 更新された構造にないフォルダとファイルを削除
        for folder in current_structure:
            if folder not in updated_structure:
                folder_path = os.path.join(base_path, folder)
                shutil.rmtree(folder_path)
                logger.info(f"フォルダを削除しました: {folder_path}")

    def update_readme(self, requirements):
        """既存のREADME.mdファイルを更新します。"""
        try:
            readme_path = os.path.join(self.repo_folder, "README.md")
            if not os.path.exists(readme_path):
                return self.create_readme(requirements)
            
            with open(readme_path, "r+") as f:
                content = f.read()
                f.seek(0)
                f.write(f"# {requirements['project_name']}\n\n")
                f.write(f"{requirements['description']}\n\n")
                f.write("## 機能\n\n")
                for feature in requirements['features']:
                    f.write(f"### {feature['name']}\n")
                    f.write(f"{feature['description']}\n\n")
                    f.write("受け入れ基準:\n")
                    for criteria in feature['acceptance_criteria']:
                        f.write(f"- {criteria}\n")
                    f.write("\n")
                f.write(content.split("## 機能")[1] if "## 機能" in content else "")
                f.truncate()
            logger.info("README.mdが正常に更新されました。")
        except IOError as e:
            logger.error(f"README.mdの更新中にエラーが発生しました: {str(e)}")

    def update_gitignore(self, tech_stack):
        """既存の.gitignoreファイルを更新します。"""
        try:
            gitignore_path = os.path.join(self.repo_folder, ".gitignore")
            if not os.path.exists(gitignore_path):
                return self.create_gitignore(tech_stack)
            
            with open(gitignore_path, "r+") as f:
                content = f.read()
                f.seek(0)
                for tech in tech_stack:
                    tech_lower = self._normalize_language(tech)
                    if tech_lower in self.gitignore_templates:
                        f.write(f"# {tech}固有の無視パターン\n")
                        for pattern in self.gitignore_templates[tech_lower]:
                            f.write(f"{pattern}\n")
                        f.write("\n")
                f.write("# 一般的な無視パターン\n")
                f.write(".DS_Store\n")
                f.write(".idea/\n")
                f.write(".vscode/\n")
                f.write(content.split("# 一般的な無視パターン")[1] if "# 一般的な無視パターン" in content else "")
                f.truncate()
            logger.info(".gitignoreが正常に更新されました。")
        except IOError as e:
            logger.error(f".gitignoreの更新中にエラーが発生しました: {str(e)}")

    def create_feature_files(self, feature_name, feature_code, tech_stack):
        """適切なディレクトリに機能ファイルを作成します"""
        try:
            feature_dir = os.path.join(self.repo_folder, "src", "features", feature_name.lower().replace(' ', '_'))
            os.makedirs(feature_dir, exist_ok=True)
            
            language = self._normalize_language(tech_stack[0])
            file_extension = self._get_file_extension(language)
            main_file = os.path.join(feature_dir, f"main{file_extension}")
            with open(main_file, 'w') as f:
                f.write(feature_code)
            
            test_file = os.path.join(feature_dir, f"test{file_extension}")
            with open(test_file, 'w') as f:
                f.write(f"# TODO: {feature_name}のテストを実装する")
            
            logger.info(f"{feature_name}の機能ファイルが作成されました")
        except IOError as e:
            logger.error(f"{feature_name}の機能ファイル作成中にエラーが発生しました: {str(e)}")

    def _get_file_extension(self, language):
        extensions = {
            'python': '.py',
            'javascript': '.js',
            'react': '.jsx',
            'react native': '.js',
            'html': '.html',
            'css': '.css',
            'ruby': '.rb',
            'java': '.java'
        }
        return extensions.get(language, '.txt')
