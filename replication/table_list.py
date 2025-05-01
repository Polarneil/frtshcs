import os
import csv
import json
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


def should_include_table(table_name):
    prompt = f"""Given the table name "{table_name}", determine if this table from a Salesforce database is likely related to the following entities for a healthcare staffing firm:

    - Employees Internal: employees of the healthcare staffing firm
    - Employees External: clients of the firm (travel nurses, etc.) looking for placements
    - Customer: Institutions with placements (jobs) for external employees
    - Placements: Jobs for external employees listed by customers
    - Payroll
    - Time Tracking

    Respond with "yes" if the table likely pertains to one of these entities, or "no" if it does not. If you are unsure, err on the side of caution and respond with "yes".
    """
    messages = [{"role": "system", "content": "You are a helpful assistant for determining relevant database tables."}, {"role": "user", "content": prompt}]
    response = chat_completion(messages)
    if response and "choices" in response and response["choices"] and "message" in response["choices"][0] and "content" in response["choices"][0]["message"]:
        return response["choices"][0]["message"]["content"].strip().lower() == "yes"
    else:
        print(f"LLM response error for table: {table_name}. Defaulting to include.")
        return True


def process_csv(csv_filepath):
    results = []
    with open(csv_filepath, 'r') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            table_name = row[0]
            include = should_include_table(table_name)
            results.append({"table_name": table_name, "include": include})
    return results


if __name__ == "__main__":
    csv_file = "salesforce_sandbox_tables.csv"
    output_json_file = "table_analysis_results.json"
    analysis_results = process_csv(csv_file)

    with open(output_json_file, 'w') as jsonfile:
        json.dump(analysis_results, jsonfile, indent=4)

    print(f"Analysis results written to {output_json_file}")
