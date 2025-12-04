# backend/asgi.py
import os
import sys
from django.core.asgi import get_asgi_application

# Ensure correct settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Project.settings")

# HTTP app
django_asgi_app = get_asgi_application()

# Try to build Channels ProtocolTypeRouter
try:
    from channels.routing import ProtocolTypeRouter, URLRouter
    from channels.auth import AuthMiddlewareStack
except Exception as e:
    print("[ASGI] channels import failed:", repr(e), file=sys.stderr)
    application = django_asgi_app
else:
    try:
        # import the routing module for your websocket consumers
        # adapt module path if your app name is different
        from Metting import routing as metting_routing
    except Exception as e:
        # Print helpful error and fail to make it obvious
        print("[ASGI] Failed to import Metting.routing:", repr(e), file=sys.stderr)
        application = django_asgi_app
    else:
        application = ProtocolTypeRouter({
            "http": django_asgi_app,
            "websocket": AuthMiddlewareStack(
                URLRouter(metting_routing.websocket_urlpatterns)
            ),
        })
