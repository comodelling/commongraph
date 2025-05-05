import json
import os

def load_metamodel_config():
    config_path = os.path.join(os.path.dirname(__file__), "metamodel-config.json")
    with open(config_path, "r") as f:
        return json.load(f)

METAMODEL_CONFIG = load_metamodel_config()