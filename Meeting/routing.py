# Meeting/routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Support both UUID format and meeting code format (e.g., ssok-xqqm-n9pe)
    re_path(r'ws/meeting/(?P<meeting_id>[0-9a-zA-Z-]+)/$', consumers.CallConsumer.as_asgi()),
]
