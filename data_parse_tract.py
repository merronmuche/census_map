import requests
import pandas as pd

# URLs for data and variable descriptions
data_url = "https://api.census.gov/data/2020/acs/acs5/profile?get=group(DP02)&for=tract:*&in=state:01+county:001"  # Adjusted for census tracts
description_url = "https://api.census.gov/data/2020/acs/acs5/profile/variables.json"

# Fetch data
data_response = requests.get(data_url)
if data_response.status_code == 200:
    data = data_response.json()
else:
    print("Failed to fetch data")
    exit()

# Fetch variable descriptions
description_response = requests.get(description_url)
if description_response.status_code == 200:
    description_data = description_response.json()
else:
    print("Failed to fetch variable descriptions")
    exit()

# Extract headers and rows from data
headers = data[0]
rows = data[1:]

# Function to clean and parse descriptions
def parse_label(label):
    # Split into Category/Topic and Sub-Category/Details
    parts = label.split("!!")
    category = parts[0] if len(parts) > 0 else ""
    sub_category = "!!".join(parts[1:]) if len(parts) > 1 else ""
    return category.strip(), sub_category.strip()

# Create a dictionary mapping variable codes to detailed descriptions
variable_descriptions = {}
structured_data = []

for key, value in description_data["variables"].items():
    if not key.endswith(('EA', 'M', 'PMA', 'PM')):  # Exclude attributes
        label = value.get("label", "")
        category, sub_category = parse_label(label)
        variable_descriptions[key] = label
        structured_data.append({
            "Code": key,
            "Category/Topic": category,
            "Sub-Category/Details": sub_category
        })

# Replace headers with descriptions and filter rows accordingly
filtered_headers = [header for header in headers if header in variable_descriptions]
descriptive_headers = [variable_descriptions[header] for header in filtered_headers]
filtered_rows = [[row[headers.index(header)] for header in filtered_headers] for row in rows]

# Create DataFrame for filtered data
df_filtered = pd.DataFrame(filtered_rows, columns=descriptive_headers)

# Save filtered data to Excel
output_file_filtered = "census_tract_data_main_variables.xlsx"
df_filtered.to_excel(output_file_filtered, index=False, engine="openpyxl")

# Create DataFrame for structured variable descriptions
df_variables = pd.DataFrame(structured_data, columns=["Code", "Category/Topic", "Sub-Category/Details"])

# Save variable descriptions as a table to Excel
output_file_table = "censustract_variable_table.xlsx"
df_variables.to_excel(output_file_table, index=False, engine="openpyxl")

# Save variable descriptions as a table to CSV (optional)
output_file_table_csv = "census_variable_table.csv"
df_variables.to_csv(output_file_table_csv, index=False)

# Print success messages
print("Filtered data and variable descriptions saved successfully.")
print(f"Filtered Data File: {output_file_filtered}")
print(f"Variable Descriptions Table (Excel): {output_file_table}")
print(f"Variable Descriptions Table (CSV): {output_file_table_csv}")