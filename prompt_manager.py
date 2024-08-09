import os
import re
from typing import Dict, Any, List, Tuple

class PromptManager:
    def __init__(self, prompts_dir: str = 'prompts'):
        self.prompts_dir = prompts_dir
        self.prompts: Dict[str, Dict[str, str]] = {}
        self.required_variables: Dict[str, Dict[str, List[str]]] = {
            'create_code_generation_prompt': {'default': ['language', 'feature_info', 'file_name', 'file_content.type', 'file_content.description', 'file_content.properties', 'file_content.methods']},
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

    def get_prompt(self, role: str, prompt_name: str, **kwargs: Any) -> str:
        if role not in self.prompts:
            raise ValueError(f"Role '{role}' not found.")
        if prompt_name not in self.prompts[role]:
            raise ValueError(f"Prompt '{prompt_name}' not found for role '{role}'.")
        
        prompt = self.prompts[role][prompt_name]
        
        # Add only missing required variables with clear format
        if role in self.required_variables and prompt_name in self.required_variables[role]:
            required_vars = self.required_variables[role][prompt_name]
            existing_vars = set(re.findall(r'\{([^}]*)\}', prompt))
            missing_vars = set(required_vars) - existing_vars
            if missing_vars:
                variable_section = "\n".join([f"{var}: {{{var}}}" for var in missing_vars])
                prompt = f"{variable_section}\n\n{prompt}"
        
        # Replace placeholders in the prompt
        for key, value in kwargs.items():
            placeholder = f"{{{key}}}"
            if placeholder in prompt:
                prompt = prompt.replace(placeholder, str(value))
            else:
                # If the placeholder doesn't exist, add it at the beginning with the clear format
                prompt = f"{key}: {value}\n\n{prompt}"
        
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
