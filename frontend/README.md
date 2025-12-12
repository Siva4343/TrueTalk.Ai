# TrueTalk Meeting Frontend

A Microsoft Teams-like video meeting interface built with React and Socket.IO.

## Features

- 🎥 Video conferencing with camera/microphone controls
- 💬 Real-time chat
- 👥 Participant management
- 🎨 Teams-like dark theme UI
- 📱 Responsive design

## Setup

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

## Usage

1. Enter your name
2. Enter a meeting code (create one from the backend API)
3. Click "Join Meeting"
4. Grant camera and microphone permissions
5. Start collaborating!

## Controls

- 🎤 **Mute/Unmute** - Toggle your microphone
- 📷 **Video On/Off** - Toggle your camera
- 📞 **Leave** - Exit the meeting

## Backend Integration

This frontend connects to the Django backend at `http://localhost:8000`

Make sure the backend server is running before starting the frontend.

## Technologies

- React 18
- Socket.IO Client
- WebRTC (getUserMedia API)
- Vite

## Development

The app runs on `http://localhost:5173` by default.
