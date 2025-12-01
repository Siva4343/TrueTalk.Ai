import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Project.settings')

# Ensure Django apps are loaded before importing anything that touches models
django.setup()

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

import video.routing

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(
            video.routing.websocket_urlpatterns
        )
    ),
})