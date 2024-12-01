
from django.urls import path
from .views import CountyGeoJSONView,county_map, create_counties_by_metro


urlpatterns = [
    path("county/geojson/", CountyGeoJSONView.as_view(), name="county_geojson"),
    path("countymap/", county_map, name="county_map"),
    path("county/create-by-metro/", create_counties_by_metro, name="create_counties_by_metro"),
]
