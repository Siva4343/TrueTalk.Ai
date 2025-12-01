# video/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import logging

logger = logging.getLogger(__name__)

class CallConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # room_name provided in URL routing
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.group_name = f"call_{self.room_name}"

        # add user to group
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # notify others that a new user joined
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'user.join',
                'channel': self.channel_name,
            }
        )

    async def disconnect(self, close_code):
        # remove from group
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

        # notify others
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'user.leave',
                'channel': self.channel_name,
            }
        )

    async def receive(self, text_data=None, bytes_data=None):
        if text_data is None:
            return
        data = json.loads(text_data)
        action = data.get('action')

        # Normalize payloads and broadcast to group (except sender) depending on action
        if action == 'offer':
            # { action: 'offer', offer: <sdp>, to: <optional-channel> }
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'signal.offer',
                    'offer': data.get('offer'),
                    'from_channel': self.channel_name,
                    'to_channel': data.get('to'),
                }
            )

        elif action == 'answer':
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'signal.answer',
                    'answer': data.get('answer'),
                    'from_channel': self.channel_name,
                    'to_channel': data.get('to'),
                }
            )

        elif action == 'candidate':
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'signal.candidate',
                    'candidate': data.get('candidate'),
                    'from_channel': self.channel_name,
                    'to_channel': data.get('to'),
                }
            )

        elif action == 'leave':
            # user voluntarily leaves
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'user.leave',
                    'channel': self.channel_name,
                }
            )

        elif action == 'join':
            # optional handler if you want explicit join message
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'user.join',
                    'channel': self.channel_name,
                }
            )

    # Group handlers: ensure sender doesn't receive its own events
    async def signal_offer(self, event):
        if event.get('from_channel') == self.channel_name:
            return
        # If to_channel is set, deliver only to that channel (for direct peer-to-peer)
        if event.get('to_channel') and event.get('to_channel') != self.channel_name:
            return
        await self.send(text_data=json.dumps({
            'action': 'offer',
            'offer': event.get('offer'),
            'from': event.get('from_channel')
        }))

    async def signal_answer(self, event):
        if event.get('from_channel') == self.channel_name:
            return
        if event.get('to_channel') and event.get('to_channel') != self.channel_name:
            return
        await self.send(text_data=json.dumps({
            'action': 'answer',
            'answer': event.get('answer'),
            'from': event.get('from_channel')
        }))

    async def signal_candidate(self, event):
        if event.get('from_channel') == self.channel_name:
            return
        if event.get('to_channel') and event.get('to_channel') != self.channel_name:
            return
        await self.send(text_data=json.dumps({
            'action': 'candidate',
            'candidate': event.get('candidate'),
            'from': event.get('from_channel')
        }))

    async def user_join(self, event):
        if event.get('channel') == self.channel_name:
            return
        await self.send(text_data=json.dumps({
            'action': 'user-joined',
            'id': event.get('channel')
        }))

    async def user_leave(self, event):
        if event.get('channel') == self.channel_name:
            return
        await self.send(text_data=json.dumps({
            'action': 'user-left',
            'id': event.get('channel')
        }))