from django.shortcuts import render
from django.http import JsonResponse
from djgeojson.views import GeoJSONLayerView
from .models import MetropolitanArea, County
import pandas as pd
import requests
from django.views.decorators.csrf import csrf_exempt
from io import BytesIO
from zipfile import ZipFile
import geopandas as gpd
import json


def county_map(request):
    return render(request, "map.html", {})

def metropolitan_map_old(request):
    
    return render(request, 'maps.html')

def metropolitan_map(request):

    return render(request, 'ui.html')

def get_metropolitan_areas(request):

    metros = MetropolitanArea.objects.values_list('name', flat=True).order_by('name')
    return JsonResponse({"metropolitan_areas": list(metros)}, status=200)

class CountyGeoJSONView(GeoJSONLayerView):
    def get_queryset(self):
        metro_name = self.request.GET.get("metro_name", "Default Metro Area")
        return County.objects.filter(metropolitan_area__name=metro_name)

    def render_to_response(self, context, **response_kwargs):
        counties = list(self.get_queryset())
        if not counties:
            return JsonResponse({"error": "No counties found"}, status=404)

        features = []
        for county in counties:
            try:
                shape_data = (
                    json.loads(county.shape_data)
                    if isinstance(county.shape_data, str)
                    else county.shape_data
                )
                if shape_data and "features" in shape_data:
                    geometry = shape_data["features"][0].get("geometry", None)
                    if geometry:
                        features.append({
                            "type": "Feature",
                            "geometry": geometry,
                            "properties": {"name": county.name},
                        })
            except Exception as e:
                print(f"Error processing county {county.name}: {e}")

        geojson_data = {"type": "FeatureCollection", "features": features}
        return JsonResponse(geojson_data, safe=False)


@csrf_exempt
def create_counties_by_metro(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            metro_name = data.get("metro_name")
            if not metro_name:
                return JsonResponse({"error": "Metropolitan area name is required"}, status=400)

            msa_counties_file = "/path/to/list1_2020.xls"
            msa_data = pd.read_excel(msa_counties_file, engine="xlrd", skiprows=2)
            metro_data = msa_data[msa_data["CBSA Title"].str.contains(metro_name, case=False, na=False)]

            if metro_data.empty:
                return JsonResponse({"error": f"No counties found for {metro_name}"}, status=404)

            county_fips_list = metro_data.apply(
                lambda row: f"{int(row['FIPS State Code']):02}{int(row['FIPS County Code']):03}", axis=1
            ).tolist()

            BASE_URL = "https://www2.census.gov/geo/tiger/TIGER2022/COUNTY/tl_2022_us_county.zip"
            response = requests.get(BASE_URL)
            if response.status_code != 200:
                return JsonResponse({"error": "Failed to fetch shapefile"}, status=500)

            with ZipFile(BytesIO(response.content)) as z:
                z.extractall("counties_temp")
            shapefile_path = "counties_temp/tl_2022_us_county.shp"

            counties_gdf = gpd.read_file(shapefile_path)
            filtered_counties = counties_gdf[counties_gdf["GEOID"].isin(county_fips_list)]

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
