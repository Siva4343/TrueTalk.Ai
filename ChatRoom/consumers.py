import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Message


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Join a general chat room (or user-specific room)
        self.room_group_name = "chat_room"
        
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

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get("type", "chat_message")
        
        if message_type == "chat_message":
            sender_username = text_data_json.get("sender_username")
            receiver_username = text_data_json.get("receiver_username")
            message_text = text_data_json.get("message")
            
            # Save message to database
            message = await self.save_message(
                sender_username, receiver_username, message_text
            )
            
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": {
                        "id": message["id"],
                        "sender_username": message["sender_username"],
                        "receiver_username": message["receiver_username"],
                        "text": message["text"],
                        "created_at": message["created_at"],
                    }
                }
            )

    # Receive message from room group
    async def chat_message(self, event):
        message = event["message"]
        
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            "type": "chat_message",
            "message": message
        }))

    @database_sync_to_async
    def save_message(self, sender_username, receiver_username, text):
        sender, _ = User.objects.get_or_create(
            username=sender_username,
            defaults={"email": f"{sender_username}@example.com"}
        )
        
        receiver = None
        if receiver_username:
            receiver, _ = User.objects.get_or_create(
                username=receiver_username,
                defaults={"email": f"{receiver_username}@example.com"}
            )
        
        message = Message.objects.create(
            sender=sender,
            receiver=receiver,
            text=text
        )
        
        return {
            "id": message.id,
            "sender_username": message.sender.username,
            "receiver_username": message.receiver.username if message.receiver else None,
            "text": message.text,
            "created_at": message.created_at.isoformat(),
        }

