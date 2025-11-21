
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.http import FileResponse
from .models import SharedFile
from .serializers import SharedFileSerializer

# Upload + List files
class SharedFileListCreateView(generics.ListCreateAPIView):
    queryset = SharedFile.objects.all()
    serializer_class = SharedFileSerializer


# Download file
@api_view(['GET'])
def download_file(request, pk):
    try:
        file_obj = SharedFile.objects.get(pk=pk)
    except SharedFile.DoesNotExist:
        return Response({"error": "File not found"}, status=404)

    file_handle = file_obj.file.open()
    response = FileResponse(file_handle)
    return response

