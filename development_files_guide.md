# TrueTalk.Ai Development Files Guide

This document lists **only the files we modified or created** during this development session. It explains exactly where they are and what specific features they handle.

---

## 🖥️ BACKEND (Django)
**Base Folder:** `TrueTalk.Ai/ChatRoom/`

### 📂 `ChatRoom/` (The Core Logic)

| File | Exact Path | What We Did & Why |
| :--- | :--- | :--- |
| **`models.py`** | `ChatRoom/models.py` | **Database Schema**<br>- Added `Group` model for group chats.<br>- Updated `Message` model with `is_read` (for blue ticks), `msg_type` (text/image/video), and `attachment_url`. |
| **`consumers.py`** | `ChatRoom/consumers.py` | **Real-Time Logic (WebSockets)**<br>- Updated `ChatConsumer` to handle `read_receipt` events.<br>- Added logic to broadcast messages to specific Groups or Users.<br>- Handles saving messages to the DB automatically. |
| **`views.py`** | `ChatRoom/views.py` | **API Endpoints**<br>- Created `UserViewSet` to auto-create users on login.<br>- Created `GroupViewSet` to create and list groups.<br>- Created `MessageViewSet` to fetch chat history. |
| **`serializers.py`** | `ChatRoom/serializers.py` | **Data Formatting**<br>- Updated `MessageSerializer` to include the new fields (`is_read`, `attachment_url`).<br>- Created `GroupSerializer` to send group member data to the frontend. |
| **`urls.py`** | `ChatRoom/urls.py` | **API Routing**<br>- Registered the new routes: `/api/chat/users/`, `/api/chat/groups/`, etc. |

### 📂 `ChatLogic/` (Utility Features)

| File | Exact Path | What We Did & Why |
| :--- | :--- | :--- |
| **`views.py`** | `ChatLogic/views.py` | **File Uploads**<br>- Created `FileUploadView` to handle image/video/file uploads.<br>- Returns a URL that the frontend uses to send the file as a message. |
| **`urls.py`** | `ChatLogic/urls.py` | **Upload Routing**<br>- Maps `/api/logic/upload/` to the file upload view. |

---

## 🎨 FRONTEND (React)
**Base Folder:** `TrueTalk.Ai/ChatRoom/my-app/src/`

### 📂 `src/pages/` (Screens)

| File | Exact Path | What We Did & Why |
| :--- | :--- | :--- |
| **`LoginPage.jsx`** | `src/pages/LoginPage.jsx` | **Login Screen**<br>- Calls `POST /api/chat/users/` to create or fetch the user.<br>- Saves the username to `localStorage` so you stay logged in. |
| **`ChatPage.jsx`** | `src/pages/ChatPage.jsx` | **Main Container**<br>- Holds the state for `currentChat` (who you are talking to).<br>- Renders the `Sidebar` and `ChatWindow` side-by-side. |

### 📂 `src/components/` (Building Blocks)

| File | Exact Path | What We Did & Why |
| :--- | :--- | :--- |
| **`Sidebar.jsx`** | `src/components/Sidebar.jsx` | **Navigation Bar**<br>- Fetches User and Group lists from the API.<br>- **Polling**: Checks every 3s for the "Last Message" to show previews.<br>- **Group Modal**: Added a popup to create new groups.<br>- **Logout**: Added button to clear session. |
| **`ChatWindow.jsx`** | `src/components/ChatWindow.jsx` | **The Chat Interface**<br>- **WebSockets**: Connects to `ws://...` to send/receive messages.<br>- **Read Receipts**: Sends a signal when you open a chat (Blue Ticks).<br>- **File Sharing**: Handles Image/Video/File uploads via API.<br>- **Location**: Gets browser coordinates and sends them. |

### 📂 `src/` (Configuration)

| File | Exact Path | What We Did & Why |
| :--- | :--- | :--- |
| **`App.jsx`** | `src/App.jsx` | **Main Router**<br>- Added logic to check if a user is logged in.<br>- Redirects to `LoginPage` if not authenticated, otherwise shows `ChatPage`. |
