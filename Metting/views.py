from django.shortcuts import render
from rest_framework import generics
from .models import Caption
from .serializers import CaptionSerializer

class CaptionListCreateView(generics.ListCreateAPIView):
    queryset = Caption.objects.all().order_by('-created_at')
    serializer_class = CaptionSerializer

# Create your views here.
