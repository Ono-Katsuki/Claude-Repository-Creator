import os
import logging

logger = logging.getLogger(__name__)

class MarkdownGenerator:
    @staticmethod
    def create_project_summary(requirements, repo_folder, output_path):
        summary_content = f"# {requirements['project_name']}\n\n"
        summary_content += f"## Project Description\n{requirements['description']}\n\n"
        summary_content += "## Features\n"
        for feature in requirements['features']:
            summary_content += f"### {feature['name']}\n"
            summary_content += f"{feature['description']}\n\n"
            summary_content += "Acceptance Criteria:\n"
            for criteria in feature['acceptance_criteria']:
                summary_content += f"- {criteria}\n"
            summary_content += "\n"
        summary_content += f"## Tech Stack\n{', '.join(requirements['tech_stack'])}\n\n"
        summary_content += "## Folder Structure\n"
        summary_content += MarkdownGenerator.generate_folder_structure_markdown(requirements['folder_structure'])
        
        summary_content += "\n## Full Project Code\n"
        summary_content += MarkdownGenerator.generate_full_code_markdown(repo_folder)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(summary_content)
        
        logger.info(f"Project summary with full code created and saved to: {output_path}")

    @staticmethod
    def generate_folder_structure_markdown(structure, indent=""):
        markdown = ""
        for folder, contents in structure.items():
            markdown += f"{indent}- {folder}/\n"
            if "files" in contents:
                for file in contents["files"]:
                    markdown += f"{indent}  - {file['name']}\n"
            if "subfolders" in contents:
                markdown += MarkdownGenerator.generate_folder_structure_markdown(contents["subfolders"], indent + "  ")
        return markdown

    @staticmethod
    def generate_full_code_markdown(root_folder):
        markdown = ""
        for root, dirs, files in os.walk(root_folder):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, root_folder)
                markdown += f"### {relative_path}\n\n"
                markdown += "```\n"
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        markdown += f.read()
                except Exception as e:
                    markdown += f"Error reading file: {str(e)}"
                markdown += "\n```\n\n"
        return markdown
