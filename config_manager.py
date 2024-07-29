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
            'api_key': '',
            'version_control': 'git',
            'cache_expiration': 3600  # 1時間
        }
        with open(self.config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        return default_config

    def save_config(self, config):
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
