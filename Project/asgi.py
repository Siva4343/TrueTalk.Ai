# backend/asgi.py
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

# HTTP application (Django)
django_asgi_app = get_asgi_application()

# Try to create a Channels ProtocolTypeRouter for websockets.
# If channels is not installed, we fall back to the Django ASGI app and print a clear error.
try:
    from channels.routing import ProtocolTypeRouter, URLRouter
    from channels.auth import AuthMiddlewareStack
    import Metting.routing as metting_routing  # import your app routing module

    application = ProtocolTypeRouter({
        "http": django_asgi_app,
        "websocket": AuthMiddlewareStack(
            URLRouter(
                metting_routing.websocket_urlpatterns
            )
        ),
    })

except ModuleNotFoundError as exc:
    # Channels not installed — provide clear message but still serve HTTP.
    # This prevents a confusing "ModuleNotFoundError" traceback at runtime.
    missing = str(exc).replace("No module named ", "")
    print(f"[ASGI] Warning: channels not available ({missing}). WebSocket support disabled.")
    application = django_asgi_app

