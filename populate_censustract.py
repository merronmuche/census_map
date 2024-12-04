import os
import django
import requests
from county_mapping import metropolitan_area_county_mapping
import zipfile
from django.db import transaction
import geopandas as gpd

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "census_map.settings")
django.setup()

from app.models import County,CensusTract


CENSUS_TRACT_BASE_URL = "https://www2.census.gov/geo/tiger/TIGER2021/TRACT/"
TRACT_SHAPE_FILES_DIR = "/tmp/tract_shape_files"

def get_required_state_fips():
    """Extract unique state FIPS codes from the county mapping."""
    state_fips = set(fips[:2] for counties in metropolitan_area_county_mapping.values() for fips in counties.values())
    return state_fips

def download_and_extract_state_tract_shapes(state_fips):
    """Download and extract tract shapefiles for the required states."""
    os.makedirs(TRACT_SHAPE_FILES_DIR, exist_ok=True)
    for state_code in state_fips:
        file_name = f"tl_2021_{state_code}_tract.zip"
        url = f"{CENSUS_TRACT_BASE_URL}{file_name}"
        zip_path = os.path.join(TRACT_SHAPE_FILES_DIR, file_name)

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
            zip_ref.extractall(TRACT_SHAPE_FILES_DIR)

        # Remove the ZIP file to save space
        os.remove(zip_path)
        print(f"Extracted {file_name} to {TRACT_SHAPE_FILES_DIR}.")


def load_tract_data_by_county_fips(county_fips, state_fips):
    """Load census tracts for a given county and state."""
    shapefile_path = os.path.join(TRACT_SHAPE_FILES_DIR, f"tl_2021_{state_fips}_tract.shp")
    
    if not os.path.exists(shapefile_path):
        print(f"Shapefile not found: {shapefile_path}")
        return None

    # Read the shapefile
    gdf = gpd.read_file(shapefile_path)

    # Filter for the specific county FIPS code
    return gdf[gdf["COUNTYFP"] == county_fips]

def save_census_tracts_to_db():
    """Save census tracts for all counties in the database."""
    with transaction.atomic():
        for metro_name, counties_fips in metropolitan_area_county_mapping.items():
            for county_name, county_fips in counties_fips.items():
                state_fips = county_fips[:2]  # Extract state FIPS from county FIPS
                try:
                    county = County.objects.get(fips_code=county_fips)
                except County.DoesNotExist:
                    print(f"County {county_name} with FIPS {county_fips} not found.")
                    continue

                # Load tracts for the county
                tract_gdf = load_tract_data_by_county_fips(county_fips[2:], state_fips)
                if tract_gdf is None or tract_gdf.empty:
                    print(f"No tracts found for county {county_name} with FIPS {county_fips}.")
                    continue

                # Save each tract
                for _, row in tract_gdf.iterrows():
                    CensusTract.objects.get_or_create(
                        fips_code=row["GEOID"],
                        county=county,
                        defaults={
                            "name": row["NAMELSAD"],
                            "shape_data": row.geometry.__geo_interface__,
                        }
                    )
                print(f"Saved tracts for county {county_name}.")


if __name__ == "__main__":
    state_fips = get_required_state_fips()
    
    download_and_extract_state_tract_shapes(state_fips)
    
    save_census_tracts_to_db()
