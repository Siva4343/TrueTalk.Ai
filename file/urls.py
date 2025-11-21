from django.urls import path
from .views import SharedFileListCreateView, download_file

urlpatterns = [
    path('upload/', SharedFileListCreateView.as_view(), name='file-upload'),
    path('download/<int:pk>/', download_file, name='file-download'),
]
