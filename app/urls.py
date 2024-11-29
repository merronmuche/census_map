
from django.urls import path
from .views import CountyGeoJSONView,county_map


urlpatterns = [
    path("county/<int:id>/geojson/", CountyGeoJSONView.as_view(), name="county_geojson"),
    path("countymap/<int:id>/", county_map, name="county_map"),  


]
