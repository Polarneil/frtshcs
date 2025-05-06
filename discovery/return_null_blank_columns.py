import pandas as pd


def find_empty_columns(csv_filepath):
    """
    Reads a CSV file and identifies columns that are entirely null or blank.

    Args:
        csv_filepath (str): The path to the CSV file.

    Returns:
        list: A list of column names that are completely empty.
              Returns an empty list if no empty columns are found or if there's an error.
    """
    try:
        df = pd.read_csv(csv_filepath)
        empty_columns = [col for col in df.columns if df[col].isnull().all()]
        return empty_columns
    except FileNotFoundError:
        print(f"Error: File not found at {csv_filepath}")
        return []
    except Exception as e:
        print(f"An error occurred: {e}")
        return []


if __name__ == "__main__":
    file_path = "netsuite.csv"
    empty_cols = find_empty_columns(file_path)

    if empty_cols:
        print("\nThe following columns are completely empty:")
        for col in empty_cols:
            print(f"- {col}")
    else:
        print("\nNo completely empty columns were found.")
