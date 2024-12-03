from .models import MetropolitanArea,County
from django.shortcuts import render
from django.http import JsonResponse
from djgeojson.views import GeoJSONLayerView
import pandas as pd
import requests
from django.views.decorators.csrf import csrf_exempt
from io import BytesIO
from zipfile import ZipFile
import geopandas as gpd
import json


def county_map(request):
    return render(request, "map.html", {})


class CountyGeoJSONView(GeoJSONLayerView):
    """
    Returns GeoJSON for all counties.
    """
    def get_queryset(self):
        return County.objects.filter(metropolitan_area__name="New York–Newark–Jersey City, NY-NJ-PA MSA")
    
    def render_to_response(self, context, **response_kwargs):
        counties = list(self.get_queryset())
        if not counties:
            return JsonResponse({"error": "No counties found"}, status=404)

        try:
            # Initialize an empty list for features
            features = []

            for county in counties:
                try:
                    # Deserialize shape_data if it's stored as a string
                    shape_data = (
                        json.loads(county.shape_data)
                        if isinstance(county.shape_data, str)
                        else county.shape_data
                    )

                    # Ensure shape_data has the expected structure
                    if shape_data and "features" in shape_data and shape_data["features"]:
                        geometry = shape_data["features"][0].get("geometry", None)
                        if geometry:
                            features.append({
                                "type": "Feature",
                                "geometry": geometry,
                                "properties": {
                                    "name": county.name,
                                },
                            })
                    else:
                        print(f"Invalid shape_data for county: {county.name}")
                except json.JSONDecodeError as e:
                    print(f"Error decoding shape_data for county {county.name}: {str(e)}")
                except Exception as e:
                    print(f"Unexpected error for county {county.name}: {str(e)}")

            # Wrap the features in a FeatureCollection
            geojson_data = {
                "type": "FeatureCollection",
                "features": features,
            }

            return JsonResponse(geojson_data, safe=False)
        except Exception as e:
            print(f"Error during GeoJSON generation: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)
# Load the MSA-to-county mapping file


@csrf_exempt
def create_counties_by_metro(request):
    """
    Dynamically create counties based on metropolitan area name.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            # Extract metro name from request
            metro_name = data.get("metro_name")
            if not metro_name:
                return JsonResponse({"error": "Metropolitan area name is required"}, status=400)

            # Load MSA-to-county mapping dataset
            msa_counties_file = "/home/meron/works/census_map/list1_2020.xls"
            msa_data = pd.read_excel(msa_counties_file, engine="xlrd", skiprows=2)

            # Filter dataset by metro name
            metro_data = msa_data[msa_data["CBSA Title"].str.contains(metro_name, case=False, na=False)]
            if metro_data.empty:
                return JsonResponse({"error": f"No counties found for metropolitan area: {metro_name}"}, status=404)

            # Extract county FIPS codes
            county_fips_list = metro_data.apply(
                lambda row: f"{int(row['FIPS State Code']):02}{int(row['FIPS County Code']):03}", axis=1
            ).tolist()

            # Fetch the TIGER/Line shapefile for counties
            BASE_URL = "https://www2.census.gov/geo/tiger/TIGER2022/COUNTY/tl_2022_us_county.zip"
            response = requests.get(BASE_URL)
            if response.status_code != 200:
                return JsonResponse({"error": "Failed to fetch shapefile"}, status=500)

            # Extract the ZIP file
            with ZipFile(BytesIO(response.content)) as z:
                z.extractall("counties_temp")
            shapefile_path = "counties_temp/tl_2022_us_county.shp"

            # Load shapefile into GeoPandas
            counties_gdf = gpd.read_file(shapefile_path)

            # Filter counties by FIPS codes
            filtered_counties = counties_gdf[counties_gdf["GEOID"].isin(county_fips_list)]
            if filtered_counties.empty:
                return JsonResponse({"error": "No counties found for the specified metropolitan area"}, status=404)

            # Loop through the filtered counties and save to the database
            counties_created = 0
            for _, row in filtered_counties.iterrows():
                county_name = row["NAME"]
                fips_code = row["GEOID"]
                shape_data = json.loads(filtered_counties[filtered_counties["GEOID"] == fips_code].to_json())

                if not County.objects.filter(fips_code=fips_code).exists():
                    County.objects.create(
                        name=county_name,
                        fips_code=fips_code,
                        shape_data=shape_data,
                    )
                    counties_created += 1

            return JsonResponse(
                {"message": f"{counties_created} counties created successfully for {metro_name}"},
                status=201,
            )

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid HTTP method"}, status=405)

