from django.db import models


class MetropolitanArea(models.Model):
    """
    Represents a metropolitan area containing multiple counties.
    """
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name
class County(models.Model):
    name = models.CharField(max_length=100)
    metropolitan_area = models.ForeignKey(
        MetropolitanArea,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="counties",
    )
    fips_code = models.CharField(max_length=10, unique=True)
    shape_data = models.JSONField() 

    def __str__(self):
        return self.name 
