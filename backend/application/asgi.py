import os
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'application.settings')
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

http_application = get_asgi_application()
from application.ws_routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": http_application,
    'websocket': AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                websocket_urlpatterns
            )
        )
    ),
})