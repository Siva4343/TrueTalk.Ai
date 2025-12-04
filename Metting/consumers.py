# Meeting/consumers.py
# (This is the same file as before but with small updates to respect payload.targetLang)
import json
import asyncio
import os
import time
import traceback
from collections import OrderedDict
from channels.generic.websocket import AsyncWebsocketConsumer

# Try to import google-cloud-translate v3 client (recommended)
GCP_AVAILABLE = False
try:
    from google.cloud import translate as gcloud_translate_v3
    GCP_AVAILABLE = True
except Exception:
    GCP_AVAILABLE = False

# Fallbacks...
FALLBACK_GOOGLETRANS = False
try:
    from googletrans import Translator as GoogleTransTranslator
    FALLBACK_GOOGLETRANS = True
except Exception:
    FALLBACK_GOOGLETRANS = False

DEEP_TRANSLATOR_AVAILABLE = False
try:
    from deep_translator import GoogleTranslator as DeepGoogleTranslator
    DEEP_TRANSLATOR_AVAILABLE = True
except Exception:
    DEEP_TRANSLATOR_AVAILABLE = False

googletrans_translator = None

gcp_client = None
if GCP_AVAILABLE:
    try:
        GCP_PROJECT = os.environ.get("GCP_PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT")
        if GCP_PROJECT:
            gcp_client = gcloud_translate_v3.TranslationServiceClient()
        else:
            gcp_client = None
    except Exception:
        gcp_client = None

ROOMS = {}
ROOM_CAPTIONS = {}
ROOM_CAPTIONS_MAX = 200

TRANSLATION_CACHE = OrderedDict()
TRANSLATION_CACHE_MAX = int(os.environ.get("TRANSLATION_CACHE_MAX", "1000"))

DEFAULT_TRANSLATE_LANGS = os.environ.get("TRANSLATE_LANGS", "te,hi,ta,en").split(",")

DEBUG_WS = os.environ.get("DEBUG_WS", "") not in ("", "0", "false", "False")

def cache_get(key):
    try:
        val = TRANSLATION_CACHE.get(key)
        if val is not None:
            TRANSLATION_CACHE.move_to_end(key)
        return val
    except Exception:
        return None

def cache_set(key, value):
    try:
        TRANSLATION_CACHE[key] = value
        TRANSLATION_CACHE.move_to_end(key)
        while len(TRANSLATION_CACHE) > TRANSLATION_CACHE_MAX:
            TRANSLATION_CACHE.popitem(last=False)
    except Exception:
        pass

def make_participants_list(room_id):
    lst = []
    for sid, info in ROOMS.get(room_id, {}).items():
        lst.append({"socketId": sid, "name": info.get("name")})
    return lst

class MeetConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope["url_route"]["kwargs"].get("room_id")
        await self.accept()
        self.socket_id = self.channel_name[-8:]
        if not self.room_id:
            await self.close()
            return
        if self.room_id not in ROOMS:
            ROOMS[self.room_id] = {}
        ROOMS[self.room_id][self.socket_id] = {
            "channel_name": self.channel_name,
            "name": "Someone",
            "last_caption": "",
        }
        if self.room_id not in ROOM_CAPTIONS:
            ROOM_CAPTIONS[self.room_id] = []
        print(f"[WS CONNECT] socket={self.socket_id} room={self.room_id} channel={self.channel_name}")
        participants = make_participants_list(self.room_id)
        for sid, info in list(ROOMS[self.room_id].items()):
            try:
                await self.channel_layer.send(
                    info["channel_name"],
                    {
                        "type": "ws.send_json",
                        "message": {"type": "participants", "participants": participants},
                    },
                )
            except Exception as e:
                print(f"[WS CONNECT] failed to notify {sid}: {e}")

    async def disconnect(self, close_code):
        print(f"[WS DISCONNECT] socket={getattr(self,'socket_id',None)} room={getattr(self,'room_id',None)} code={close_code}")
        if getattr(self, "room_id", None) and getattr(self, "socket_id", None):
            room = ROOMS.get(self.room_id, {})
            if self.socket_id in room:
                del room[self.socket_id]
            participants = make_participants_list(self.room_id)
            for sid, info in list(room.items()):
                try:
                    await self.channel_layer.send(
                        info["channel_name"],
                        {
                            "type": "ws.send_json",
                            "message": {"type": "participants", "participants": participants},
                        },
                    )
                except Exception as e:
                    print(f"[WS DISCONNECT] failed to notify {sid}: {e}")
            if not room:
                ROOMS.pop(self.room_id, None)
                ROOM_CAPTIONS.pop(self.room_id, None)

    async def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data or "{}")
        except Exception:
            data = {}
        t = data.get("type")
        payload = data.get("payload")
        to = data.get("to")

        try:
            payload_keys = list(payload.keys()) if isinstance(payload, dict) else None
        except Exception:
            payload_keys = None

        print(f"[WS RECV] socket={self.socket_id} room={self.room_id} type={t} to={to} payloadKeys={payload_keys}")

        if t == "introduce":
            name = (payload or {}).get("name", "Someone")
            if self.room_id in ROOMS and self.socket_id in ROOMS[self.room_id]:
                ROOMS[self.room_id][self.socket_id]["name"] = name
            await self.send_json({"type": "assign-id", "payload": {"id": self.socket_id}})
            history = ROOM_CAPTIONS.get(self.room_id, [])
            try:
                await self.send_json({"type": "caption-history", "payload": history})
            except Exception as e:
                print(f"[HISTORY SEND ERROR] {e}")
            participants = make_participants_list(self.room_id)
            for sid, info in list(ROOMS[self.room_id].items()):
                try:
                    await self.channel_layer.send(
                        info["channel_name"],
                        {
                            "type": "ws.send_json",
                            "message": {"type": "participants", "participants": participants},
                        },
                    )
                except Exception as e:
                    print(f"[WS INTRO] failed to notify {sid}: {e}")
            return

        if t in ("offer", "answer", "ice-candidate"):
            if not to:
                print(f"[WS WARN] missing 'to' for type {t}")
                return
            target = ROOMS.get(self.room_id, {}).get(to)
            if not target:
                print(f"[WS WARN] target {to} not found in room {self.room_id}")
                return
            try:
                await self.channel_layer.send(
                    target["channel_name"],
                    {
                        "type": "ws.send_json",
                        "message": {"type": t, "from": self.socket_id, "payload": payload},
                    },
                )
                print(f"[WS FORWARD] {t} from {self.socket_id} -> {to}")
            except Exception as e:
                print(f"[WS FORWARD] failed to forward {t} to {to}: {e}")
            return

        if t in ("chat-message", "host-command", "reaction"):
            if t == "chat-message" and isinstance(payload, dict) and payload.get("type") == "caption":
                text = (payload.get("text") or "")[:4000]
                speaker = payload.get("from") or self.socket_id
                ts = payload.get("time") or None
                is_final = bool(payload.get("isFinal", True))
                if self.room_id in ROOMS and speaker in ROOMS[self.room_id]:
                    speaker_info = ROOMS[self.room_id][speaker]
                else:
                    speaker_info = None
                last_text = ""
                if speaker_info:
                    last_text = speaker_info.get("last_caption", "")
                if not is_final and text == last_text:
                    print(f"[CAPTION SKIP] duplicate interim from={speaker} text_preview={text[:80]}")
                    return
                if speaker_info:
                    if not is_final:
                        ROOMS[self.room_id][speaker]["last_caption"] = text
                    else:
                        ROOMS[self.room_id][speaker]["last_caption"] = ""

                # Check for requested language in payload (short code expected e.g. "te" or "hi")
                requested_lang = None
                if isinstance(payload, dict):
                    requested_lang = payload.get("targetLang") or payload.get("target_lang") or None
                    if isinstance(requested_lang, str) and requested_lang:
                        requested_lang = requested_lang.split("-")[0].lower()

                # Determine language targets
                if requested_lang:
                    lang_codes = [requested_lang]
                    # keep english as fallback
                    if "en" not in lang_codes:
                        lang_codes.append("en")
                else:
                    lang_codes = [c.strip() for c in DEFAULT_TRANSLATE_LANGS if c.strip()]
                    if "en" not in lang_codes:
                        lang_codes.append("en")

                translations = {}

                if text and is_final:
                    # Cache key should include requested_lang to differentiate translations
                    cache_key = f"{self.room_id}::tlang={','.join(lang_codes)}::" + text.strip().lower()
                    cached = cache_get(cache_key)
                    if cached:
                        translations = cached.copy()
                        debug_info = {"cache_hit": True, "cache_key": cache_key, "cached_targets": list(translations.keys())}
                        if DEBUG_WS:
                            await self._send_debug_to_source(debug_info)
                    else:
                        start_all = time.perf_counter()
                        try:
                            if gcp_client and (os.environ.get("GCP_PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT")):
                                print("[TRANSLATE] Using GCP Translate v3")
                                project = os.environ.get("GCP_PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT")
                                parent = f"projects/{project}/locations/global"
                                loop = asyncio.get_running_loop()

                                async def translate_gcp_async(src_text, target_lang):
                                    def blocking():
                                        try:
                                            response = gcp_client.translate_text(
                                                request={
                                                    "parent": parent,
                                                    "contents": [src_text],
                                                    "mime_type": "text/plain",
                                                    "target_language_code": target_lang,
                                                }
                                            )
                                            if response and response.translations and len(response.translations) > 0:
                                                return response.translations[0].translated_text
                                            return ""
                                        except Exception as e:
                                            print(f"[GCP TRANSLATE ERROR] target={target_lang} err={e}")
                                            return ""
                                    return await loop.run_in_executor(None, blocking)

                                tasks = [translate_gcp_async(text, code) for code in lang_codes]
                                results = await asyncio.gather(*tasks, return_exceptions=True)
                                for code, result in zip(lang_codes, results):
                                    translations[code] = "" if isinstance(result, Exception) else (result or "")

                            elif DEEP_TRANSLATOR_AVAILABLE:
                                print("[TRANSLATE] Using deep_translator fallback")
                                loop = asyncio.get_running_loop()

                                def deep_translate_sync(text_inner, target):
                                    try:
                                        return DeepGoogleTranslator(source="auto", target=target).translate(text_inner) or ""
                                    except Exception as e:
                                        print(f"[deep_translator error] target={target} err={e}")
                                        return ""

                                tasks = [loop.run_in_executor(None, deep_translate_sync, text, code) for code in lang_codes]
                                completed = await asyncio.gather(*tasks, return_exceptions=True)
                                for code, result in zip(lang_codes, completed):
                                    translations[code] = "" if isinstance(result, Exception) else (result or "")

                            elif FALLBACK_GOOGLETRANS:
                                global googletrans_translator
                                if googletrans_translator is None:
                                    try:
                                        googletrans_translator = GoogleTransTranslator()
                                    except Exception as e:
                                        print(f"[googletrans init error] {e}")
                                        googletrans_translator = None

                                if googletrans_translator:
                                    print("[TRANSLATE] Using googletrans fallback")
                                    loop = asyncio.get_running_loop()

                                    def translate_sync(text_inner, dest):
                                        try:
                                            res = googletrans_translator.translate(text_inner, dest=dest)
                                            if hasattr(res, "text"):
                                                return getattr(res, "text", "")
                                            if isinstance(res, dict) and res.get("text"):
                                                return res.get("text")
                                            return str(res) or ""
                                        except Exception as e:
                                            print(f"[googletrans error] dest={dest} err={e}")
                                            return ""

                                    tasks = [loop.run_in_executor(None, translate_sync, text, code) for code in lang_codes]
                                    completed = await asyncio.gather(*tasks, return_exceptions=True)
                                    for code, result in zip(lang_codes, completed):
                                        translations[code] = "" if isinstance(result, Exception) else (result or "")
                                else:
                                    print("[TRANSLATE SKIPPED] googletrans failed to initialize")
                                    translations = {c: "" for c in lang_codes}
                            else:
                                translations = {c: "" for c in lang_codes}
                                print("[TRANSLATE SKIPPED] No translation client configured (set GCP_PROJECT_ID+credentials or install deep-translator)")
                        except Exception as e:
                            print(f"[TRANSLATE FAIL] {e}")
                            traceback.print_exc()
                            translations = {c: "" for c in lang_codes}
                        duration_all = int((time.perf_counter() - start_all) * 1000)
                        cache_set(cache_key, translations.copy())
                        if DEBUG_WS:
                            await self._send_debug_to_source({"cache_hit": False, "key": cache_key, "duration_ms": duration_all, "targets": lang_codes})
                else:
                    translations = {c: "" for c in lang_codes}

                non_empty = {k: v for k, v in translations.items() if v}
                if not non_empty and is_final:
                    for c in lang_codes:
                        translations[c] = text
                    translations.setdefault("en", text)

                LANG_DISPLAY = {
                    "hi": "Hindi (हिन्दी)",
                    "te": "Telugu (తెలుగు)",
                    "ta": "Tamil (தமிழ்)",
                    "kn": "Kannada (ಕನ್ನಡ)",
                    "ml": "Malayalam (മലയാളം)",
                    "mr": "Marathi (मराठी)",
                    "gu": "Gujarati (ગુજરાતી)",
                    "bn": "Bengali (বাংলা)",
                    "pa": "Punjabi (ਪੰਜਾਬੀ)",
                    "or": "Odia (ଓଡ଼ିଆ)",
                    "en": "English"
                }

                def _safe_set_translation(key, val):
                    try:
                        if key and val is not None:
                            existing = translations.get(key)
                            if not existing:
                                translations[key] = val
                            else:
                                if existing == "" and val:
                                    translations[key] = val
                    except Exception:
                        pass

                for code in list(translations.keys()):
                    val = translations.get(code, "") or ""
                    if val:
                        _safe_set_translation(code, val)
                        _safe_set_translation(code.upper(), val)
                        _safe_set_translation(f"{code}-IN", val)
                        _safe_set_translation(f"{code}_IN", val)
                        disp = LANG_DISPLAY.get(code)
                        if disp:
                            _safe_set_translation(disp, val)
                            short_disp = disp.split("(", 1)[0].strip()
                            _safe_set_translation(short_disp, val)
                            _safe_set_translation(short_disp.lower(), val)

                if translations.get("en"):
                    _safe_set_translation("en-US", translations["en"])
                    _safe_set_translation("EN", translations["en"])
                    _safe_set_translation("english", translations["en"])

                if is_final:
                    entry = {"from": speaker, "text": text, "time": ts}
                    hist = ROOM_CAPTIONS.setdefault(self.room_id, [])
                    hist.append(entry)
                    if len(hist) > ROOM_CAPTIONS_MAX:
                        ROOM_CAPTIONS[self.room_id] = hist[-ROOM_CAPTIONS_MAX :]

                print(f"[BROADCAST CAPTION] room={self.room_id} from={speaker} preview={(text[:120]+'...') if len(text)>120 else text} translations_found={len([k for k,v in translations.items() if v])} isFinal={is_final}")

                caption_payload = {
                    "type": "caption",
                    "from": speaker,
                    "text": text,
                    "translations": translations,
                    "time": ts,
                    "isFinal": is_final,
                    "sourceSocket": self.socket_id,
                }

                for sid, info in list(ROOMS.get(self.room_id, {}).items()):
                    try:
                        await self.channel_layer.send(
                            info["channel_name"],
                            {"type": "ws.send_json", "message": {"type": "chat-message", "payload": caption_payload}},
                        )
                    except Exception as e:
                        print(f"[WS BROADCAST] failed to send caption to {sid}: {e}")
                return

            for sid, info in list(ROOMS.get(self.room_id, {}).items()):
                try:
                    await self.channel_layer.send(
                        info["channel_name"],
                        {"type": "ws.send_json", "message": {"type": t, "from": self.socket_id, "payload": payload}},
                    )
                except Exception as e:
                    print(f"[WS BROADCAST] failed to send {t} to {sid}: {e}")
            return

        print(f"[WS INFO] unhandled message type: {t}")

    async def ws_send_json(self, event):
        message = event.get("message")
        await self.send(text_data=json.dumps(message))

    async def _send_debug_to_source(self, info: dict):
        try:
            if not DEBUG_WS:
                return
            payload = {"type": "caption-debug", "payload": {"info": info, "ts": int(time.time() * 1000)}}
            await self.send(text_data=json.dumps({"type": "chat-message", "payload": payload}))
        except Exception:
            pass
