from django.urls import path
from .consumers import LiveCaptionConsumer

websocket_urlpatterns = [
    path("ws/captions/", LiveCaptionConsumer.as_asgi()),
]
