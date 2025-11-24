import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Message
from django.contrib.auth.models import User

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room = "contactroom"
        await self.channel_layer.group_add(self.room, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.room, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)

        if data.get("type") == "text":
            await self.handle_text_message(data)
        else:
            await self.handle_contact_message(data)

    async def handle_text_message(self, data):
        user = User.objects.get(username=data["sender"])
        msg = Message.objects.create(sender=user, text=data["text"])

        await self.channel_layer.group_send(
            self.room,
            {"type": "chat_message", "message": msg.to_json()}
        )

    async def handle_contact_message(self, data):
        user = User.objects.get(username=data["sender"])
        msg = Message.objects.create(
            sender=user,
            contact_name=data["contact_name"],
            contact_phone=data["contact_phone"],
        )

        await self.channel_layer.group_send(
            self.room,
            {"type": "chat_message", "message": msg.to_json()}
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event["message"]))
