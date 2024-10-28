# auction/admin.py

from django.contrib import admin
from .models import Player, Team, Bid, Sale

# Register the Team model
@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'purse')

# Register the Player model
@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('name', 'base_price') 

# Register the Team model
@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ('player', 'team', 'price')

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('player', 'team', 'price')
