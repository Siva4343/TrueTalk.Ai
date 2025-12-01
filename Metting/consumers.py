# meet/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

# Development in-memory mapping: room_id -> { socket_id: { "name":..., "channel_name":... } }
ROOMS = {}

def make_participants_list(room_id):
    lst = []
    for sid, info in ROOMS.get(room_id, {}).items():
        # include socket id and name; clients expect "socketId" key
        lst.append({"socketId": sid, "name": info.get("name")})
    return lst

class MeetConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs'].get('room_id')
        await self.accept()

        # generate short id based on channel_name tail (unique per process)
        self.socket_id = self.channel_name[-8:]

        if not self.room_id:
            # reject if no room_id (shouldn't happen if URL route correct)
            await self.close()
            return

        if self.room_id not in ROOMS:
            ROOMS[self.room_id] = {}

        ROOMS[self.room_id][self.socket_id] = {
            "channel_name": self.channel_name,
            "name": "Someone"
        }

        print(f"[WS CONNECT] socket={self.socket_id} room={self.room_id} channel={self.channel_name}")

        # broadcast participants list to everyone in the room
        participants = make_participants_list(self.room_id)
        for sid, info in list(ROOMS[self.room_id].items()):
            try:
                await self.channel_layer.send(info["channel_name"], {
                    "type": "ws.send_json",
                    "message": {"type": "participants", "participants": participants}
                })
            except Exception as e:
                print(f"[WS CONNECT] failed to notify {sid}: {e}")

    async def disconnect(self, close_code):
        print(f"[WS DISCONNECT] socket={getattr(self,'socket_id',None)} room={getattr(self,'room_id',None)} code={close_code}")
        if getattr(self, "room_id", None) and getattr(self, "socket_id", None):
            room = ROOMS.get(self.room_id, {})
            if self.socket_id in room:
                del room[self.socket_id]

            # broadcast update
            participants = make_participants_list(self.room_id)
            for sid, info in list(room.items()):
                try:
                    await self.channel_layer.send(info["channel_name"], {
                        "type": "ws.send_json",
                        "message": {"type": "participants", "participants": participants}
                    })
                except Exception as e:
                    print(f"[WS DISCONNECT] failed to notify {sid}: {e}")

            # cleanup empty room
            if not room:
                ROOMS.pop(self.room_id, None)

    async def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data or "{}")
        except Exception:
            data = {}
        t = data.get("type")
        payload = data.get("payload")
        to = data.get("to")

        print(f"[WS RECV] socket={self.socket_id} room={self.room_id} type={t} to={to} payloadKeys={list(payload.keys()) if isinstance(payload, dict) else None}")

        # introduce: set name for this socket, then send assign-id & participants
        if t == "introduce":
            name = (payload or {}).get("name", "Someone")
            if self.room_id in ROOMS and self.socket_id in ROOMS[self.room_id]:
                ROOMS[self.room_id][self.socket_id]["name"] = name

            # send assign-id back to the introducer
            await self.send_json({"type": "assign-id", "payload": {"id": self.socket_id}})

            # broadcast participants list
            participants = make_participants_list(self.room_id)
            for sid, info in list(ROOMS[self.room_id].items()):
                try:
                    await self.channel_layer.send(info["channel_name"], {
                        "type": "ws.send_json",
                        "message": {"type": "participants", "participants": participants}
                    })
                except Exception as e:
                    print(f"[WS INTRO] failed to notify {sid}: {e}")
            return

        # forward offers/answers/ice-candidates to single target
        if t in ("offer", "answer", "ice-candidate"):
            if not to:
                print(f"[WS WARN] missing 'to' for type {t}")
                return
            target = ROOMS.get(self.room_id, {}).get(to)
            if not target:
                print(f"[WS WARN] target {to} not found in room {self.room_id}")
                return
            try:
                await self.channel_layer.send(target["channel_name"], {
                    "type": "ws.send_json",
                    "message": {"type": t, "from": self.socket_id, "payload": payload}
                })
                print(f"[WS FORWARD] {t} from {self.socket_id} -> {to}")
            except Exception as e:
                print(f"[WS FORWARD] failed to forward {t} to {to}: {e}")
            return

        # broadcast chat / host-command / reaction messages to room
        if t in ("chat-message", "host-command", "reaction"):
            for sid, info in list(ROOMS.get(self.room_id, {}).items()):
                try:
                    await self.channel_layer.send(info["channel_name"], {
                        "type": "ws.send_json",
                        "message": {"type": t, "from": self.socket_id, "payload": payload}
                    })
                except Exception as e:
                    print(f"[WS BROADCAST] failed to send {t} to {sid}: {e}")
            return

        # unknown types are ignored for now
        print(f"[WS INFO] unhandled message type: {t}")

    # helper to send via channel layer (calls this when we want to push to a channel)
    async def ws_send_json(self, event):
        message = event.get("message")
        await self.send(text_data=json.dumps(message))
