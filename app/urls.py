from django.urls import path
from .views import (
    CensusTractGeoJSONView,
    CountyGeoJSONView,
    BlockGroupGeoJSONView,  
    metropolitan_map,
    get_metropolitan_areas,
)

urlpatterns = [
    path("api/get_metropolitan_areas/", get_metropolitan_areas, name="get_metropolitan_areas"),
    path("api/get_county_geojson/", CountyGeoJSONView.as_view(), name="county_geojson"),
    path("api/get_census_tracts/", CensusTractGeoJSONView.as_view(), name="census_tract_geojson"),
    path("api/get_block_groups/", BlockGroupGeoJSONView.as_view(), name="block_group_geojson"),  
    path("map/", metropolitan_map, name="metropolitan_map"),
]
