import requests

class ClaudeAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.anthropic.com/v1"

    def generate_response(self, prompt):
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key,
        }
        data = {
            "prompt": prompt,
            "max_tokens_to_sample": 1000,
            "model": "claude-v1.3",
        }
        response = requests.post(f"{self.base_url}/completions", headers=headers, json=data)
        response.raise_for_status()
        return response.json()["completion"]
