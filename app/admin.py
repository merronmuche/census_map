from django.contrib import admin
from .models import County

@admin.register(County)
class CountyAdmin(admin.ModelAdmin):
    list_display = ["id","name", "fips_code"]
