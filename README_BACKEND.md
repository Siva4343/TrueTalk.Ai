# Backend Updates & Setup Guide

## 🚀 Updates Made
The backend has been fully updated to use **Django REST Framework (DRF)** and **Django Channels** for WebRTC signaling.

### Key Changes:
1. **Serializers (`video/serializers.py`)**:
   - Added `UserSerializer`, `CallSessionSerializer`, `CallLogSerializer`.
   - Added validation logic for initiating calls.

2. **Views (`video/views.py`)**:
   - Converted to `ModelViewSet` for standard REST operations.
   - Added custom actions: `initiate_call`, `accept_call`, `reject_call`, `end_call`.
   - Implemented `CallLogViewSet` for history.

3. **Permissions (`video/permissions.py`)**:
   - Added custom permissions: `IsCallParticipant`, `IsCallReceiver`, `CanEndCall`.

4. **URLs (`video/urls.py`)**:
   - Configured DRF Routers for automatic URL routing.

5. **WebSockets (`video/consumers.py`)**:
   - Enhanced `CallConsumer` to handle WebRTC signaling (offer, answer, ICE candidates).
   - Added database logging for call events.

6. **Settings (`Project/settings.py`)**:
   - Configured `REST_FRAMEWORK` settings.
   - Added `channels` and `corsheaders` configuration.

## 🛠️ How to Run

### 1. Install Dependencies
Make sure you have the required packages installed:
```bash
pip install djangorestframework django-cors-headers channels channels-redis daphne django-filter
```

### 2. Run Migrations
Apply the database changes:
```bash
python manage.py migrate
```

### 3. Start the Server
Start the Django development server:
```bash
python manage.py runserver
```
The API will be available at `http://127.0.0.1:8000/api/`.
The WebSocket endpoint will be at `ws://127.0.0.1:8000/ws/call/<room_name>/`.

## 🔗 API Endpoints

- **Initiate Call**: `POST /api/call-sessions/initiate_call/`
- **Accept Call**: `POST /api/call-sessions/{id}/accept_call/`
- **Reject Call**: `POST /api/call-sessions/{id}/reject_call/`
- **End Call**: `POST /api/call-sessions/{id}/end_call/`
- **Call History**: `GET /api/call-sessions/`
