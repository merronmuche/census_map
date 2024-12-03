import os
import django
import uuid
import requests
from county_mapping import metropolitan_area_county_mapping
import zipfile
from django.db import transaction
import geopandas as gpd

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "census_map.settings")
django.setup()

from app.models import MetropolitanArea, County


BASE_URL = "https://www2.census.gov/geo/tiger/TIGER2022/COUNTY/tl_2022_us_county.zip"
SHAPE_FILES_DIR = "/tmp/shape_files"

def download_and_extract_shapes():
    zip_path = os.path.join(SHAPE_FILES_DIR, "counties.zip")
    os.makedirs(SHAPE_FILES_DIR, exist_ok=True)

    response = requests.get(BASE_URL, stream=True)
    with open(zip_path, "wb") as zip_file:
        for chunk in response.iter_content(chunk_size=8192):
            zip_file.write(chunk)
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(SHAPE_FILES_DIR)
    os.remove(zip_path)

def load_shape_data_by_fips(fips_code):
    """
    Generate shape data for a given FIPS code by reading from the shapefiles.
    """
    shapefile_path = os.path.join(SHAPE_FILES_DIR, "tl_2022_us_county.shp")  # Shapefile path

    # Ensure shapefile exists
    if not os.path.exists(shapefile_path):
        raise FileNotFoundError(f"Shapefile not found at {shapefile_path}. Ensure the ZIP is extracted correctly.")

    # Read the shapefile using GeoPandas
    try:
        gdf = gpd.read_file(shapefile_path)
    except Exception as e:
        raise RuntimeError(f"Error reading shapefile: {e}")

    # Filter for the specific FIPS code
    filtered_gdf = gdf[gdf["GEOID"] == fips_code]

    if filtered_gdf.empty:
        return None  

    return filtered_gdf.to_json()

def save_data_to_db():
    with transaction.atomic():
        # Iterate over metropolitan areas
        for metro_name, counties_fips in metropolitan_area_county_mapping.items():
            # Create or retrieve MetropolitanArea
            metropolitan_area, created = MetropolitanArea.objects.get_or_create(
                name=metro_name,
                defaults={
                    "description": "",
                    "cbsa_code": None, 
                    "uuid": uuid.uuid4(),
                }
            )
            
            # Iterate over counties and their FIPS codes
            for county_name, fips_code in counties_fips.items():
                shape_data = load_shape_data_by_fips(fips_code)
                
                County.objects.get_or_create(
                    name=county_name,
                    metropolitan_area=metropolitan_area,
                    defaults={
                        "fips_code": fips_code,
                        "shape_data": shape_data,
                        "uuid": uuid.uuid4(),
                    }
                )

if __name__ == "__main__":
    download_and_extract_shapes()
    
    save_data_to_db()
