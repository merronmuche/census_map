from django.db import models
import uuid


class MetropolitanArea(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    cbsa_code = models.CharField(max_length=10, unique=True, blank=True, null=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    

    def __str__(self):
        return self.name


class County(models.Model):
    name = models.CharField(max_length=100)
    metropolitan_area = models.ForeignKey(
        MetropolitanArea, 
        on_delete=models.CASCADE, 
        null=True,
        blank=True,
    )
    fips_code = models.CharField(max_length=10,null=True,blank=True)
    shape_data = models.JSONField(blank=True, null=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class CensusTract(models.Model):
    name = models.CharField(max_length=100)
    county = models.ForeignKey(
        County,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    fips_code = models.CharField(max_length=10, unique=True)
    shape_data = models.JSONField(blank=True, null=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class BlockGroup(models.Model):
    name = models.CharField(max_length=100, )
    population = models.PositiveIntegerField()
    male = models.DecimalField(max_digits=100, decimal_places=2)
    female = models.DecimalField(max_digits=100, decimal_places=2)
    black = models.DecimalField(max_digits=100, decimal_places=2)
    white = models.DecimalField(max_digits=100, decimal_places=2)
    asian = models.PositiveIntegerField(default=0)
    hispanic = models.PositiveIntegerField(default=0)
    household_type = models.CharField(max_length=255, blank=True, null=True)
    medean_income = models.FloatField()
    medean_income = models.IntegerField()
    census_tract = models.ForeignKey(
        CensusTract, 
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    fips_code = models.CharField(max_length=12, unique=True)
    shape_data = models.JSONField(blank=True, null=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} (FIPS: {self.fips_code})"
