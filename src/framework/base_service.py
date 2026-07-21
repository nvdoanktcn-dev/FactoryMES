from src.utils.logger import get_logger


class BaseService:

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

    def log_info(self, message):
        self.logger.info(message)

    def log_warning(self, message):
        self.logger.warning(message)

    def log_error(self, message):
        self.logger.error(message)