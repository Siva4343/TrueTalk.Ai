from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets
from .models import BusinessProfile
from .serializers import BusinessProfileSerializer

class BusinessProfileViewSet(viewsets.ModelViewSet):
    queryset = BusinessProfile.objects.all()
    serializer_class = BusinessProfileSerializer
    