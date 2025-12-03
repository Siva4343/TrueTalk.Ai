import json
import jwt
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from .models import ChatRoom, Message, UserStatus

class JWTAuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        query_string = scope.get('query_string', b'').decode()
        token = None
        
        # Extract token from query string
        for param in query_string.split('&'):
            if param.startswith('token='):
                token = param.split('=')[1]
                break
        
        if token:
            try:
                # Decode JWT token
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('user_id')
                if user_id:
                    scope['user'] = await self.get_user(user_id)
            except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
                scope['user'] = None
        else:
            scope['user'] = None
        
        return await self.app(scope, receive, send)

    @database_sync_to_async
    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)
            return
        
        self.user_id = str(self.user.id)
        self.user_group = f'user_{self.user_id}'
        
        # Join user group
        await self.channel_layer.group_add(
            self.user_group,
            self.channel_name
        )
        
        # Update user status
        await self.update_user_status(True)
        
        await self.accept()
        
        # Send connected message
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'WebSocket connected successfully'
        }))

    async def disconnect(self, close_code):
        # Update user status
        if hasattr(self, 'user') and self.user:
            await self.update_user_status(False)
        
        # Leave user group
        if hasattr(self, 'user_group'):
            await self.channel_layer.group_discard(
                self.user_group,
                self.channel_name
            )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'join_room':
            await self.handle_join_room(data)
        elif message_type == 'leave_room':
            await self.handle_leave_room(data)
        elif message_type == 'send_message':
            await self.handle_send_message(data)
        elif message_type == 'typing':
            await self.handle_typing(data)
        elif message_type == 'read_receipt':
            await self.handle_read_receipt(data)
        elif message_type == 'reaction':
            await self.handle_reaction(data)
        elif message_type == 'delete_message':
            await self.handle_delete_message(data)

    async def handle_join_room(self, data):
        room_id = data.get('room_id')
        if room_id:
            room_group = f'chat_{room_id}'
            await self.channel_layer.group_add(
                room_group,
                self.channel_name
            )
            
            # Send join notification
            await self.channel_layer.group_send(
                room_group,
                {
                    'type': 'user_joined',
                    'user_id': self.user_id,
                    'username': self.user.username,
                }
            )

    async def handle_leave_room(self, data):
        room_id = data.get('room_id')
        if room_id:
            room_group = f'chat_{room_id}'
            await self.channel_layer.group_discard(
                room_group,
                self.channel_name
            )

    async def handle_send_message(self, data):
        room_id = data.get('room_id')
        content = data.get('content')
        message_type = data.get('message_type', 'text')
        
        if not room_id or not content:
            return
        
        # Save message to database
        message = await self.save_message(room_id, content, message_type, data)
        
        # Send to room group
        await self.channel_layer.group_send(
            f'chat_{room_id}',
            {
                'type': 'chat_message',
                'message': await self.serialize_message(message),
                'sender_id': self.user_id
            }
        )
        
        # Send notification to room participants
        await self.send_message_notification(room_id, message)

    async def handle_typing(self, data):
        room_id = data.get('room_id')
        is_typing = data.get('is_typing')
        
        if room_id:
            await self.channel_layer.group_send(
                f'chat_{room_id}',
                {
                    'type': 'typing_indicator',
                    'user_id': self.user_id,
                    'username': self.user.username,
                    'is_typing': is_typing
                }
            )
            
            # Update typing status in database
            await self.update_typing_status(room_id, is_typing)

    async def handle_read_receipt(self, data):
        message_id = data.get('message_id')
        await self.mark_message_as_read(message_id)
        
        # Notify sender that message was read
        message = await self.get_message(message_id)
        if message and message.sender != self.user:
            await self.channel_layer.group_send(
                f'user_{message.sender.id}',
                {
                    'type': 'message_read',
                    'message_id': str(message_id),
                    'reader_id': self.user_id
                }
            )

    async def handle_reaction(self, data):
        message_id = data.get('message_id')
        emoji = data.get('emoji')
        
        reaction = await self.save_reaction(message_id, emoji)
        
        if reaction:
            # Get message room
            message = await self.get_message(message_id)
            if message:
                await self.channel_layer.group_send(
                    f'chat_{message.room.id}',
                    {
                        'type': 'message_reaction',
                        'message_id': str(message_id),
                        'user_id': self.user_id,
                        'emoji': emoji
                    }
                )

    async def handle_delete_message(self, data):
        message_id = data.get('message_id')
        delete_for_all = data.get('delete_for_all', False)
        
        deleted = await self.delete_message(message_id, delete_for_all)
        
        if deleted:
            message = await self.get_message(message_id)
            if message:
                await self.channel_layer.group_send(
                    f'chat_{message.room.id}',
                    {
                        'type': 'message_deleted',
                        'message_id': str(message_id),
                        'deleted_for_all': delete_for_all,
                        'deleted_by': self.user_id
                    }
                )

    # Handler methods for group events
    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message',
            'data': event['message']
        }))

    async def typing_indicator(self, event):
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'user_id': event['user_id'],
            'username': event['username'],
            'is_typing': event['is_typing']
        }))

    async def user_joined(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_joined',
            'user_id': event['user_id'],
            'username': event['username']
        }))

    async def user_left(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'user_id': event['user_id'],
            'username': event['username']
        }))

    async def message_read(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message_read',
            'message_id': event['message_id'],
            'reader_id': event['reader_id']
        }))

    async def message_reaction(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message_reaction',
            'message_id': event['message_id'],
            'user_id': event['user_id'],
            'emoji': event['emoji']
        }))

    async def message_deleted(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message_deleted',
            'message_id': event['message_id'],
            'deleted_for_all': event['deleted_for_all'],
            'deleted_by': event['deleted_by']
        }))

    async def user_status_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_status',
            'user_id': event['user_id'],
            'is_online': event['is_online']
        }))

    # Database operations
    @database_sync_to_async
    def update_user_status(self, is_online):
        status, created = UserStatus.objects.get_or_create(user=self.user)
        status.is_online = is_online
        status.save()

    @database_sync_to_async
    def save_message(self, room_id, content, message_type, data):
        try:
            room = ChatRoom.objects.get(id=room_id)
            message = Message.objects.create(
                room=room,
                sender=self.user,
                message_type=message_type,
                content=content
            )
            
            # Handle additional data based on message type
            if message_type == 'location':
                message.latitude = data.get('latitude')
                message.longitude = data.get('longitude')
                message.location_name = data.get('location_name')
                message.save()
            elif message_type == 'file':
                # File handling would be done separately via API
                pass
                
            return message
        except ChatRoom.DoesNotExist:
            return None

    @database_sync_to_async
    def serialize_message(self, message):
        from .serializers import MessageSerializer
        return MessageSerializer(message).data

    @database_sync_to_async
    def update_typing_status(self, room_id, is_typing):
        status, created = UserStatus.objects.get_or_create(user=self.user)
        if is_typing:
            try:
                room = ChatRoom.objects.get(id=room_id)
                status.typing_in = room
            except ChatRoom.DoesNotExist:
                pass
        else:
            status.typing_in = None
        status.save()

    @database_sync_to_async
    def mark_message_as_read(self, message_id):
        try:
            message = Message.objects.get(id=message_id)
            message.read_by.add(self.user)
            return True
        except Message.DoesNotExist:
            return False

    @database_sync_to_async
    def get_message(self, message_id):
        try:
            return Message.objects.get(id=message_id)
        except Message.DoesNotExist:
            return None

    @database_sync_to_async
    def save_reaction(self, message_id, emoji):
        try:
            message = Message.objects.get(id=message_id)
            # Remove existing reaction from this user
            message.reactions.pop(str(self.user.id), None)
            # Add new reaction
            message.reactions[str(self.user.id)] = emoji
            message.save()
            return True
        except Message.DoesNotExist:
            return False

    @database_sync_to_async
    def delete_message(self, message_id, delete_for_all):
        try:
            message = Message.objects.get(id=message_id)
            
            if delete_for_all and message.sender == self.user:
                message.deleted_for_all = True
                message.is_deleted = True
                message.deleted_by = self.user
                message.save()
                return True
            elif not delete_for_all:
                message.is_deleted = True
                message.save()
                return True
            return False
        except Message.DoesNotExist:
            return False

    async def send_message_notification(self, room_id, message):
        # Get all participants except sender
        participants = await self.get_room_participants(room_id)
        
        for participant in participants:
            if participant.id != self.user.id:
                # Check if participant is online
                is_online = await self.is_user_online(participant.id)
                if not is_online:
                    # Here you could send push notification
                    pass

    @database_sync_to_async
    def get_room_participants(self, room_id):
        try:
            room = ChatRoom.objects.get(id=room_id)
            return list(room.participants.all())
        except ChatRoom.DoesNotExist:
            return []

    @database_sync_to_async
    def is_user_online(self, user_id):
        try:
            status = UserStatus.objects.get(user_id=user_id)
            return status.is_online
        except UserStatus.DoesNotExist:
            return False


class ChatRoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        
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
        
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': data['message'],
                'sender': data.get('sender', 'anonymous')
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'sender': event['sender']
        }))


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)
            return
        
        self.notification_group = f'notifications_{self.user.id}'
        
        await self.channel_layer.group_add(
            self.notification_group,
            self.channel_name
        )
        
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.notification_group,
            self.channel_name
        )

    async def send_notification(self, event):
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'title': event['title'],
            'message': event['message'],
            'notification_type': event.get('type', 'info'),
            'timestamp': event.get('timestamp')
        }))