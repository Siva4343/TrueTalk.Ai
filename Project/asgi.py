import os
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
import Metting.routing   # ← your correct app name

# IMPORTANT: Project folder name is "Project" (case-sensitive)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Project.settings')

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,

    "websocket": AuthMiddlewareStack(
        URLRouter(
            Metting.routing.websocket_urlpatterns
        )
    ),
})
