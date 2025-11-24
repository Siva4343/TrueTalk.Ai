import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Poll
from .serializers import PollSerializer

class PollConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.poll_id = self.scope['url_route']['kwargs']['poll_id']
        self.room_group_name = f'poll_{self.poll_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def poll_update(self, event):
        poll_id = event['poll_id']
        poll_data = await self.get_poll_data(poll_id)
        
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'poll_update',
            'poll': poll_data
        }))
    
    @database_sync_to_async
    def get_poll_data(self, poll_id):
        try:
            poll = Poll.objects.get(id=poll_id)
            serializer = PollSerializer(poll)
            return serializer.data
        except Poll.DoesNotExist:
            return None