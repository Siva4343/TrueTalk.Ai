import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from googletrans import Translator
from .models import Caption


def translate_text(text):
    translator = Translator()
    return {
        "hi": translator.translate(text, src="en", dest="hi").text,
        "te": translator.translate(text, src="en", dest="te").text,
        "ta": translator.translate(text, src="en", dest="ta").text,
    }


class LiveCaptionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "captions_group"

        await self.channel_layer.group_add(
            self.group_name, self.channel_name
        )

        await self.accept()

        await self.send(text_data=json.dumps({
            "type": "connected",
            "message": "WebSocket connected successfully"
        }))

    async def disconnect(self, code):
        await self.channel_layer.group_discard(
            self.group_name, self.channel_name
        )

    async def receive(self, text_data=None):
        data = json.loads(text_data)
        english = data["text"]
        speaker = data.get("speaker", "User")

        loop = asyncio.get_event_loop()
        translations = await loop.run_in_executor(
            None, translate_text, english
        )

        Caption.objects.create(
            original_text=english,
            hindi=translations["hi"],
            telugu=translations["te"],
            tamil=translations["ta"],
            speaker=speaker,
        )

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "broadcast_message",
                "message": {
                    "type": "caption",
                    "original": english,
                    "speaker": speaker,
                    "translations": translations,
                },
            }
        )

    async def broadcast_message(self, event):
        await self.send(text_data=json.dumps(event["message"]))
