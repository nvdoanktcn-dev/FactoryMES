import json

from src.utils.paths import config_path


CONFIG_PATH = config_path()


class AppConfig:
    @staticmethod
    def load():
        with open(CONFIG_PATH, "r", encoding="utf-8") as file:
            return json.load(file)

    @staticmethod
    def get(key, default=None):
        config = AppConfig.load()
        return config.get(key, default)
