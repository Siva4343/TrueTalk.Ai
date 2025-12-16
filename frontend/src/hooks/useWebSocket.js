import { useEffect, useRef, useState } from 'react';

export const useWebSocket = (meetingId, userId, userName) => {
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState([]);
  const wsRef = useRef(null);
  const handlersRef = useRef({});

  useEffect(() => {
    if (!meetingId) return;

    const ws = new WebSocket(
      `ws://localhost:8000/ws/meeting/${meetingId}/`
    );

    ws.onopen = () => {
      setIsConnected(true);
      ws.send(JSON.stringify({
        type: 'login',
        data: { userId, name: userName },
      }));
    };

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      handlersRef.current[msg.type]?.(msg.data);
      setMessages(prev => [...prev, msg]);
    };

    ws.onclose = () => setIsConnected(false);
    ws.onerror = console.error;

    wsRef.current = ws;

    return () => ws.close();
  }, [meetingId, userId, userName]);

  const sendMessage = (type, data) => {
    wsRef.current?.readyState === WebSocket.OPEN &&
      wsRef.current.send(JSON.stringify({ type, data }));
  };

  const on = (type, handler) => {
    handlersRef.current[type] = handler;
  };

  return { isConnected, sendMessage, on, messages };
};
