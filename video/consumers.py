import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from django.utils import timezone
from .models import CallSession, CallLog

logger = logging.getLogger(__name__)
# ...existing code...
import json
from channels.generic.websocket import AsyncWebSocketConsumer

class CallConsumer(AsyncWebSocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'call_{self.room_name}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        
        # Broadcast to room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'call_message',
                'message': data
            }
        )

    async def call_message(self, event):
        # use json.dumps (not json.stringify)
        await self.send(text_data=json.dumps(event['message']))
# ...existing code...# ...existing code...
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/call/(?P<room_name>\w+)/$', consumers.CallConsumer.as_asgi()),
]
# ...existing code...# ...existing code...
import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
import backend.routing as backend_routing  # adjust if your app name differs

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TrueTalk.Ai.settings')  # adjust to your project.settings
django.setup()

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            backend_routing.websocket_urlpatterns
        )
    ),
})
# ...existing code...# ...existing code...
INSTALLED_APPS = [
    # ...existing apps...
    'channels',
    'backend',  # add your app name here if not present
]

ASGI_APPLICATION = 'TrueTalk.Ai.asgi.application'  # adjust project path if different

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}
# ...existing code...

class CallConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for handling WebRTC signaling
    Manages real-time communication for video/audio calls
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        try:
            self.room_name = self.scope['url_route']['kwargs']['room_name']
            self.room_group_name = f'call_{self.room_name}'
            self.user = self.scope.get("user")
            
            # Validate user
            if not self.user or not self.user.is_authenticated:
                logger.warning(f"Unauthenticated connection attempt to room: {self.room_name}")
                await self.close(code=4001)
                return
            
            # Join room group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            await self.accept()
            
            logger.info(f"User {self.user.username} connected to room: {self.room_name}")
            
            # Notify others in the room about the new participant
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_joined',
                    'user_id': self.user.id,
                    'username': self.user.username,
                    'sender_channel_name': self.channel_name
                }
            )
            
        except Exception as e:
            logger.error(f"Error in connect: {str(e)}")
            await self.close(code=4000)

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        try:
            # Notify others in the room about the participant leaving
            if hasattr(self, 'room_group_name') and hasattr(self, 'user'):
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'user_left',
                        'user_id': self.user.id,
                        'username': self.user.username,
                        'sender_channel_name': self.channel_name
                    }
                )
                
                # Leave room group
                await self.channel_layer.group_discard(
                    self.room_group_name,
                    self.channel_name
                )
                
                logger.info(f"User {self.user.username} disconnected from room: {self.room_name} (code: {close_code})")
        except Exception as e:
            logger.error(f"Error in disconnect: {str(e)}")

    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if not message_type:
                logger.warning(f"Message without type from {self.user.username}")
                await self.send_error("Message type is required")
                return
            
            logger.debug(f"Received {message_type} from {self.user.username} in room {self.room_name}")
            
            # Handle different message types
            if message_type == 'offer':
                await self.handle_webrtc_signal(data)
            
            elif message_type == 'answer':
                await self.handle_webrtc_signal(data)
            
            elif message_type == 'ice-candidate':
                await self.handle_webrtc_signal(data)
            
            elif message_type == 'join_call':
                await self.handle_join_call(data)
            
            elif message_type == 'leave_call':
                await self.handle_leave_call(data)
            
            elif message_type == 'call_end':
                await self.handle_call_end(data)
            
            elif message_type == 'mute_audio':
                await self.handle_media_toggle(data, 'audio', False)
            
            elif message_type == 'unmute_audio':
                await self.handle_media_toggle(data, 'audio', True)
            
            elif message_type == 'disable_video':
                await self.handle_media_toggle(data, 'video', False)
            
            elif message_type == 'enable_video':
                await self.handle_media_toggle(data, 'video', True)
            
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received: {str(e)}")
            await self.send_error("Invalid JSON format")
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            await self.send_error("Internal server error")

    async def handle_webrtc_signal(self, data):
        """Handle WebRTC signaling messages (offer, answer, ICE candidate)"""
        target_user = data.get('target_user_id')
        
        # Send to specific user or broadcast to room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'webrtc_signal',
                'message': data,
                'sender_channel_name': self.channel_name,
                'sender_user_id': self.user.id,
                'target_user_id': target_user
            }
        )

    async def webrtc_signal(self, event):
        """Send WebRTC signal to specific user or all except sender"""
        # Don't send back to sender
        if self.channel_name == event['sender_channel_name']:
            return
        
        # If target user specified, only send to that user
        target_user_id = event.get('target_user_id')
        if target_user_id and self.user.id != target_user_id:
            return
        
        await self.send(text_data=json.dumps(event['message']))

    async def handle_media_toggle(self, data, media_type, enabled):
        """Handle audio/video mute/unmute events"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'media_status',
                'media_type': media_type,
                'enabled': enabled,
                'user_id': self.user.id,
                'username': self.user.username,
                'sender_channel_name': self.channel_name
            }
        )

    async def media_status(self, event):
        """Send media status to all except sender"""
        if self.channel_name != event['sender_channel_name']:
            await self.send(text_data=json.dumps({
                'type': 'media_status',
                'media_type': event['media_type'],
                'enabled': event['enabled'],
                'user_id': event['user_id'],
                'username': event['username']
            }))

    async def user_joined(self, event):
        """Notify about user joining"""
        if self.channel_name != event['sender_channel_name']:
            await self.send(text_data=json.dumps({
                'type': 'user_joined',
                'user_id': event['user_id'],
                'username': event['username']
            }))

    async def user_left(self, event):
        """Notify about user leaving"""
        if self.channel_name != event['sender_channel_name']:
            await self.send(text_data=json.dumps({
                'type': 'user_left',
                'user_id': event['user_id'],
                'username': event['username']
            }))

    async def send_error(self, message):
        """Send error message to client"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message
        }))

    @database_sync_to_async
    def handle_join_call(self, data):
        """Handle user joining a call"""
        try:
            call_session = CallSession.objects.get(room_name=self.room_name)
            
            # Create join log
            CallLog.objects.create(
                call_session=call_session,
                user=self.user,
                action='joined'
            )
            
            # Update call status if receiver joining
            if self.user == call_session.receiver and call_session.status == 'initiated':
                call_session.status = 'ongoing'
                call_session.started_at = timezone.now()
                call_session.save()
                logger.info(f"Call {call_session.call_id} status updated to ongoing")
            
            return True
        except CallSession.DoesNotExist:
            logger.error(f"Call session not found for room: {self.room_name}")
            return False
        except Exception as e:
            logger.error(f"Error in handle_join_call: {str(e)}")
            return False

    @database_sync_to_async
    def handle_leave_call(self, data):
        """Handle user leaving a call"""
        try:
            call_session = CallSession.objects.get(room_name=self.room_name)
            
            CallLog.objects.create(
                call_session=call_session,
                user=self.user,
                action='left'
            )
            
            logger.info(f"User {self.user.username} left call {call_session.call_id}")
            return True
        except CallSession.DoesNotExist:
            logger.error(f"Call session not found for room: {self.room_name}")
            return False
        except Exception as e:
            logger.error(f"Error in handle_leave_call: {str(e)}")
            return False

    @database_sync_to_async
    def handle_call_end(self, data):
        """Handle call ending"""
        try:
            call_session = CallSession.objects.get(room_name=self.room_name)
            
            # Only update if call is not already ended
            if call_session.status not in ['ended', 'missed']:
                call_session.status = 'ended'
                call_session.ended_at = timezone.now()
                
                # Set started_at if it wasn't set
                if not call_session.started_at:
                    call_session.started_at = call_session.created_at
                
                call_session.save()
            
            CallLog.objects.create(
                call_session=call_session,
                user=self.user,
                action='ended_call'
            )
            
            logger.info(f"Call {call_session.call_id} ended by {self.user.username}")
            return True
        except CallSession.DoesNotExist:
            logger.error(f"Call session not found for room: {self.room_name}")
            return False
        except Exception as e:
            logger.error(f"Error in handle_call_end: {str(e)}")
            return False