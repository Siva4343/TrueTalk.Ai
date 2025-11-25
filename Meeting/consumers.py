# meetings/consumers.py
import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Meeting, ChatMessage, Participant, Notepad, Reaction

User = get_user_model()

class MeetingConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.meeting_id = self.scope['url_route']['kwargs']['meeting_id']
        self.group_name = f"meeting_{self.meeting_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # notify presence (optional)
        await self.send_json({'type':'connected','meeting':self.meeting_id})

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        t = content.get('type')
        if t == 'chat.message':
            text = content.get('text', '')
            msg = await self.create_chat_message(text)
            payload = {
                'type': 'broadcast.message',
                'message': {
                    'id': str(msg.id),
                    'content': msg.content,
                    'sender': msg.sender.username if msg.sender else None,
                    'created_at': msg.created_at.isoformat()
                }
            }
            await self.channel_layer.group_send(self.group_name, payload)

        elif t == 'notepad.update':
            new = content.get('content', '')
            user_id = content.get('user_id')
            await self.update_notepad(new, user_id)
            await self.channel_layer.group_send(self.group_name, {
                'type': 'broadcast.notepad',
                'content': new,
                'editor': user_id
            })

        elif t in ('signal.offer','signal.answer','signal.ice'):
            # forward raw signaling to group (in prod target specific peer)
            await self.channel_layer.group_send(self.group_name, {
                'type': 'signal.forward',
                'payload': content
            })

        elif t == 'reaction.add':
            emoji = content.get('emoji')
            target_message = content.get('target_message')
            r = await self.create_reaction(emoji, target_message)
            await self.channel_layer.group_send(self.group_name, {
                'type': 'broadcast.reaction',
                'reaction': {'id': str(r.id), 'emoji': r.emoji, 'target_message': str(r.target_message.id) if r.target_message else None}
            })

    # event handlers
    async def broadcast_message(self, event):
        await self.send_json({'type':'chat.message', 'message': event['message']})

    async def broadcast_notepad(self, event):
        await self.send_json({'type':'notepad.update', 'content': event['content'], 'editor': event.get('editor')})

    async def signal_forward(self, event):
        await self.send_json(event['payload'])

    async def broadcast_reaction(self, event):
        await self.send_json({'type':'reaction.add', 'reaction': event['reaction']})

    # DB helpers
    @database_sync_to_async
    def create_chat_message(self, text):
        meeting = Meeting.objects.get(pk=self.meeting_id)
        sender = None
        if self.scope.get('user') and self.scope['user'].is_authenticated:
            sender = self.scope['user']
        return ChatMessage.objects.create(meeting=meeting, sender=sender, content=text)

    @database_sync_to_async
    def update_notepad(self, content, user_id):
        meeting = Meeting.objects.get(pk=self.meeting_id)
        notepad, created = Notepad.objects.get_or_create(meeting=meeting)
        if user_id:
            try:
                user = User.objects.get(pk=user_id)
            except Exception:
                user = None
        else:
            user = self.scope.get('user') if self.scope.get('user').is_authenticated else None
        notepad.content = content
        notepad.last_edited_by = user
        notepad.save()
        return notepad

    @database_sync_to_async
    def create_reaction(self, emoji, target_message_id):
        meeting = Meeting.objects.get(pk=self.meeting_id)
        sender = self.scope.get('user') if (self.scope.get('user') and self.scope['user'].is_authenticated) else None
        target_msg = None
        if target_message_id:
            try:
                target_msg = ChatMessage.objects.get(pk=target_message_id)
            except ChatMessage.DoesNotExist:
                target_msg = None
        return Reaction.objects.create(meeting=meeting, sender=sender, emoji=emoji, target_message=target_msg)
