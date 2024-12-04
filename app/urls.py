from django.urls import path
from .views import (
    CountyGeoJSONView,
    create_counties_by_metro,
    metropolitan_map,
    get_metropolitan_areas,
)

urlpatterns = [
    path("api/get_metropolitan_areas/", get_metropolitan_areas, name="get_metropolitan_areas"),
    path("api/get_county_geojson/", CountyGeoJSONView.as_view(), name="county_geojson"),
    path("county/create-by-metro/", create_counties_by_metro, name="create_counties_by_metro"),
    path("map/", metropolitan_map, name="metropolitan_map"),

]
