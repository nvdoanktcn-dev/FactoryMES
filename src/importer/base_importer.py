from abc import ABC, abstractmethod


class BaseImporter(ABC):
    @abstractmethod
    def load_file(self, filename):
        pass

    @abstractmethod
    def clean_data(self, dataframe):
        pass

    @abstractmethod
    def validate_data(self, dataframe):
        pass

    @abstractmethod
    def save(self, dataframe):
        pass