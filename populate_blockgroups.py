import os
import django
import requests
import zipfile
from django.db import transaction
import geopandas as gpd
import json

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "census_map.settings")
django.setup()

from app.models import CensusTract, BlockGroup

BLOCK_GROUP_BASE_URL = "https://www2.census.gov/geo/tiger/TIGER2021/BG/"
BLOCK_GROUP_SHAPE_FILES_DIR = "/tmp/block_group_shape_files"



def get_required_census_tract_codes():
    """Extract all Census Tract FIPS codes from the database."""
    return list(CensusTract.objects.values_list('fips_code', flat=True))



def download_and_extract_shapefiles(census_tract_fips):
    """Download and extract block group shapefiles for the required Census Tracts."""
    os.makedirs(BLOCK_GROUP_SHAPE_FILES_DIR, exist_ok=True)
    state_fips_set = {fips[:2] for fips in census_tract_fips}  # Get unique state FIPS codes

    for state_code in state_fips_set:
        file_name = f"tl_2021_{state_code}_bg.zip"
        url = f"{BLOCK_GROUP_BASE_URL}{file_name}"
        zip_path = os.path.join(BLOCK_GROUP_SHAPE_FILES_DIR, file_name)

        # Download the file
        print(f"Downloading {url}...")
        response = requests.get(url, stream=True)
        if response.status_code != 200:
            print(f"Failed to download {url}: HTTP {response.status_code}")
            continue

        # Save the ZIP file locally
        with open(zip_path, "wb") as zip_file:
            for chunk in response.iter_content(chunk_size=8192):
                zip_file.write(chunk)

        # Extract the ZIP file
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(BLOCK_GROUP_SHAPE_FILES_DIR)

        # Remove the ZIP file to save space
        os.remove(zip_path)
        print(f"Extracted {file_name} to {BLOCK_GROUP_SHAPE_FILES_DIR}.")


def load_block_group_data_by_tract(census_tract_fips, shapefile_path):
    """Load block groups for a given Census Tract from the shapefile."""
    if not os.path.exists(shapefile_path):
        print(f"Shapefile not found: {shapefile_path}")
        return None

    # Read the shapefile
    gdf = gpd.read_file(shapefile_path)

    # Filter by Census Tract FIPS
    return gdf[gdf["TRACTCE"].isin([fips[5:] for fips in census_tract_fips])]


def save_block_groups_to_db():
    """Save block groups for all Census Tracts in the database."""
    with transaction.atomic():
        # Step 1: Get all Census Tract FIPS codes
        census_tract_fips = get_required_census_tract_codes()

        # Step 2: Download and extract shapefiles for the corresponding states
        download_and_extract_shapefiles(census_tract_fips)

        # Step 3: Process each Census Tract
        state_fips_set = {fips[:2] for fips in census_tract_fips}  # Unique state FIPS codes
        for state_fips in state_fips_set:
            shapefile_path = os.path.join(BLOCK_GROUP_SHAPE_FILES_DIR, f"tl_2021_{state_fips}_bg.shp")
            bg_gdf = load_block_group_data_by_tract(census_tract_fips, shapefile_path)

            if bg_gdf is None or bg_gdf.empty:
                print(f"No block groups found for state FIPS {state_fips}.")
                continue

            # Save each block group
            for _, row in bg_gdf.iterrows():
                tract_fips = f"{state_fips}{row['COUNTYFP']}{row['TRACTCE']}"
                try:
                    census_tract = CensusTract.objects.get(fips_code=tract_fips)
                except CensusTract.DoesNotExist:
                    print(f"CensusTract with FIPS {tract_fips} not found, skipping BlockGroup {row['GEOID']}.")
                    continue

                # Save the BlockGroup
                BlockGroup.objects.get_or_create(
                    fips_code=row["GEOID"],
                    census_tract=census_tract,
                    defaults={
                        "name": row["NAMELSAD"],
                        "population": row.get("POPULATION", 0),  # Placeholder for actual data
                        "male": row.get("MALE", 0),              # Placeholder for actual data
                        "female": row.get("FEMALE", 0),          # Placeholder for actual data
                        "black": row.get("BLACK", 0),            # Placeholder for actual data
                        "white": row.get("WHITE", 0),            # Placeholder for actual data
                        "shape_data": row.geometry.__geo_interface__
                    }
                )
            print(f"Saved block groups for state FIPS: {state_fips}")


if __name__ == "__main__":
    save_block_groups_to_db()
