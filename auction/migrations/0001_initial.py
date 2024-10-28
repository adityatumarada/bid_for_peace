# Generated by Django 4.2.16 on 2024-10-26 21:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Player',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('base_price', models.DecimalField(decimal_places=2, max_digits=10)),
            ],
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('purse', models.DecimalField(decimal_places=2, default=1000000, max_digits=10)),
            ],
        ),
        migrations.CreateModel(
            name='Sales',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('player', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auction.player')),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auction.team')),
            ],
        ),
        migrations.CreateModel(
            name='Bid',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('player', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auction.player')),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auction.team')),
            ],
        ),
    ]
