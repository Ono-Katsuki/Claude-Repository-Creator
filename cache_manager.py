import json
import time

class CacheManager:
    def __init__(self, cache_file='cache.json'):
        self.cache_file = cache_file
        self.cache = self.load_cache()

    def load_cache(self):
        try:
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_cache(self):
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f)

    def get(self, key):
        if key in self.cache:
            if time.time() - self.cache[key]['timestamp'] < self.cache[key]['expiration']:
                return self.cache[key]['data']
        return None

    def set(self, key, value, expiration=3600):
        self.cache[key] = {
            'data': value,
            'timestamp': time.time(),
            'expiration': expiration
        }
        self.save_cache()
