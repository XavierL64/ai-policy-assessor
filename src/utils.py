import pandas as pd

def load_exceptions(csv_path):
    """
    Loads exceptions from a CSV file and returns a list of dictionaries.
    Cleans non-breaking spaces and converts NaN to None.
    Each dictionary contains 'exception_id', 'exception_definition', and 'mitigant_definition' for one exception.
    """
    df = pd.read_csv(csv_path, encoding='utf-8')
    df = df.where(pd.notnull(df), None)
    df = df.map(lambda x: x.replace("\xa0", " ").strip() if isinstance(x, str) else x)

    return df[["exception_id", "exception_definition", "mitigant_definition"]].to_dict(orient="records")

def load_criteria(criteria_id, csv_path):
    """
    Loads a single criterion from a CSV file based on its ID.
    Returns a dictionary with 'criteria_description' and 'criteria_guidelines'.
    """
    df = pd.read_csv(csv_path, encoding='utf-8')
    criteria = df[df['criteria_id'] == criteria_id]
    criteria_description = criteria['criteria_description']
    criteria_guidelines = criteria['criteria_guidelines']

    return {
        'criteria_description': criteria['criteria_description'].iloc[0],
        'criteria_guidelines': criteria['criteria_guidelines'].iloc[0]
    }
   



