import pandas as pd


class DataFrameFactory:

    @staticmethod
    def from_records(records):
        return pd.DataFrame(records)

    @staticmethod
    def single(record):
        return pd.DataFrame([record])

    @staticmethod
    def empty(columns):
        return pd.DataFrame(columns=columns)