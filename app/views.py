from django.shortcuts import render
from django.http import JsonResponse
from djgeojson.views import GeoJSONLayerView
from .models import CensusTract, MetropolitanArea, County, BlockGroup
import pandas as pd
import requests
from django.views.decorators.csrf import csrf_exempt
from io import BytesIO
from zipfile import ZipFile
import geopandas as gpd
import json
from django.views import View
from django.db.models import Sum


def county_map(request):
    return render(request, "map.html", {})

def metropolitan_map_old(request):
    
    return render(request, 'maps.html')

def metropolitan_map(request):

    return render(request, 'ui.html')

def get_metropolitan_areas(request):

    metros = MetropolitanArea.objects.values_list('name', flat=True).order_by('name')
    return JsonResponse({"metropolitan_areas": list(metros)}, status=200)


class BlockGroupGeoJSONView(View):
    def get_queryset(self, metro_name):
        # Filter BlockGroups by Metropolitan Area
        return BlockGroup.objects.filter(
            census_tract__county__metropolitan_area__name=metro_name
        )

    def render_to_response(self, context, **response_kwargs):
        metro_name = self.request.GET.get("metro_name", None)
        if not metro_name:
            return JsonResponse({"error": "metro_name parameter is required"}, status=400)

        block_groups = self.get_queryset(metro_name)
        if not block_groups.exists():
            return JsonResponse({"error": f"No block groups found for {metro_name}."}, status=404)

        features = []
        for block_group in block_groups:
            try:
                # Parse shape_data for GeoJSON structure
                geometry = (
                    json.loads(block_group.shape_data)
                    if isinstance(block_group.shape_data, str)
                    else block_group.shape_data
                )

                if geometry:
                    features.append({
                        "type": "Feature",
                        "geometry": geometry,
                        "properties": {
                            "name": block_group.name,
                            "fips_code": block_group.fips_code,
                            "population": block_group.population,
                            "male": block_group.male,
                            "female": block_group.female,
                            "black": block_group.black,
                            "white": block_group.white,
                        },
                    })
            except Exception as e:
                print(f"Error processing block group {block_group.name}: {e}")

        geojson_data = {
            "type": "FeatureCollection",
            "features": features,
        }

        return JsonResponse(geojson_data, safe=False)

    def get(self, request, *args, **kwargs):
        return self.render_to_response(context=None)

class CensusTractGeoJSONView(View):
    def get_queryset(self, metro_name):

        return CensusTract.objects.filter(
            county__metropolitan_area__name=metro_name
        ).annotate(
            cumulative_population=Sum('blockgroup__population')  # Sum population of related block groups
        )

    def render_to_response(self, context, **response_kwargs):
        """
        Build the GeoJSON response for census tracts.
        """
        metro_name = self.request.GET.get("metro_name", None)
        if not metro_name:
            return JsonResponse({"error": "metro_name parameter is required"}, status=400)

        census_tracts = self.get_queryset(metro_name)
        if not census_tracts.exists():
            return JsonResponse({"error": "No census tracts found for the given metropolitan area"}, status=404)

        features = []
        for tract in census_tracts:
            try:
                # Parse shape_data for GeoJSON structure
                geometry = (
                    json.loads(tract.shape_data)
                    if isinstance(tract.shape_data, str)
                    else tract.shape_data
                )

                if geometry:
                    features.append({
                        "type": "Feature",
                        "geometry": geometry,
                        "properties": {
                            "name": tract.name,
                            "fips_code": tract.fips_code,
                            "population": tract.cumulative_population or 0,  # Include cumulative population
                        },
                    })
            except Exception as e:
                print(f"Error processing census tract {tract.name}: {e}")

        geojson_data = {
            "type": "FeatureCollection",
            "features": features,
        }

        return JsonResponse(geojson_data, safe=False)

    def get(self, request, *args, **kwargs):
        return self.render_to_response(context=None)


class CountyGeoJSONView(GeoJSONLayerView):
    def get_queryset(self):
        metro_name = self.request.GET.get("metro_name", "Default Metro Area")
        return County.objects.filter(
            metropolitan_area__name=metro_name
        ).annotate(
            cumulative_population=Sum('censustract__blockgroup__population')  # Sum population of related block groups
        )

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
                            "properties": {
                            "name": county.name,
                            "population": county.cumulative_population or 0,  # Include cumulative population
                        },
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
