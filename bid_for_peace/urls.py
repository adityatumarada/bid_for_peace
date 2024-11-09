from django.contrib import admin
from django.urls import path
from auction.views import admin_auction_view, user_auction_view, login_view, logout_view, start_auction, end_auction, place_bid
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', login_view, name='login_view'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('admin_auction/', admin_auction_view, name='admin_auction_view'),
    path('auction/', user_auction_view, name='user_auction_view'),
    path('start_auction/<int:player_id>/', start_auction, name='start_auction'),
    path('end_auction/<int:auction_id>/', end_auction, name='end_auction'),
    path('place_bid/<int:player_id>/', place_bid, name='place_bid'),
]
