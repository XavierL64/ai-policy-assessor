import pandas as pd

def load_exceptions(csv_path):
    """
    Loads exceptions from a CSV file and returns a list of dictionaries.
    Each dictionary contains 'exception_id', 'exception_definition', and 'mitigant_definition' for one exception.
    """
    df = pd.read_csv(csv_path, encoding='utf-8')
    return df[["exception_id", "exception_definition", "mitigant_definition"]].to_dict(orient="records")

load_exceptions("../exceptions/exceptions.csv")



