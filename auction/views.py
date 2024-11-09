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
        team_players = Sale.objects.filter(team=team, is_sold=True)
        total_players = team_players.count() or 0
        non_legend_players = team_players.filter(player__legend=False).count() or 0

        team_data[team.name] = {
            'remaining_purse': remaining_purse,
            'total_players': total_players,
            'non_legend_players': non_legend_players
        }

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
    sold_players = Sale.objects.filter(is_sold=True).order_by('-id')
    unsold_players = all_players.exclude(id__in=sold_players.values_list('player_id', flat=True))
    ongoing_player = Sale.objects.filter(is_sold=False).first()

    teams = Team.objects.all()
    team_data = {}
    
    for team in teams:
        total_spent = Sale.objects.filter(team=team, is_sold=True).aggregate(Sum('price'))['price__sum'] or 0
        remaining_purse = team.purse - total_spent
        team_players = Sale.objects.filter(team=team, is_sold=True)
        total_players = team_players.count() or 0
        non_legend_players = team_players.filter(player__legend=False).count() or 0
        
        team_data[team.name] = {
            'remaining_purse': remaining_purse,
            'total_players': total_players,
            'non_legend_players': non_legend_players
        }

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
        my_total_players = bought_players.count() or 0
        my_total_non_legend_players = bought_players.filter(player__legend=False).count() or 0
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
        'my_total_players': my_total_players,
        'my_total_non_legend_players': my_total_non_legend_players,
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
        last_bid_price = last_bid.price
        if last_bid_price < Decimal('2'):
            increment = Decimal('0.1')
        elif Decimal('2') <= last_bid_price < Decimal('5'):
            increment = Decimal('0.2')
        else:  
            increment = Decimal('0.25')
        new_bid_amount = last_bid_price + increment
    else:
        new_bid_amount = ongoing_player.player.base_price

    user_team = request.user.team
    if not last_bid or  last_bid.team != user_team:    
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
