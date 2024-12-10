from django.contrib import admin
from app.models import MetropolitanArea, County, CensusTract, BlockGroup

@admin.register(MetropolitanArea)
class MetropolitanAreaAdmin(admin.ModelAdmin):
    list_display = ("name", "cbsa_code")
    search_fields = ("name", "cbsa_code")
    list_filter = ("created_at", "updated_at")
   

@admin.register(County)
class CountyAdmin(admin.ModelAdmin):
    list_display = ("name", "metropolitan_area", "fips_code")
    search_fields = ("name", "fips_code")
    list_filter = ("metropolitan_area", "created_at", "updated_at")


@admin.register(CensusTract)
class CensusTractAdmin(admin.ModelAdmin):
    list_display = ("name", "county", "fips_code")
    search_fields = ("name", "fips_code")
    list_filter = ("county", "created_at", "updated_at")


@admin.register(BlockGroup)
class BlockGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "census_tract","fips_code", "population", "male", "female")
    search_fields = ("name", "fips_code", "census_tract__name", "population")
    list_filter = ("census_tract", "created_at", "updated_at")
    
