
from django.urls import path
from .views import CountyGeoJSONView,county_map,create_counties_by_state


urlpatterns = [
    path("county/<int:id>/geojson/", CountyGeoJSONView.as_view(), name="county_geojson"),
    path("countymap/<int:id>/", county_map, name="county_map"),
    path("county/create-by-state/", create_counties_by_state, name="create-by-state"),
]
