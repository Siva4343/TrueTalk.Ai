# Real-Time Chat Setup Guide

## Overview
This project now supports **real-time user-to-user messaging** using Django Channels (WebSockets). Users can send and receive messages instantly without page refresh.

## Features Added
- ✅ User model integration (Django User)
- ✅ Sender/Receiver message relationships
- ✅ Real-time WebSocket communication
- ✅ Automatic reconnection on disconnect
- ✅ REST API fallback if WebSocket fails
- ✅ Group chat (no receiver) or direct messaging (with receiver)

---

## Installation Steps

### Step 1: Install Required Packages

Open terminal in project root and run:

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install Django Channels and dependencies
pip install channels channels-redis

# Or install from requirements.txt
pip install -r requirements.txt
```

### Step 2: Run Database Migrations

Since we updated the Message model, you need to create and apply migrations:

```powershell
# Make sure you're in project root (C:\Users\lenovo\Documents\GitHub\TrueTalk.Ai)
python manage.py makemigrations ChatRoom
python manage.py migrate
```

### Step 3: Start the Backend Server

```powershell
# In project root
python manage.py runserver
```

The server will run on `http://127.0.0.1:8000` and handle both:
- REST API: `http://127.0.0.1:8000/api/chat/messages/`
- WebSocket: `ws://127.0.0.1:8000/ws/chat/`

### Step 4: Start the Frontend

Open a **new terminal** and run:

```powershell
cd ChatRoom/my-app
npm run dev
```

The frontend will run on `http://localhost:5173`

---

## How It Works

### Backend Architecture

1. **Models** (`ChatRoom/models.py`):
   - `Message` model with `sender` and `receiver` (ForeignKey to User)
   - Supports both group chat (receiver=None) and direct messages

2. **WebSocket Consumer** (`ChatRoom/consumers.py`):
   - Handles WebSocket connections
   - Broadcasts messages to all connected clients in real-time
   - Saves messages to database automatically

3. **REST API** (`ChatRoom/views.py`):
   - Still available as fallback
   - Endpoint: `POST /api/chat/messages/`
   - Accepts: `sender_username`, `receiver_username` (optional), `text`

### Frontend Architecture

1. **WebSocket Connection**:
   - Automatically connects on page load
   - Reconnects if connection drops
   - Shows connection status indicator

2. **Message Sending**:
   - Primary: Sends via WebSocket for instant delivery
   - Fallback: Uses REST API if WebSocket unavailable

3. **Message Receiving**:
   - Listens for WebSocket messages
   - Updates UI in real-time without refresh
   - Shows sender → receiver relationship

---

## Usage

### Group Chat (Everyone sees messages)
1. Enter your name in "Your Name" field
2. Leave "Send To" field **empty**
3. Type your message and send
4. All users will see the message instantly

### Direct Message (User-to-User)
1. Enter your name in "Your Name" field
2. Enter receiver's username in "Send To" field
3. Type your message and send
4. Only you and the receiver will see the message (in current implementation, all users see it, but it's marked with → receiver)

---

## Testing Real-Time Messaging

1. **Open two browser windows/tabs**:
   - Window 1: `http://localhost:5173`
   - Window 2: `http://localhost:5173`

2. **In Window 1**:
   - Name: "Alice"
   - Send To: (leave empty for group chat)
   - Message: "Hello everyone!"

3. **In Window 2**:
   - You should see Alice's message appear **instantly** without refreshing

4. **For Direct Message**:
   - Window 1: Name "Alice", Send To "Bob", Message "Hi Bob!"
   - Window 2: Name "Bob"
   - Both will see: "Alice → Bob: Hi Bob!"

---

## File Structure

```
ChatRoom/
├── models.py          # Updated Message model with sender/receiver
├── serializers.py     # Updated to handle User relationships
├── views.py           # REST API endpoint (fallback)
├── consumers.py       # WebSocket consumer (NEW)
├── routing.py         # WebSocket URL routing (NEW)
└── my-app/
    └── src/
        └── App.jsx    # Updated frontend with WebSocket support

Project/
├── settings.py        # Added Channels configuration
└── asgi.py            # Updated for WebSocket support
```

---

## Troubleshooting

### WebSocket Not Connecting
- Check that Django server is running
- Check browser console for errors
- Verify `CHANNEL_LAYERS` in `settings.py` is configured
- Frontend will automatically fallback to REST API

### Messages Not Appearing
- Check browser console for errors
- Verify database migrations ran successfully
- Check Django server logs for errors

### "ModuleNotFoundError: No module named 'channels'"
- Run: `pip install channels channels-redis`

---

## Production Notes

For production, replace the in-memory channel layer with Redis:

```python
# In settings.py
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}
```

Then install and run Redis server.

---

## API Endpoints

### REST API (Fallback)
- **GET** `/api/chat/messages/` - Get all messages
- **POST** `/api/chat/messages/` - Create message
  ```json
  {
    "sender_username": "alice",
    "receiver_username": "bob",  // optional
    "text": "Hello!"
  }
  ```

### WebSocket
- **Connect**: `ws://127.0.0.1:8000/ws/chat/`
- **Send Message**:
  ```json
  {
    "type": "chat_message",
    "sender_username": "alice",
    "receiver_username": "bob",
    "message": "Hello!"
  }
  ```

---

## Summary

✅ Real-time messaging is now fully functional
✅ Users can send messages to specific users or group chat
✅ Messages are saved to database
✅ Automatic reconnection on disconnect
✅ REST API fallback for reliability

Enjoy your real-time chat platform! 🚀

