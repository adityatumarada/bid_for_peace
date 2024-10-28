# views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Player, Team, Sale, Bid
from django.db.models import Sum
from django.contrib import messages
from decimal import Decimal
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_auction_view')
        else:
            return redirect('user_auction_view')

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if request.user.is_staff:
                return redirect('admin_auction_view')
            else:
                return redirect('user_auction_view')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})

    return render(request, 'login.html')

@login_required
def logout_view(request):
    logout(request)
    return redirect('login_view')


@login_required
def admin_auction_view(request):
    if not request.user.is_staff:
        return redirect('user_auction_view')
    
    all_players = Player.objects.all()
    sold_players = Sale.objects.filter(is_sold=True)
    unsold_players = all_players.exclude(id__in=sold_players.values_list('player_id', flat=True))
    ongoing_player = Sale.objects.filter(is_sold=False).first()

    teams = Team.objects.all()
    team_data = {}
    
    for team in teams:
        total_spent = Sale.objects.filter(team=team, is_sold=True).aggregate(Sum('price'))['price__sum'] or 0
        remaining_purse = team.purse - total_spent
        team_data[team.name] = remaining_purse

    bids = []

    if ongoing_player:
        bids = Bid.objects.filter(player=ongoing_player.player).order_by('-price')
    
    return render(request, 'auction/admin_auction.html', {
        'sold_players': sold_players,
        'unsold_players': unsold_players,
        'ongoing_player': ongoing_player.player if ongoing_player else None,
        'bids': bids,
        'team_data': team_data
    })


@login_required
def user_auction_view(request):
    if request.user.is_staff:
        return redirect('admin_auction_view')
    
    all_players = Player.objects.all()
    sold_players = Sale.objects.filter(is_sold=True)
    unsold_players = all_players.exclude(id__in=sold_players.values_list('player_id', flat=True))
    ongoing_player = Sale.objects.filter(is_sold=False).first()

    teams = Team.objects.all()
    team_data = {}
    
    for team in teams:
        total_spent = Sale.objects.filter(team=team, is_sold=True).aggregate(Sum('price'))['price__sum'] or 0
        remaining_purse = team.purse - total_spent
        team_data[team.name] = remaining_purse

    bids = []
    bought_players = [] 
    remaining_purse = Decimal('0.0')

    if ongoing_player:
        bids = Bid.objects.filter(player=ongoing_player.player).order_by('-price')

    try:
        user_team = request.user.team 
        bought_players = Sale.objects.filter(team=user_team, is_sold=True).select_related('player')
        cost = Sale.objects.filter(team=user_team, is_sold=True).aggregate(Sum('price'))['price__sum']
        if not cost:
            cost = Decimal('0.0')
        remaining_purse = user_team.purse - cost
    except Team.DoesNotExist:
        bought_players = [] 

    # Render the user auction view with all necessary context
    return render(request, 'auction/user_auction.html', {
        'sold_players': sold_players,
        'unsold_players': unsold_players,
        'ongoing_player': ongoing_player.player if ongoing_player else None,
        'bids': bids,
        'team_data': team_data,
        'bought_players': bought_players,  
        'remaining_purse': remaining_purse
    })

@login_required
def start_auction(request, player_id):
    if not request.user.is_staff:
        return redirect('user_auction_view')

    player = Player.objects.get(id=player_id)
    sale = Sale.objects.create(player=player)
    sale.save()

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "auction_group",
        {
            "type": "send_auction_start_end",
        }
    )

    return redirect('admin_auction_view')

@login_required
def end_auction(request, auction_id):
    if not request.user.is_staff:
        return redirect('user_auction_view')

    auction = Sale.objects.get(is_sold=False)
    auction.is_sold = True
    auction.save()

    # Retrieve the highest bid for the auction
    highest_bid = Bid.objects.filter(player=auction.player).order_by('-price').first()

    if highest_bid:
        auction.team = highest_bid.team
        auction.price = highest_bid.price
        auction.save()

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "auction_group",
        {
            "type": "send_auction_start_end",
        }
    )

    return redirect('admin_auction_view')

@login_required
def place_bid(request, player_id):
    
    if request.user.is_staff:
        return redirect('admin_auction_view')

    ongoing_player = get_object_or_404(Sale, is_sold=False) 

    last_bid = Bid.objects.filter(player=ongoing_player.player).order_by('-price').first()
    if last_bid:
        new_bid_amount = last_bid.price + Decimal('0.1') 
    else:
        new_bid_amount = ongoing_player.player.base_price  
    
    user_team = request.user.team
    total_spent = Sale.objects.filter(team=user_team, is_sold=True).aggregate(Sum('price'))['price__sum'] or 0
    remaining_purse = user_team.purse - total_spent
    
    if remaining_purse >= new_bid_amount:
        new_bid = Bid.objects.create(player=ongoing_player.player, team=user_team, price=new_bid_amount)
        
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'auction_group',
            {
                'type': 'broadcast_new_bid',
                'bid_data': {
                    'team_name': user_team.name,
                    'player_name': ongoing_player.player.name,
                    'price': str(new_bid_amount)
                }
            }
        )

    return redirect('user_auction_view')



