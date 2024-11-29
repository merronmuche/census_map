from rest_framework_gis.serializers import ModelSerializer
from .models import County

class CountySerializer(ModelSerializer):
    class Meta:
        model = County
        fields = ('id', 'name', 'fips_code','shape_data')
