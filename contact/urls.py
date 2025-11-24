from django.urls import path
from .views import MessageListAPI

urlpatterns = [
    path("messages/", MessageListAPI.as_view(), name="messages-list"),
]
