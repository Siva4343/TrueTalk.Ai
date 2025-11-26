from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.storage import default_storage
from django.conf import settings
import os

# Create your views here.

class FileUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        file_obj = request.data.get('file')
        if not file_obj:
            return Response({"error": "No file provided"}, status=400)
        
        # Save the file
        file_name = default_storage.save(file_obj.name, file_obj)
        file_url = default_storage.url(file_name)
        
        # In a real app, you'd probably upload to S3 or similar.
        # For local dev, we need to make sure MEDIA_URL is set up.
        
        return Response({
            "file_url": file_url,
            "file_name": file_name,
            "content_type": file_obj.content_type
        }, status=201)
