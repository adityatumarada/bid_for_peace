from django.db import models
from django.contrib.auth.models import User

class Team(models.Model):
    name = models.CharField(max_length=100)
    purse = models.DecimalField(max_digits=10, decimal_places=2, default=120)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='team')

    def __str__(self):
        return self.name

class Player(models.Model):
    name = models.CharField(max_length=50)
    position = models.CharField(max_length=10, default="")
    rating = models.DecimalField(max_digits=4, decimal_places=0, default=0)
    bag = models.CharField(max_length=10, default="")
    legend = models.BooleanField(default=False)
    description = models.CharField(max_length=100, default="")
    base_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name
    
class Bid(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)

class Sale(models.Model):
    player = models.OneToOneField(Player, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_sold = models.BooleanField(default=False)