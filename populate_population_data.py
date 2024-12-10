import os
import django
import requests
import time
import logging
import psutil
from django.db import transaction

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "census_map.settings")
django.setup()

from app.models import CensusTract, BlockGroup

# Define your API Key and Base URL
CENSUS_API_KEY = "8380a02318cc4623a5d97965781a32570d2dfc77"
CENSUS_BASE_URL = "https://api.census.gov/data/2020/dec/pl"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')


def log_system_usage():
    """Log memory and CPU usage to monitor resource consumption."""
    mem = psutil.virtual_memory()
    logging.info(f"Memory usage: {mem.percent}%")
    cpu = psutil.cpu_percent(interval=1)
    logging.info(f"CPU usage: {cpu}%")


def get_required_census_tract_codes(batch_size=10):
    """Fetch Census Tract FIPS codes in smaller batches."""
    total = CensusTract.objects.count()
    for offset in range(0, total, batch_size):
        yield CensusTract.objects.filter(blockgroup__population=0).distinct().values_list('fips_code', flat=True)[offset:offset+batch_size]


def fetch_population_data_for_block_groups(census_tract_fips):
    """
    Fetch population data for block groups within a census tract using the Census API.
    Implements retries with exponential backoff for robustness.
    """
    state_fips = census_tract_fips[:2]
    county_fips = census_tract_fips[2:5]
    tract_code = census_tract_fips[5:]

    params = {
        "get": "P1_001N,P1_003N,P1_004N",  # Total, Male, Female populations
        "for": "block group:*",
        "in": f"state:{state_fips} county:{county_fips} tract:{tract_code}",
        "key": CENSUS_API_KEY,
    }

    for attempt in range(5):  # Retry up to 5 times
        try:
            logging.info(f"Fetching data for Census Tract FIPS: {census_tract_fips}, attempt {attempt + 1}")
            response = requests.get(CENSUS_BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.warning(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(2 ** attempt)  # Exponential backoff

    logging.error(f"Failed to fetch data for Census Tract FIPS {census_tract_fips} after 5 attempts.")
    return []


@transaction.atomic
def populate_block_group_data(census_tract_fips):
    """
    Populate block group population data hierarchically for a given census tract.
    """
    logging.info(f"Processing Census Tract FIPS: {census_tract_fips}")
    try:
        census_tract = CensusTract.objects.get(fips_code=census_tract_fips)
    except CensusTract.DoesNotExist:
        logging.warning(f"Census Tract with FIPS {census_tract_fips} does not exist in the database.")
        return

    # Fetch data from the Census API
    try:
        data = fetch_population_data_for_block_groups(census_tract_fips)
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch data from the Census API for FIPS {census_tract_fips}: {e}")
        return

    if not data:
        logging.warning(f"No data received from the API for FIPS {census_tract_fips}.")
        return

    # Parse header and rows
    header = data[0]
    rows = data[1:]
    required_columns = {"P1_001N", "P1_003N", "P1_004N", "block group"}
    if not required_columns.issubset(set(header)):
        logging.error("Unexpected API response format. Check the Census API query.")
        return

    total_pop_idx = header.index("P1_001N")
    male_pop_idx = header.index("P1_003N")
    female_pop_idx = header.index("P1_004N")
    block_group_id_idx = header.index("block group")

    for row in rows:
        try:
            total_population = int(row[total_pop_idx])
            male_population = float(row[male_pop_idx])
            female_population = float(row[female_pop_idx])
            block_group_id = row[block_group_id_idx]

            block_group_fips = f"{census_tract_fips}{block_group_id}"

            block_group = BlockGroup.objects.get(fips_code=block_group_fips)

            block_group.population = total_population
            block_group.male = male_population
            block_group.female = female_population
            block_group.save()

            logging.info(f"Updated Block Group {block_group.fips_code} with population data: "
                         f"Population={block_group.population}, Male={block_group.male}, Female={block_group.female}")

        except (BlockGroup.DoesNotExist, ValueError, IndexError) as e:
            logging.error(f"Error processing block group row {row}: {e}")
            continue

    logging.info(f"Successfully populated data for all block groups in Census Tract: {census_tract.name}")


if __name__ == "__main__":
    log_system_usage()  # Initial system usage logging

    for batch in get_required_census_tract_codes(batch_size=10):
        for census_tract_fip in batch:
            populate_block_group_data(census_tract_fip)

    log_system_usage()  # Final system usage logging
