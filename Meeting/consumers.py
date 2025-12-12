# Meeting/consumers.py
import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from .models import Meeting

class CallConsumer(WebsocketConsumer):
    def connect(self):
        # Get meeting_id from URL route (can be UUID or meeting code)
        meeting_identifier = self.scope['url_route']['kwargs'].get('meeting_id', None)
        
        # Try to resolve meeting code to UUID
        if meeting_identifier:
            try:
                # Check if it's a meeting code (format: xxxx-xxxx-xxxx)
                if len(meeting_identifier.split('-')) == 3:
                    # It's a meeting code, look up the meeting
                    meeting = Meeting.objects.get(meeting_code=meeting_identifier)
                    self.meeting_id = str(meeting.id)
                else:
                    # It's a UUID
                    self.meeting_id = meeting_identifier
            except Meeting.DoesNotExist:
                # If meeting not found, still use the identifier
                self.meeting_id = meeting_identifier
        else:
            self.meeting_id = None
            
        self.room_group_name = f'meeting_{self.meeting_id}' if self.meeting_id else 'call_room'
        
        # Initialize user attributes (will be set properly on login event)
        self.user_id = None
        self.user_name = 'Anonymous'
        
        # Join room group
        if self.meeting_id:
            async_to_sync(self.channel_layer.group_add)(
                self.room_group_name,
                self.channel_name
            )
        
        self.accept()

        # Response to client that we are connected
        self.send(text_data=json.dumps({
            'type': 'connection',
            'data': {
                'message': 'Connected to meeting',
                'meeting_id': self.meeting_id
            }
        }))

    def disconnect(self, close_code):
        # Leave room group
        if hasattr(self, 'room_group_name'):
            # Notify others that user left
            if hasattr(self, 'user_name'):
                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name,
                    {
                        'type': 'user_left',
                        'data': {
                            'user': self.user_name
                        }
                    }
                )
            
            async_to_sync(self.channel_layer.group_discard)(
                self.room_group_name,
                self.channel_name
            )

    # Receive message from client WebSocket
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        
        event_type = text_data_json.get('type')
        data = text_data_json.get('data', {})

        if event_type == 'login':
            # User joins the meeting
            self.user_name = data.get('name', 'Anonymous')
            self.user_id = data.get('userId', self.channel_name)
            
            # Notify others that user joined
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'user_joined',
                    'data': {
                        'user': self.user_name,
                        'userId': self.user_id
                    }
                }
            )
        
        elif event_type == 'offer':
            # WebRTC offer - send to specific user or broadcast
            target_user = data.get('target')
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'webrtc_offer',
                    'data': {
                        'offer': data.get('offer'),
                        'sender': self.user_id,
                        'target': target_user
                    }
                }
            )
        
        elif event_type == 'answer':
            # WebRTC answer
            target_user = data.get('target')
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'webrtc_answer',
                    'data': {
                        'answer': data.get('answer'),
                        'sender': self.user_id,
                        'target': target_user
                    }
                }
            )
        
        elif event_type == 'ice-candidate':
            # ICE candidate
            target_user = data.get('target')
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'ice_candidate',
                    'data': {
                        'candidate': data.get('candidate'),
                        'sender': self.user_id,
                        'target': target_user
                    }
                }
            )

        elif event_type == 'chat_message':
            # Chat message - broadcast to all in room
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'chat_message_received',
                    'data': {
                        'sender': self.user_name,
                        'senderId': self.user_id,
                        'content': data.get('content'),
                        'timestamp': data.get('timestamp')
                    }
                }
            )
        
        elif event_type == 'reaction':
            # Reaction - broadcast to all
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'reaction_received',
                    'data': {
                        'reaction': data.get('reaction'),
                        'userName': self.user_name
                    }
                }
            )

    # Handler methods for group messages
    def user_joined(self, event):
        """Send user joined notification"""
        self.send(text_data=json.dumps({
            'type': 'user_joined',
            'data': event['data']
        }))

    def user_left(self, event):
        """Send user left notification"""
        self.send(text_data=json.dumps({
            'type': 'user_left',
            'data': event['data']
        }))

    def webrtc_offer(self, event):
        """Send WebRTC offer"""
        # Only send to target user or broadcast if no target
        data = event['data']
        if not data.get('target') or data.get('target') == self.user_id:
            self.send(text_data=json.dumps({
                'type': 'offer',
                'data': data
            }))

    def webrtc_answer(self, event):
        """Send WebRTC answer"""
        data = event['data']
        if not data.get('target') or data.get('target') == self.user_id:
            self.send(text_data=json.dumps({
                'type': 'answer',
                'data': data
            }))

    def ice_candidate(self, event):
        """Send ICE candidate"""
        data = event['data']
        if not data.get('target') or data.get('target') == self.user_id:
            self.send(text_data=json.dumps({
                'type': 'ice-candidate',
                'data': data
            }))

    def chat_message_received(self, event):
        """Handle chat messages"""
        self.send(text_data=json.dumps({
            'type': 'chat_message_received',
            'data': event['data']
        }))

    def reaction_received(self, event):
        """Handle reactions"""
        self.send(text_data=json.dumps({
            'type': 'reaction',
            'data': event['data']
        }))

