# How to Start the Server

## Important: WebSocket Support

Django's default `runserver` command **does not properly support WebSocket connections**. You need to use `daphne` (ASGI server) for WebSocket support.

## Option 1: Using Daphne (Recommended - WebSocket Support)

1. **Install daphne** (if not already installed):
   ```powershell
   pip install daphne
   ```

2. **Start the server with daphne**:
   ```powershell
   daphne -b 127.0.0.1 -p 8000 Project.asgi:application
   ```

   Or use the helper script:
   ```powershell
   python run_server.py
   ```

## Option 2: Using runserver (WebSocket will NOT work, but REST API will)

If you just want to test the REST API (without WebSocket):
```powershell
python manage.py runserver 127.0.0.1:8000
```

**Note**: With `runserver`, you'll see 404 errors for `/ws/chat/` in the terminal, but the REST API fallback will still work for sending messages.

## Verify Server is Running

1. Open browser: `http://127.0.0.1:8000/api/chat/messages/`
   - Should return JSON (empty array `[]` if no messages)

2. Check WebSocket (only works with daphne):
   - Frontend will show "Connected" status if WebSocket works
   - If not, it will automatically use REST API fallback

## Troubleshooting

### "ModuleNotFoundError: No module named 'daphne'"
```powershell
pip install daphne
```

### WebSocket still not connecting
1. Make sure you're using `daphne`, not `runserver`
2. Check that `ASGI_APPLICATION = 'Project.asgi.application'` is in `settings.py`
3. Verify `ChatRoom/routing.py` has the WebSocket URL pattern

### Messages still not sending
1. Check browser console for errors
2. Check Django server logs
3. Verify the REST API endpoint works: `http://127.0.0.1:8000/api/chat/messages/`
4. Make sure CORS is enabled in `settings.py`


