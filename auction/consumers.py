import json
from channels.generic.websocket import AsyncWebsocketConsumer

class AuctionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = 'auction_group'
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)

        if data['type'] == 'auction_start':
            await self.send_auction_start_end(data)
        elif data['type'] == 'new_bid':
            await self.broadcast_new_bid(data)

    async def send_auction_start_end(self, event):
        # Broadcasts the start or end of the auction
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'refresh_page',  # This is the message that triggers the page refresh
            }
        )

    async def broadcast_new_bid(self, event):
        bid_data = event['bid_data']
        await self.send(text_data=json.dumps({
            'type': 'broadcast_new_bid',
            'team_name': bid_data['team_name'],
            'price': bid_data['price'],
            'player_name': bid_data['player_name']
        }))

    # Add the missing handler for 'refresh_page'
    async def refresh_page(self, event):
        # Send a message to the WebSocket to refresh the page or update the UI
        await self.send(text_data=json.dumps({
            'type': 'refresh_page',
            'message': 'Page should refresh'
        }))
