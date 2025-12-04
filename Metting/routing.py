# Metting/routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Original simple route (keeps compatibility)
    re_path(r"ws/meet/(?P<room_id>\w+)/$", consumers.MeetConsumer.as_asgi()),

    # More explicit routes (use these if frontend expects these)
    re_path(r"ws/meet/(?P<room_id>\w+)/signaling/$", consumers.MeetConsumer.as_asgi()),
    re_path(r"ws/meet/(?P<room_id>\w+)/chat/$", consumers.MeetConsumer.as_asgi()),
]
