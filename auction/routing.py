from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/auction/', consumers.AuctionConsumer.as_asgi()),
]

