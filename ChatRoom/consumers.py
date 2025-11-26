import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Message


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Get room name from URL route
        self.room_name = self.scope['url_route']['kwargs'].get('room_name', 'general')
        self.room_group_name = f"chat_{self.room_name}"
        
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
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get("type", "chat_message")
            
            if message_type == "read_receipt":
                message_id = text_data_json.get("message_id")
                reader_username = text_data_json.get("reader_username")
                
                if message_id and reader_username:
                    await self.mark_message_as_read(message_id)
                    
                    # Broadcast read receipt to room
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            "type": "read_receipt",
                            "message_id": message_id,
                            "reader_username": reader_username
                        }
                    )
            
            elif message_type == "chat_message":
                sender_username = text_data_json.get("sender_username")
                receiver_username = text_data_json.get("receiver_username")
                group_id = text_data_json.get("group_id")
                message_text = text_data_json.get("message")
                msg_type = text_data_json.get("msg_type", "text")
                attachment_url = text_data_json.get("attachment_url")
                
                if not sender_username:
                    await self.send(text_data=json.dumps({
                        "type": "error",
                        "message": "sender_username is required"
                    }))
                    return
                
                # Save message to database
                message = await self.save_message(
                    sender_username, receiver_username, group_id, message_text, msg_type, attachment_url
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
                            "group_id": message["group_id"],
                            "text": message["text"],
                            "msg_type": message["msg_type"],
                            "attachment_url": message["attachment_url"],
                            "created_at": message["created_at"],
                            "is_read": False
                        }
                    }
                )
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": "Invalid JSON format"
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": str(e)
            }))

    # Receive message from room group
    async def chat_message(self, event):
        message = event["message"]
        
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            "type": "chat_message",
            "message": message
        }))

    # Receive read receipt from room group
    async def read_receipt(self, event):
        await self.send(text_data=json.dumps({
            "type": "read_receipt",
            "message_id": event["message_id"],
            "reader_username": event["reader_username"]
        }))

    @database_sync_to_async
    def save_message(self, sender_username, receiver_username, group_id, text, msg_type, attachment_url):
        from .models import Group
        
        sender, _ = User.objects.get_or_create(
            username=sender_username.strip(),
            defaults={"email": f"{sender_username.strip()}@example.com"}
        )
        
        receiver = None
        if receiver_username and receiver_username.strip():
            receiver, _ = User.objects.get_or_create(
                username=receiver_username.strip(),
                defaults={"email": f"{receiver_username.strip()}@example.com"}
            )
            
        group = None
        if group_id:
            try:
                group = Group.objects.get(id=group_id)
            except Group.DoesNotExist:
                pass
        
        message = Message.objects.create(
            sender=sender,
            receiver=receiver,
            group=group,
            text=text,
            msg_type=msg_type,
            attachment_url=attachment_url
        )
        
        return {
            "id": message.id,
            "sender_username": message.sender.username,
            "receiver_username": message.receiver.username if message.receiver else None,
            "group_id": message.group.id if message.group else None,
            "text": message.text,
            "msg_type": message.msg_type,
            "attachment_url": message.attachment_url,
            "created_at": message.created_at.isoformat(),
            "is_read": message.is_read
        }

    @database_sync_to_async
    def mark_message_as_read(self, message_id):
        from .models import Message
        try:
            message = Message.objects.get(id=message_id)
            message.is_read = True
            message.save()
        except Message.DoesNotExist:
            pass

