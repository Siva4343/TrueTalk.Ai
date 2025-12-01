import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import CallSession, CallLog

class CallConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'call_{self.room_name}'
        self.user = self.scope["user"]

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

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data['type']

        if message_type == 'offer':
            # Send offer to other users in the room
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'call_message',
                    'message': data,
                    'sender_channel_name': self.channel_name
                }
            )
        
        elif message_type == 'answer':
            # Send answer to other users
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'call_message',
                    'message': data,
                    'sender_channel_name': self.channel_name
                }
            )
        
        elif message_type == 'ice-candidate':
            # Send ICE candidate to other users
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'call_message',
                    'message': data,
                    'sender_channel_name': self.channel_name
                }
            )
        
        elif message_type == 'join_call':
            await self.handle_join_call(data)
        
        elif message_type == 'leave_call':
            await self.handle_leave_call(data)
        
        elif message_type == 'call_end':
            await self.handle_call_end(data)

    async def call_message(self, event):
        # Don't send the message back to the sender
        if self.channel_name != event['sender_channel_name']:
            await self.send(text_data=json.dumps(event['message']))

    @database_sync_to_async
    def handle_join_call(self, data):
        try:
            call_session = CallSession.objects.get(room_name=self.room_name)
            CallLog.objects.create(
                call_session=call_session,
                user=self.user,
                action='joined'
            )
            
            # Update call status if this is the receiver joining
            if self.user == call_session.receiver and call_session.status == 'initiated':
                call_session.status = 'ongoing'
                call_session.save()
                
        except CallSession.DoesNotExist:
            pass

    @database_sync_to_async
    def handle_leave_call(self, data):
        try:
            call_session = CallSession.objects.get(room_name=self.room_name)
            CallLog.objects.create(
                call_session=call_session,
                user=self.user,
                action='left'
            )
        except CallSession.DoesNotExist:
            pass

    @database_sync_to_async
    def handle_call_end(self, data):
        try:
            call_session = CallSession.objects.get(room_name=self.room_name)
            call_session.status = 'ended'
            call_session.save()
            
            CallLog.objects.create(
                call_session=call_session,
                user=self.user,
                action='ended_call'
            )
        except CallSession.DoesNotExist:
            pass