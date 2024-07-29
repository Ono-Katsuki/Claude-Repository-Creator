import os
import sys
import json
import logging
import tkinter as tk
from tkinter import scrolledtext
from claude_api import ClaudeAPI
from repo_generator import RepoGenerator
from config_manager import ConfigManager
from cache_manager import CacheManager
from version_control import VersionControlFactory
from code_generator import CodeGenerator
from code_tester import CodeTester

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClaudeRepoCreator:
    def __init__(self):
        self.config = ConfigManager().load_config()
        self.claude_api = ClaudeAPI(self.config['api_key'])
        self.repo_generator = RepoGenerator()
        self.cache_manager = CacheManager()
        self.vc_system = VersionControlFactory.create(self.config['version_control'])

    def generate_requirements(self, project_description):
        cache_key = f"requirements_{hash(project_description)}"
        cached_requirements = self.cache_manager.get(cache_key)
        if cached_requirements:
            return cached_requirements

        prompt = f"""
        以下のプロジェクト説明に基づいて、詳細な要件定義を作成してください：

        {project_description}

        要件を以下の構造のJSONフォーマットで提供してください：
        {{
            "project_name": "文字列",
            "description": "文字列",
            "features": [
                {{
                    "name": "文字列",
                    "description": "文字列",
                    "acceptance_criteria": ["文字列"]
                }}
            ],
            "tech_stack": ["文字列"],
            "folder_structure": {{
                "フォルダ名": {{
                    "subfolders": {{}},
                    "files": ["文字列"]
                }}
            }}
        }}
        """
        try:
            response = self.claude_api.generate_response(prompt)
            requirements = json.loads(response)
            self.cache_manager.set(cache_key, requirements)
            return requirements
        except Exception as e:
            logger.error(f"要件の生成中にエラーが発生しました: {str(e)}")
            raise

    def create_repository(self, requirements, update_existing=False):
        try:
            if update_existing:
                self.update_existing_repository(requirements)
            else:
                self.repo_generator.create_structure(requirements['folder_structure'])
                self.repo_generator.create_readme(requirements)
                self.repo_generator.create_gitignore(requirements['tech_stack'])
            
            for feature in requirements['features']:
                self.create_feature_files(feature, requirements['tech_stack'])

            self.vc_system.initialize(requirements['project_name'])
        except Exception as e:
            logger.error(f"リポジトリの作成中にエラーが発生しました: {str(e)}")
            raise

    def update_existing_repository(self, requirements):
        try:
            current_structure = self.repo_generator.get_current_structure()
            updated_structure = requirements['folder_structure']
            self.repo_generator.update_structure(current_structure, updated_structure)
            self.repo_generator.update_readme(requirements)
            self.repo_generator.update_gitignore(requirements['tech_stack'])
        except Exception as e:
            logger.error(f"既存のリポジトリの更新中にエラーが発生しました: {str(e)}")
            raise

    def create_feature_files(self, feature, tech_stack):
        try:
            code_generator = CodeGenerator(self.claude_api, tech_stack)
            feature_code = code_generator.generate_feature_code(feature)
            
            # コードの自動テスト
            code_tester = CodeTester(tech_stack)
            test_result = code_tester.test_code(feature_code)
            
            if test_result['success']:
                # ユーザーにコードを表示し、編集を許可
                edited_code = self.show_code_editor(feature['name'], feature_code)
                self.repo_generator.create_feature_files(feature['name'], edited_code)
            else:
                logger.error(f"生成されたコードにエラーがあります: {test_result['message']}")
                # エラーメッセージをユーザーに表示し、手動での修正を促す
                self.show_error_message(test_result['message'])
        except Exception as e:
            logger.error(f"機能ファイルの作成中にエラーが発生しました: {str(e)}")
            raise

    def show_code_editor(self, feature_name, code):
        root = tk.Tk()
        root.title(f"コードエディタ - {feature_name}")
        
        editor = scrolledtext.ScrolledText(root, width=100, height=30)
        editor.insert(tk.INSERT, code)
        editor.pack()

        edited_code = [code]  # リストを使用して参照渡しをシミュレート

        def save_and_exit():
            edited_code[0] = editor.get("1.0", tk.END)
            root.quit()

        save_button = tk.Button(root, text="保存して閉じる", command=save_and_exit)
        save_button.pack()

        root.mainloop()
        root.destroy()

        return edited_code[0]

    def show_error_message(self, message):
        root = tk.Tk()
        root.title("エラー")
        
        label = tk.Label(root, text=message)
        label.pack(padx=20, pady=20)

        ok_button = tk.Button(root, text="OK", command=root.destroy)
        ok_button.pack(pady=10)

        root.mainloop()

    def run(self):
        try:
            project_description = input("プロジェクトの説明を入力してください: ")
            requirements = self.generate_requirements(project_description)
            
            update_existing = input("既存のリポジトリを更新しますか？ (y/n): ").lower() == 'y'
            self.create_repository(requirements, update_existing)
            
            print(f"プロジェクト: {requirements['project_name']} のリポジトリが正常に{'更新' if update_existing else '作成'}されました。")
        except Exception as e:
            logger.error(f"プログラムの実行中にエラーが発生しました: {str(e)}")
            sys.exit(1)

if __name__ == "__main__":
    creator = ClaudeRepoCreator()
    creator.run()
