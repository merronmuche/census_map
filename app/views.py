from .models import County
from django.shortcuts import render
from django.http import JsonResponse
from djgeojson.views import GeoJSONLayerView

import requests
from django.views.decorators.csrf import csrf_exempt
from io import BytesIO
from zipfile import ZipFile
import geopandas as gpd
import json


def county_map(request, id):
    county = County.objects.get(id=id)
    return render(
        request,
        "map.html",
        {
            "county": county,
        },
    )

class CountyGeoJSONView(GeoJSONLayerView):
    def get_queryset(self):
        return County.objects.filter(id=self.kwargs["id"])

    def render_to_response(self, context, **response_kwargs):
        county = self.get_queryset().first()
        if not county:
            print("No county found")
            return JsonResponse({"error": "county not found"}, status=404)

        try:
            
            print(f"County shape_file: {county.shape_data}")
            shape_file = (
                county.shape_data
            )  
            data = {"shape_file": shape_file} 
            return JsonResponse(data, safe=False)  
        except Exception as e:
            print(f"Error: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def create_counties_by_state(request):
    if request.method == "POST":
        data = json.loads(request.body)

        # Extract the state name or FIPS code from the request body
        state_fips = data.get("state_fips")
        state_name = data.get("state_name")

        if not state_fips and not state_name:
            return JsonResponse({"error": "State FIPS or state name is required"}, status=400)

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

        # Filter counties by state FIPS or state name
        if state_fips:
            filtered_counties = counties_gdf[counties_gdf["STATEFP"] == state_fips]
        elif state_name:
            filtered_counties = counties_gdf[counties_gdf["STATE_NAME"].str.lower() == state_name.lower()]

        if filtered_counties.empty:
            return JsonResponse({"error": "No counties found for the specified state"}, status=404)

        # Loop through the filtered counties and save to the database
        counties_created = 0
        for _, row in filtered_counties.iterrows():
            county_name = row["NAME"]
            fips_code = row["GEOID"]
            shape_data = json.loads(filtered_counties[filtered_counties["GEOID"] == fips_code].to_json())

            # Check if the county already exists
            if not County.objects.filter(fips_code=fips_code).exists():
                County.objects.create(
                    name=county_name,
                    fips_code=fips_code,
                    shape_data=shape_data,
                )
                counties_created += 1

        return JsonResponse({"message": f"{counties_created} counties created successfully"}, status=201)
    else:
        return JsonResponse({"error": "Invalid HTTP method"}, status=405)
