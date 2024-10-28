import os
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
import auction.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bid_for_peace.settings')

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(
            auction.routing.websocket_urlpatterns
        )
    ),
})
