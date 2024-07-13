import os
import tomllib


def load_config(config_path="config.toml"):
    with open(config_path, 'rb') as f:
        config = tomllib.load(f)
    return config['default']

config_path = os.path.join(os.path.dirname(__file__), '..', 'config.toml')

CONFIG = load_config(config_path)
