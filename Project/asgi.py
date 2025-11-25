"""
ASGI config for Project project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Project.settings')

application = get_asgi_application()

# meetings/asgi.py
# yourproject/asgi.py
import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

from django.core.asgi import get_asgi_application
import Meeting.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Project.settings')
django.setup()

# HTTP -> Django ASGI application, WebSocket -> Channels consumers
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            Meeting.routing.websocket_urlpatterns
        )
    ),
})

