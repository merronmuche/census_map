import requests
from django.db import transaction
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "census_map.settings")
django.setup()

from app.models import CensusTract, BlockGroup


# Define your API Key and Base URL
CENSUS_API_KEY = "8380a02318cc4623a5d97965781a32570d2dfc77"
CENSUS_BASE_URL = "https://api.census.gov/data/2020/dec/pl"


def get_required_census_tract_codes():
    """Extract all Census Tract FIPS codes from the database."""
    return list(CensusTract.objects.values_list('fips_code', flat=True))

def fetch_population_data_for_block_groups(census_tract_fips):
    """
    Fetch population data for block groups within a census tract using the Census API.
    """
    # Extract FIPS components
    state_fips = census_tract_fips[:2]
    county_fips = census_tract_fips[2:5]
    tract_code = census_tract_fips[5:]

    # Prepare API parameters
    params = {
        "get": "P1_001N,P1_003N,P1_004N",  # Total, Male, Female populations
        "for": "block group:*",
        "in": f"state:{state_fips} county:{county_fips} tract:{tract_code}",
        "key": CENSUS_API_KEY,
    }

    # API request
    response = requests.get(CENSUS_BASE_URL, params=params)
    response.raise_for_status()  # Raise exception for HTTP errors
    return response.json()

@transaction.atomic
def populate_block_group_data(census_tract_fips):
    """
    Populate block group population data hierarchically for a given census tract.
    """
    try:
        # Get the Census Tract from the database
        census_tract = CensusTract.objects.get(fips_code=census_tract_fips)
    except CensusTract.DoesNotExist:
        print(f"Census Tract with FIPS {census_tract_fips} does not exist in the database.")
        return

    print(f"Fetching population data for Census Tract: {census_tract.name} (FIPS: {census_tract.fips_code})")

    # Fetch data from the Census API
    try:
        data = fetch_population_data_for_block_groups(census_tract_fips)
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch data from the Census API: {e}")
        return

    # Parse header and rows
    header = data[0]
    rows = data[1:]
    print("API Header:", header)
    if rows:
        print("API Row Example:", rows[0])

    # Ensure required columns are present
    required_columns = {"P1_001N", "P1_003N", "P1_004N", "block group"}
    if not required_columns.issubset(set(header)):
        print("Unexpected API response format. Check the Census API query.")
        return

    # Find column indexes
    total_pop_idx = header.index("P1_001N")
    male_pop_idx = header.index("P1_003N")
    female_pop_idx = header.index("P1_004N")
    block_group_id_idx = header.index("block group")

    # Update database for each block group
    for row in rows:
        try:
            # Parse data for the block group
            total_population = int(row[total_pop_idx])
            male_population = float(row[male_pop_idx])
            female_population = float(row[female_pop_idx])
            block_group_id = row[block_group_id_idx]

            # Construct full block group FIPS
            block_group_fips = f"{census_tract_fips}{block_group_id}"

            # Retrieve block groups from the database
            block_group = BlockGroup.objects.get(fips_code=block_group_fips)

            # Update all matching block groups
            block_group.population = total_population
            block_group.male = male_population
            block_group.female = female_population
            block_group.save()  # Save changes

            print(f"Updated Block Group {block_group.fips_code} with population data: "
                    f"Population={block_group.population}, Male={block_group.male}, Female={block_group.female}")

        except (ValueError, IndexError) as e:
            print(f"Error processing row {row}: {e}")
            continue

    print(f"Successfully populated data for all block groups in Census Tract: {census_tract.name}")


# Main function to update Census Tract 202 (Example)
if __name__ == "__main__":
    census_tract_fips = get_required_census_tract_codes()
    for census_tract_fip in census_tract_fips:
        populate_block_group_data(census_tract_fip)

