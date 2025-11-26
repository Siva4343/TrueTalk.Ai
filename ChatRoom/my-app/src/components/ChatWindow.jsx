import { useState, useEffect, useRef } from 'react';

export default function ChatWindow({ chat }) {
    const [messages, setMessages] = useState([]);
    const [newMessage, setNewMessage] = useState('');
    const [ws, setWs] = useState(null);
    const [uploading, setUploading] = useState(false);
    const messagesEndRef = useRef(null);
    const fileInputRef = useRef(null);
    const currentUsername = localStorage.getItem('username');

    useEffect(() => {
        if (!chat) return;

        // Determine room name
        const roomName = chat.type === 'group'
            ? `group_${chat.data.id}`
            : `user_${Math.min(currentUsername, chat.data.username)}_${Math.max(currentUsername, chat.data.username)}`;

        // Connect to WebSocket
        const websocket = new WebSocket(`ws://localhost:8000/ws/chat/${roomName}/`);

        websocket.onopen = () => {
            console.log('WebSocket connected');
        };

        websocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'chat_message') {
                setMessages(prev => [...prev, data.message]);
            }
        };

        websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        setWs(websocket);

        // Fetch message history
        fetchMessages();

        return () => {
            websocket.close();
        };
    }, [chat]);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const fetchMessages = async () => {
        try {
            const response = await fetch('http://localhost:8000/api/chat/messages/');
            const data = await response.json();

            // Filter messages for current chat
            const filtered = data.filter(msg => {
                if (chat.type === 'group') {
                    return msg.group?.id === chat.data.id;
                } else {
                    return (
                        (msg.sender_username === currentUsername && msg.receiver_username === chat.data.username) ||
                        (msg.sender_username === chat.data.username && msg.receiver_username === currentUsername)
                    );
                }
            });

            setMessages(filtered);
        } catch (error) {
            console.error('Error fetching messages:', error);
        }
    };

    const sendMessage = (e) => {
        e.preventDefault();
        if (!newMessage.trim() || !ws) return;

        const messageData = {
            type: 'chat_message',
            sender_username: currentUsername,
            message: newMessage,
            msg_type: 'text'
        };

        if (chat.type === 'group') {
            messageData.group_id = chat.data.id;
        } else {
            messageData.receiver_username = chat.data.username;
        }

        ws.send(JSON.stringify(messageData));
        setNewMessage('');
    };

    const handleFileUpload = async (e, type) => {
        const file = e.target.files[0];
        if (!file) return;

        setUploading(true);
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('http://localhost:8000/api/logic/upload/', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (response.ok && ws) {
                const messageData = {
                    type: 'chat_message',
                    sender_username: currentUsername,
                    message: file.name,
                    msg_type: type,
                    attachment_url: data.file_url
                };

                if (chat.type === 'group') {
                    messageData.group_id = chat.data.id;
                } else {
                    messageData.receiver_username = chat.data.username;
                }

                ws.send(JSON.stringify(messageData));
            }
        } catch (error) {
            console.error('Error uploading file:', error);
        } finally {
            setUploading(false);
        }
    };

    const shareLocation = () => {
        if (navigator.geolocation && ws) {
            navigator.geolocation.getCurrentPosition((position) => {
                const { latitude, longitude } = position.coords;
                const locationUrl = `https://www.google.com/maps?q=${latitude},${longitude}`;

                const messageData = {
                    type: 'chat_message',
                    sender_username: currentUsername,
                    message: `Location: ${latitude}, ${longitude}`,
                    msg_type: 'location',
                    attachment_url: locationUrl
                };

                if (chat.type === 'group') {
                    messageData.group_id = chat.data.id;
                } else {
                    messageData.receiver_username = chat.data.username;
                }

                ws.send(JSON.stringify(messageData));
            });
        }
    };

    if (!chat) {
        return (
            <div className="flex-1 flex items-center justify-center bg-gray-900">
                <div className="text-center">
                    <div className="text-6xl mb-4">💬</div>
                    <h2 className="text-2xl font-bold text-gray-400">Select a chat to start messaging</h2>
                </div>
            </div>
        );
    }

    return (
        <div className="flex-1 flex flex-col bg-gray-900">
            {/* Header */}
            <div className="p-4 border-b border-gray-700 bg-gray-800/50 backdrop-blur-sm">
                <div className="flex items-center space-x-3">
                    <div className={`w-12 h-12 rounded-full flex items-center justify-center text-white font-semibold ${chat.type === 'group'
                            ? 'bg-gradient-to-br from-blue-500 to-cyan-500'
                            : 'bg-gradient-to-br from-purple-500 to-pink-500'
                        }`}>
                        {chat.type === 'group' ? '#' : chat.data.username[0].toUpperCase()}
                    </div>
                    <div>
                        <h3 className="font-semibold text-lg">{chat.data.name || chat.data.username}</h3>
                        <p className="text-sm text-gray-400">
                            {chat.type === 'group' ? `${chat.data.members?.length || 0} members` : 'Online'}
                        </p>
                    </div>
                </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((msg, idx) => {
                    const isOwn = msg.sender_username === currentUsername;

                    return (
                        <div key={idx} className={`flex ${isOwn ? 'justify-end' : 'justify-start'}`}>
                            <div className={`max-w-md ${isOwn ? 'order-2' : 'order-1'}`}>
                                {!isOwn && chat.type === 'group' && (
                                    <p className="text-xs text-gray-400 mb-1 ml-2">{msg.sender_username}</p>
                                )}
                                <div className={`rounded-2xl px-4 py-2 ${isOwn
                                        ? 'bg-gradient-to-r from-purple-600 to-pink-600'
                                        : 'bg-gray-700'
                                    }`}>
                                    {msg.msg_type === 'text' && <p>{msg.text}</p>}
                                    {msg.msg_type === 'image' && (
                                        <div>
                                            <img src={msg.attachment_url} alt="Shared" className="rounded-lg max-w-xs" />
                                            <p className="text-sm mt-1">{msg.text}</p>
                                        </div>
                                    )}
                                    {msg.msg_type === 'video' && (
                                        <div>
                                            <video src={msg.attachment_url} controls className="rounded-lg max-w-xs" />
                                            <p className="text-sm mt-1">{msg.text}</p>
                                        </div>
                                    )}
                                    {msg.msg_type === 'file' && (
                                        <a href={msg.attachment_url} target="_blank" rel="noopener noreferrer" className="flex items-center space-x-2 hover:underline">
                                            <span>📎</span>
                                            <span>{msg.text}</span>
                                        </a>
                                    )}
                                    {msg.msg_type === 'location' && (
                                        <a href={msg.attachment_url} target="_blank" rel="noopener noreferrer" className="flex items-center space-x-2 hover:underline">
                                            <span>📍</span>
                                            <span>{msg.text}</span>
                                        </a>
                                    )}
                                </div>
                                <p className="text-xs text-gray-500 mt-1 ml-2">
                                    {new Date(msg.created_at).toLocaleTimeString()}
                                </p>
                            </div>
                        </div>
                    );
                })}
                <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="p-4 border-t border-gray-700 bg-gray-800/50 backdrop-blur-sm">
                <form onSubmit={sendMessage} className="flex items-center space-x-2">
                    <input
                        type="file"
                        ref={fileInputRef}
                        onChange={(e) => handleFileUpload(e, 'file')}
                        className="hidden"
                    />

                    <button
                        type="button"
                        onClick={() => fileInputRef.current?.click()}
                        className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
                        disabled={uploading}
                    >
                        📎
                    </button>

                    <button
                        type="button"
                        onClick={shareLocation}
                        className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
                    >
                        📍
                    </button>

                    <input
                        type="text"
                        value={newMessage}
                        onChange={(e) => setNewMessage(e.target.value)}
                        placeholder="Type a message..."
                        className="flex-1 px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                    />

                    <button
                        type="submit"
                        className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white px-6 py-3 rounded-lg transition-all transform hover:scale-105"
                    >
                        Send
                    </button>
                </form>
            </div>
        </div>
    );
}
