from .models import MetropolitanArea,County
from django.shortcuts import render
from django.http import JsonResponse
from djgeojson.views import GeoJSONLayerView

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
        return County.objects.all()
    def render_to_response(self, context, **response_kwargs):

        counties = list(self.get_queryset())
        if not counties:
            return JsonResponse({"error": "No counties found"}, status=404)

        try:
            # Initialize an empty list for features
            features = []

            for county in counties:
                # Ensure shape_data exists and has the expected structure
                if county.shape_data and "features" in county.shape_data and county.shape_data["features"]:
                    geometry = county.shape_data["features"][0].get("geometry", None)
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

            # Wrap the features in a FeatureCollection
            geojson_data = {
                "type": "FeatureCollection",
                "features": features,
            }

            return JsonResponse(geojson_data, safe=False)
        except Exception as e:
            print(f"Error during GeoJSON generation: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def create_counties_by_metro(request):
    """
    Create counties based on metropolitan area.
    """
    if request.method == "POST":
        data = json.loads(request.body)

        metro_name = data.get("metro_name")
        metro_fips = data.get("metro_fips")

        if not metro_name and not metro_fips:
            return JsonResponse({"error": "Metro name or FIPS codes are required"}, status=400)

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

        if metro_fips:
            filtered_counties = counties_gdf[counties_gdf["GEOID"].isin(metro_fips)]
        elif metro_name:
            if metro_name.lower() == "new york city":
                nyc_fips = ["36061", "36005", "36047", "36081", "36085"]
                filtered_counties = counties_gdf[counties_gdf["GEOID"].isin(nyc_fips)]
            else:
                return JsonResponse({"error": "Metro name not recognized or supported"}, status=404)

        if filtered_counties.empty:
            return JsonResponse({"error": "No counties found for the specified metropolitan area"}, status=404)

        metro_area, created = MetropolitanArea.objects.get_or_create(name=metro_name)
        counties_created = 0
        for _, row in filtered_counties.iterrows():
            county_name = row["NAME"]
            fips_code = row["GEOID"]
            shape_data = json.loads(filtered_counties[filtered_counties["GEOID"] == fips_code].to_json())

            # Check if county already exists
            if not County.objects.filter(fips_code=fips_code).exists():
                County.objects.create(
                    name=county_name,
                    fips_code=fips_code,
                    shape_data=shape_data,
                )
                counties_created += 1

        return JsonResponse({"message": f"{counties_created} counties created successfully for {metro_name}"}, status=201)
    else:
        return JsonResponse({"error": "Invalid HTTP method"}, status=405)