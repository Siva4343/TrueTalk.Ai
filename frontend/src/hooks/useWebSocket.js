import { useEffect, useRef, useState } from 'react';

export const useWebSocket = (meetingId, userId, userName) => {
    const [isConnected, setIsConnected] = useState(false);
    const [messages, setMessages] = useState([]);
    const wsRef = useRef(null);
    const handlersRef = useRef({});

    useEffect(() => {
        if (!meetingId) return;

        const wsUrl = `ws://localhost:8000/ws/meeting/${meetingId}/`;
        console.log('Connecting to WebSocket:', wsUrl);

        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            console.log('✅ WebSocket connected!');
            setIsConnected(true);

            ws.send(JSON.stringify({
                type: 'login',
                data: {
                    name: userName,
                    userId: userId,
                }
            }));
        };

        ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            console.log('📨 Received:', message.type);

            if (handlersRef.current[message.type]) {
                handlersRef.current[message.type](message.data);
            }

            setMessages(prev => [...prev, message]);
        };

        ws.onerror = (error) => {
            console.error('❌ WebSocket error:', error);
        };

        ws.onclose = () => {
            console.log('🔌 WebSocket disconnected');
            setIsConnected(false);
        };

        wsRef.current = ws;

        return () => {
            if (ws.readyState === WebSocket.OPEN) {
                ws.close();
            }
        };
    }, [meetingId, userId, userName]);

    const sendMessage = (type, data) => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type, data }));
            console.log('📤 Sent:', type);
        }
    };

    const on = (eventType, handler) => {
        handlersRef.current[eventType] = handler;
    };

    return { isConnected, sendMessage, on, messages };
};
