    
# Create your models here.
from django.db import models

class BusinessProfile(models.Model):
    name = models.CharField(max_length=100)
    tagline = models.CharField(max_length=150, blank=True)
    description = models.TextField(blank=True)
    gmail = models.EmailField()
    website = models.URLField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    business_hours = models.CharField(max_length=100, blank=True)
    services = models.TextField(blank=True)
    social_links = models.JSONField(blank=True, null=True)
    photo = models.ImageField(upload_to='profile_photos/', blank=True)

    def __str__(self):
        return self.name