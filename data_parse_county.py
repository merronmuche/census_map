import requests
import pandas as pd

# URLs for data and variable descriptions
data_url = "https://api.census.gov/data/2023/acs/acs1/profile?get=group(DP02)&for=county:037&in=state:06"
description_url = "https://api.census.gov/data/2023/acs/acs1/profile/variables.json"

# Fetch data
data_response = requests.get(data_url)
if data_response.status_code == 200:
    data = data_response.json()
else:
    print(f"Status Code: {data_response.status_code}")
    print(f"Response Text: {data_response.text}")
    print("Failed to fetch data")
    exit()

# Fetch variable descriptions
description_response = requests.get(description_url)
if description_response.status_code == 200:
    description_data = description_response.json()
else:
    print("Failed to fetch variable descriptions")
    exit()

# Helper function to split label into Category/Topic and Sub-Category/Details
def parse_label(label):
    parts = label.split("!!")
    category = parts[0] if len(parts) > 0 else ""
    sub_category = "!!".join(parts[1:]) if len(parts) > 1 else ""
    return category.strip(), sub_category.strip()

# Extract variables with their descriptions
structured_data = []
for code, details in description_data["variables"].items():
    if not code.endswith(('EA', 'M', 'PMA', 'PM')):
        label = details.get("label", "")
        category, sub_category = parse_label(label)
        structured_data.append({"Code": code, "Category/Topic": category, "Sub-Category/Details": sub_category})

# Create DataFrame
df_structured = pd.DataFrame(structured_data)

# Save to Excel
output_file = "census_variable_descriptions.xlsx"
df_structured.to_excel(output_file, index=False, engine="openpyxl")

# Print success message
print("Data saved successfully as a table.")
print(f"Output file: {output_file}")
