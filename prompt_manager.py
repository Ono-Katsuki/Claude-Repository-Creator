import os
import re
from typing import Dict, Any, List, Tuple

class PromptManager:
    def __init__(self, prompts_dir: str = 'prompts'):
        self.prompts_dir = prompts_dir
        self.prompts: Dict[str, Dict[str, str]] = {}
        self.default_placeholders: Dict[str, Dict[str, str]] = {
            'create_code_generation_prompt': {
                'tech_stack': 'The programming tech stack to use',
                'feature_info': 'Information about the features to implement',
                'file_name': 'The name of the file to generate',
                'file_content.type': 'The type of the file content',
                'file_content.description': 'Description of the file content',
                'file_content.properties': 'Properties of the file content',
                'format_methods(file_content.methods)': 'Formatted methods of the file content'
            },
            'create_json_requirements_prompt': {
                'project_description': 'Description of the project'
            },
            'create_json_update_prompt': {
                'project_description': 'Description of the project',
                'current_requirements': 'Current requirements of the project',
                'user_feedback': 'Feedback from the user'
            },
            'create_text_requirements_prompt': {
                'user_request': 'The request from the user'
            },
            'create_text_update_prompt': {
                'current_requirements': 'Current requirements of the project',
                'user_feedback': 'Feedback from the user'
            }
        }
        self._load_prompts()
        
    def _load_prompts(self):
        for role in os.listdir(self.prompts_dir):
            role_path = os.path.join(self.prompts_dir, role)
            if os.path.isdir(role_path):
                self.prompts[role] = {}
                for prompt_file in os.listdir(role_path):
                    if prompt_file.endswith('.md'):
                        prompt_name = os.path.splitext(prompt_file)[0]
                        prompt_path = os.path.join(role_path, prompt_file)
                        with open(prompt_path, 'r') as f:
                            content = f.read()
                        self.prompts[role][prompt_name] = content

    def _format_value(self, value: Any) -> str:
        if isinstance(value, list):
            return ', '.join(map(str, value))
        elif isinstance(value, dict):
            return ', '.join(f"{k}: {v}" for k, v in value.items())
        elif isinstance(value, (int, float, bool)):
            return str(value)
        elif value is None:
            return ''
        else:
            return str(value)

    def _resolve_nested_key(self, data: Dict[str, Any], key: str) -> Any:
        parts = key.split('.')
        for part in parts:
            if isinstance(data, dict) and part in data:
                data = data[part]
            elif hasattr(data, part):
                data = getattr(data, part)
            else:
                return None
        return data

    def format_methods(self, methods):
        formatted_methods = []
        for method in methods:
            if isinstance(method, dict):
                params = ", ".join(method.get('params', []))
                name = method.get('name', '')
                return_type = method.get('return_type', '')
                description = method.get('description', '')
            else:
                params = ", ".join(method.params)
                name = method.name
                return_type = method.return_type
                description = method.description
            
            formatted_method = f"{name}({params}) -> {return_type}: {description}"
            formatted_methods.append(formatted_method)
        return "\n".join(formatted_methods)

    def get_prompt(self, role: str, prompt_name: str, hierarchy_folder: str, **kwargs: Any) -> str:
        if role not in self.prompts:
            raise ValueError(f"Role '{role}' not found.")
        if prompt_name not in self.prompts[role]:
            raise ValueError(f"Prompt '{prompt_name}' not found for role '{role}'.")
        
        prompt = self.prompts[role][prompt_name]
        print(f"Original prompt: {prompt}")  # デバッグ用プリント
        
        # Add missing placeholders with XML tags
        if hierarchy_folder in self.default_placeholders:
            print(f"Checking placeholders for {hierarchy_folder}")  # デバッグ用プリント
            missing_placeholders = []
            for placeholder, description in self.default_placeholders[hierarchy_folder].items():
                print(f"Checking placeholder: {placeholder}")  # デバッグ用プリント
                if f"{{{placeholder}}}" not in prompt:
                    print(f"Placeholder {placeholder} is missing")  # デバッグ用プリント
                    xml_placeholder = f'<{placeholder}>{{{placeholder}}}</{placeholder}>'
                    missing_placeholders.append(f"{xml_placeholder} <!-- {description} -->")
            
            if missing_placeholders:
                print(f"Adding missing placeholders: {missing_placeholders}")  # デバッグ用プリント
                prompt += "\n" + "\n".join(missing_placeholders)
            else:
                print("No missing placeholders found")  # デバッグ用プリント
        else:
            print(f"No default placeholders defined for {hierarchy_folder}")  # デバッグ用プリント
        
        print(f"Prompt after adding placeholders: {prompt}")  # デバッグ用プリント
        
        # Replace placeholders in the prompt
        for key, value in kwargs.items():
            placeholder = f"{{{key}}}"
            if placeholder in prompt:
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        sub_placeholder = f"{{{key}.{sub_key}}}"
                        if sub_placeholder in prompt:
                            if isinstance(sub_value, list):
                                formatted_value = ', '.join(map(str, sub_value))
                            else:
                                formatted_value = self._format_value(sub_value)
                            prompt = prompt.replace(sub_placeholder, formatted_value)
                else:
                    formatted_value = self._format_value(value)
                    prompt = prompt.replace(placeholder, formatted_value)
        
        # Handle special cases for file_content
        if 'file_content' in kwargs:
            file_content = kwargs['file_content']
            for field in ['type', 'description', 'properties']:
                placeholder = f"{{file_content.{field}}}"
                if placeholder in prompt:
                    value = file_content.get(field, '')
                    if isinstance(value, list):
                        formatted_value = ', '.join(map(str, value))
                    else:
                        formatted_value = self._format_value(value)
                    prompt = prompt.replace(placeholder, formatted_value)
        
        # Handle special function calls
        if "{format_methods(file_content.methods)}" in prompt:
            methods = self._resolve_nested_key(kwargs, 'file_content.methods')
            if methods:
                methods_str = self.format_methods(methods)
                prompt = prompt.replace("{format_methods(file_content.methods)}", methods_str)
        
        print(f"Final prompt: {prompt}")  # デバッグ用プリント
        return prompt.strip()

    def list_prompts(self) -> List[Tuple[str, str]]:
        prompt_list = []
        for role in self.prompts:
            for prompt_name in self.prompts[role]:
                prompt_list.append((role, prompt_name))
        return prompt_list

    def get_prompt_content(self, role: str, prompt_name: str) -> str:
        if role not in self.prompts or prompt_name not in self.prompts[role]:
            raise ValueError(f"Prompt '{prompt_name}' not found for role '{role}'.")
        return self.prompts[role][prompt_name]

prompt_manager = PromptManager()
