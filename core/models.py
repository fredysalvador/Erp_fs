from django.db import models

class Status(models.Model):
    name = models.CharField(max_length=50, unique=True,verbose_name="Status Name")
    is_active = models.BooleanField(default=True, verbose_name="Is Active?")

    class Meta:
        verbose_name = "Status"
        verbose_name_plural = "Statuses"

    def __str__(self):
        return self.name

class Country(models.Model):
    name = models.CharField(max_length=50, unique=True,verbose_name="Country Name")
    code = models.CharField(max_length=2, unique=True, verbose_name="Country Code")
    is_active = models.BooleanField(default=True, verbose_name="Is Active?")

    class Meta:
        verbose_name = "Country"
        verbose_name_plural = "Countries"

    def __str__(self):
        return self.name

class Currency(models.Model):
    name = models.CharField(max_length=50, unique=True,verbose_name="Currency Name")
    code = models.CharField(max_length=3, unique=True, verbose_name="Currency Code")
    symbol = models.CharField(max_length=5, verbose_name="Currency Symbol")
    is_active = models.BooleanField(default=True, verbose_name="Is Active?")

    class Meta:
        verbose_name = "Currency"
        verbose_name_plural = "Currencies"

    def __str__(self):
        return self.name


