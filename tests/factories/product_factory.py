import pandas as pd


class DataFrameFactory:

    @staticmethod
    def products(*rows):
        return pd.DataFrame(list(rows))

    @staticmethod
    def machines(*rows):
        return pd.DataFrame(list(rows))

    @staticmethod
    def employees(*rows):
        return pd.DataFrame(list(rows))