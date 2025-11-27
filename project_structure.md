# TrueTalk.Ai Exact File Locations

This document lists the **exact folder path** for every important file in your project.

## 🖥️ BACKEND (Django)
**Root Folder:** `TrueTalk.Ai/`

| File Name | Exact Path | Purpose |
| :--- | :--- | :--- |
| `manage.py` | `TrueTalk.Ai/manage.py` | Server command tool. |
| `db.sqlite3` | `TrueTalk.Ai/db.sqlite3` | Database file. |
| `settings.py` | `TrueTalk.Ai/Project/settings.py` | Global settings (DB, Apps). |
| `asgi.py` | `TrueTalk.Ai/Project/asgi.py` | WebSocket entry point. |
| `urls.py` | `TrueTalk.Ai/Project/urls.py` | Main URL router. |

### 📂 App Folder: `TrueTalk.Ai/ChatRoom/`
| File Name | Exact Path | Purpose |
| :--- | :--- | :--- |
| `models.py` | `TrueTalk.Ai/ChatRoom/models.py` | Database Tables (User, Message). |
| `views.py` | `TrueTalk.Ai/ChatRoom/views.py` | API Logic (Login, Lists). |
| `consumers.py` | `TrueTalk.Ai/ChatRoom/consumers.py` | WebSocket Logic (Real-time). |
| `routing.py` | `TrueTalk.Ai/ChatRoom/routing.py` | WebSocket URL routing. |
| `serializers.py` | `TrueTalk.Ai/ChatRoom/serializers.py` | JSON Converters. |
| `urls.py` | `TrueTalk.Ai/ChatRoom/urls.py` | API URL routing. |

### 📂 App Folder: `TrueTalk.Ai/ChatLogic/`
| File Name | Exact Path | Purpose |
| :--- | :--- | :--- |
| `views.py` | `TrueTalk.Ai/ChatLogic/views.py` | File Upload Logic. |
| `urls.py` | `TrueTalk.Ai/ChatLogic/urls.py` | Upload URL routing. |

---

## 🎨 FRONTEND (React)
**Root Folder:** `TrueTalk.Ai/ChatRoom/my-app/`

| File Name | Exact Path | Purpose |
| :--- | :--- | :--- |
| `package.json` | `TrueTalk.Ai/ChatRoom/my-app/package.json` | Dependencies list. |
| `vite.config.js` | `TrueTalk.Ai/ChatRoom/my-app/vite.config.js` | Build configuration. |

### 📂 Source Folder: `TrueTalk.Ai/ChatRoom/my-app/src/`
| File Name | Exact Path | Purpose |
| :--- | :--- | :--- |
| `main.jsx` | `TrueTalk.Ai/ChatRoom/my-app/src/main.jsx` | App Entry Point. |
| `App.jsx` | `TrueTalk.Ai/ChatRoom/my-app/src/App.jsx` | Main Router (Login vs Chat). |
| `index.css` | `TrueTalk.Ai/ChatRoom/my-app/src/index.css` | Global Styles (Tailwind). |

### 📂 Components: `TrueTalk.Ai/ChatRoom/my-app/src/components/`
| File Name | Exact Path | Purpose |
| :--- | :--- | :--- |
| `Sidebar.jsx` | `TrueTalk.Ai/ChatRoom/my-app/src/components/Sidebar.jsx` | Left sidebar (Users/Groups). |
| `ChatWindow.jsx` | `TrueTalk.Ai/ChatRoom/my-app/src/components/ChatWindow.jsx` | Right chat area. |

### 📂 Pages: `TrueTalk.Ai/ChatRoom/my-app/src/pages/`
| File Name | Exact Path | Purpose |
| :--- | :--- | :--- |
| `LoginPage.jsx` | `TrueTalk.Ai/ChatRoom/my-app/src/pages/LoginPage.jsx` | Login Screen. |
| `ChatPage.jsx` | `TrueTalk.Ai/ChatRoom/my-app/src/pages/ChatPage.jsx` | Chat Screen Container. |

---

## 🔗 Connection Summary
-   **Frontend** (`src/pages/LoginPage.jsx`) talks to **Backend** (`ChatRoom/views.py`) via **HTTP**.
-   **Frontend** (`src/components/ChatWindow.jsx`) talks to **Backend** (`ChatRoom/consumers.py`) via **WebSockets**.
