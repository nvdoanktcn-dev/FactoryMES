import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
CONFIG_PATH = BASE_DIR / "config" / "app.json"


class AppConfig:
    @staticmethod
    def load():
        with open(CONFIG_PATH, "r", encoding="utf-8") as file:
            return json.load(file)

    @staticmethod
    def get(key, default=None):
        config = AppConfig.load()
        return config.get(key, default)