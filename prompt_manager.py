import os
import re
from typing import Dict, Any

class PromptManager:
    def __init__(self, prompts_dir: str = 'prompts'):
        self.prompts_dir = prompts_dir
        self.prompts: Dict[str, Dict[str, str]] = {}
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
        
        # Replace placeholders in the prompt
        for key, value in kwargs.items():
            placeholder = f"{{{key}}}"
            prompt = prompt.replace(placeholder, str(value))
        
        # Remove any remaining placeholders
        prompt = re.sub(r'\{[^}]*\}', '', prompt)
        
        return prompt.strip()
