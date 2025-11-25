import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import SharedContact


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        # Accept WebSocket connection
        await self.accept()

    async def receive(self, text_data):
        data = json.loads(text_data)

        msg_type = data.get("type")

        # ---- TEXT MESSAGE (optional if needed) ----
        if msg_type == "text":
            await self.send(text_data=json.dumps({
                "type": "text",
                "sender": data["sender"],
                "text": data["text"]
            }))

        # ---- CONTACT MESSAGE ----
        if msg_type == "contact":
            name = data["contact_name"]
            phone = data["contact_phone"]
            sender = data["sender"]

            # Save into database SAFELY (sync → async wrapper)
            await self.save_contact(sender, name, phone)

            # Send message back to React
            await self.send(text_data=json.dumps({
                "type": "contact",
                "sender": sender,
                "contact_name": name,
                "contact_phone": phone,
            }))

    # ---- DB Function wrapped for async ----
    @database_sync_to_async
    def save_contact(self, sender, name, phone):
        return SharedContact.objects.create(
            sender=sender,
            name=name,
            phone=phone
        )
