from django.urls import path
from .consumers import ChatConsumer

websocket_urlpatterns = [
    path("ws/contact/", ChatConsumer.as_asgi()),
]
