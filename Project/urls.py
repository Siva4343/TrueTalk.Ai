"""
URL configuration for Project project.
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/chat/", include("ChatRoom.urls")),
    path("api/logic/", include("ChatLogic.urls")),
]