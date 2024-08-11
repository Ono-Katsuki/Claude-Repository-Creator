import os
import re
from typing import Dict, Any, List, Tuple


class PromptManager:
    def __init__(self, prompts_dir: str = 'prompts'):
        self.prompts_dir = prompts_dir
        self.prompts: Dict[str, Dict[str, str]] = {}
        self.required_variables: Dict[str, Dict[str, List[str]]] = {
            'create_code_generation_prompt': {'default': ['tech_stack', 'features', 'file_name', 'file_content']},
            'create_json_requirements_prompt': {'default': ['project_description']},
            'create_json_update_prompt': {'default': ['project_description', 'current_requirements', 'user_feedback']},
            'create_text_requirements_prompt': {'default': ['user_request']},
            'create_text_update_prompt': {'default': ['current_requirements', 'user_feedback']}
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
            return 'None'
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
                # Handle dictionary representation
                params = ", ".join(method.get('params', []))
                name = method.get('name', '')
                return_type = method.get('return_type', '')
                description = method.get('description', '')
            else:
                # Handle object representation
                params = ", ".join(method.params)
                name = method.name
                return_type = method.return_type
                description = method.description
            
            formatted_method = f"{name}({params}) -> {return_type}: {description}"
            formatted_methods.append(formatted_method)
        return "\n".join(formatted_methods)

    def _add_missing_content(self, prompt: str, key: str, value: Any) -> str:
        if isinstance(value, dict):
            for k, v in value.items():
                nested_key = f"{key}.{k}"
                if f"{{{nested_key}}}" not in prompt:
                    prompt = f"{nested_key}: {self._format_value(v)}\n\n{prompt}"
        elif isinstance(value, list) and key == 'file_content.methods':
            if "{format_methods(file_content.methods)}" not in prompt:
                methods_str = self.format_methods(value)
                prompt = f"{key}:\n{methods_str}\n\n{prompt}"
        elif f"{{{key}}}" not in prompt:
            prompt = f"{key}: {self._format_value(value)}\n\n{prompt}"
        return prompt

    def get_prompt(self, role: str, prompt_name: str, **kwargs: Any) -> str:
        if role not in self.prompts:
            raise ValueError(f"Role '{role}' not found.")
        if prompt_name not in self.prompts[role]:
            raise ValueError(f"Prompt '{prompt_name}' not found for role '{role}'.")
        
        prompt = self.prompts[role][prompt_name]
        
        # Replace placeholders in the prompt and add missing content
        for key, value in kwargs.items():
            placeholder = f"{{{key}}}"
            if placeholder in prompt:
                formatted_value = self._format_value(value)
                prompt = prompt.replace(placeholder, formatted_value)
            else:
                # If the placeholder doesn't exist, add missing content
                prompt = self._add_missing_content(prompt, key, value)
        
        # Handle special function calls
        if "{format_methods(file_content.methods)}" in prompt:
            methods = self._resolve_nested_key(kwargs, 'file_content.methods')
            if methods:
                methods_str = self.format_methods(methods)
                prompt = prompt.replace("{format_methods(file_content.methods)}", methods_str)
        
        # Remove any remaining unresolved placeholders
        prompt = re.sub(r'\{[^}]+\}', '', prompt)
        
        final_prompt = prompt.strip()                
        return final_prompt

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
