from django.db import models

class County(models.Model):
    name = models.CharField(max_length=100)
    fips_code = models.CharField(max_length=10, unique=True)
    shape_data = models.JSONField() 

    def __str__(self):
        return self.name 
