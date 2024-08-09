import json

class ConfigManager:
    def __init__(self, config_file='config.json'):
        self.config_file = config_file

    def load_config(self):
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return self.create_default_config()

    def create_default_config(self):
        default_config = {
            'claude_api_key': '',
            'openai_api_key': '',
            'version_control': 'git',
            'cache_expiration': 3600  # 1時間
        }
        with open(self.config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        return default_config

    def save_config(self, config):
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)

    def update_api_key(self, api_type, new_key):
        config = self.load_config()
        if api_type == 'claude':
            config['claude_api_key'] = new_key
        elif api_type == 'openai':
            config['openai_api_key'] = new_key
        else:
            raise ValueError("Invalid API type. Use 'claude' or 'openai'.")
        self.save_config(config)

    def get_api_key(self, api_type):
        config = self.load_config()
        if api_type == 'claude':
            return config.get('claude_api_key', '')
        elif api_type == 'openai':
            return config.get('openai_api_key', '')
        else:
            raise ValueError("Invalid API type. Use 'claude' or 'openai'.")
