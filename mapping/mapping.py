import os
import csv
import requests
from dotenv import load_dotenv

load_dotenv()

LITELLM_API_BASE = os.getenv("PROXY_URL")
VIRTUAL_TOKEN = os.getenv("VIRTUAL_TOKEN")


def chat_completion(messages, model="gpt-4o"):
    headers = {"Authorization": f"Bearer {VIRTUAL_TOKEN}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": messages}
    try:
        response = requests.post(f"{LITELLM_API_BASE}/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}, Response: {response.content if response else None}")
        return None


def map_fields(source_csv_path, target_csv_path, output_md_path):
    source_fields = []
    with open(source_csv_path, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['IN_SCOPE'].upper() == 'YES':
                source_fields.append({
                    'COLUMN_NAME': row['COLUMN_NAME'],
                    'DATA_TYPE': row['DATA_TYPE'],
                    'NULL_PERCENTAGE': row['NULL_PERCENTAGE']
                })

    target_fields = []
    with open(target_csv_path, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            target_fields.append({
                'COLUMN_NAME': row['COLUMN_NAME'],
                'DATA_TYPE': row['DATA_TYPE'],
                'DESCRIPTION': row['DESCRIPTION']
            })

    if not source_fields or not target_fields:
        print("Error: One or both of the CSV files are empty or have no in-scope source fields.")
        return

    source_str = "\n".join([f"Column Name: {f['COLUMN_NAME']}, Data Type: {f['DATA_TYPE']}" for f in source_fields])
    target_str = "\n".join([f"Column Name: {f['COLUMN_NAME']}, Data Type: {f['DATA_TYPE']}, Description: {f['DESCRIPTION']}" for f in target_fields])

    prompt = f"""
    [NO PROSE]
    You are an expert in data migration and mapping. Your task is to map fields from a source table to a target table.

    Source Table Fields (only considering fields marked as IN_SCOPE='YES'):
    {source_str}

    Target Table Fields:
    {target_str}

    For each source field, identify the best matching target field(s). Consider the column names, data types, and the description of the target field.

    If there's a direct one-to-one mapping based on name and similar data type, indicate that.
    If a data type transformation is likely needed, mention it (e.g., 'string to integer', 'date to string').
    If multiple source fields might need to be combined (concatenated or otherwise transformed) to fit a target field, suggest the combination and the potential transformation.
    You will list every source field and its corresponding target field(s) (if any) with any necessary transformation details.

    Provide your mapping in the following format for each source field:
    Source Column: [Source Column Name]
    Mapped Target Column(s): [Target Column Name(s)] (with potential transformation: [Transformation details])
    ---
    """

    messages = [{"role": "system", "content": "You are an expert in data migration and mapping."}, {"role": "user", "content": prompt}]
    response = chat_completion(messages)

    if response and 'choices' in response and response['choices']:
        mapping_result = response['choices'][0]['message']['content']
        print("\n--- Mapping Results ---")
        print(mapping_result)

        with open(output_md_path, 'w') as md_file:
            md_file.write("# Field Mapping Results\n\n")
            md_file.write(mapping_result)
    else:
        print("Failed to get a mapping response from the GenAI model.")


if __name__ == "__main__":
    source_csv_file = 'source.csv'
    target_csv_file = 'target.csv'
    output_md_file = 'mapping_results.md'
    map_fields(source_csv_file, target_csv_file, output_md_file)
