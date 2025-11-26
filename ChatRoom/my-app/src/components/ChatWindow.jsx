import { useState, useEffect, useRef } from 'react';

export default function ChatWindow({ chat }) {
    const [messages, setMessages] = useState([]);
    const [newMessage, setNewMessage] = useState('');
    const [ws, setWs] = useState(null);
    const [uploading, setUploading] = useState(false);
    const messagesEndRef = useRef(null);
    const fileInputRef = useRef(null);
    const imageInputRef = useRef(null);
    const currentUsername = localStorage.getItem('username');

    useEffect(() => {
        if (!chat) return;

        // Determine room name
        const roomName = chat.type === 'group'
            ? `group_${chat.data.id}`
            : `user_${[currentUsername, chat.data.username].sort().join('_')}`;

        // Connect to WebSocket
        const websocket = new WebSocket(`ws://localhost:8000/ws/chat/${roomName}/`);

        websocket.onopen = () => {
            console.log('WebSocket connected');
        };

        websocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'chat_message') {
                setMessages(prev => [...prev, data.message]);

                // If we receive a message in the current chat, mark it as read immediately
                if (data.message.sender_username !== currentUsername) {
                    websocket.send(JSON.stringify({
                        type: 'read_receipt',
                        message_id: data.message.id,
                        reader_username: currentUsername
                    }));
                }
            } else if (data.type === 'read_receipt') {
                setMessages(prev => prev.map(msg =>
                    msg.id === data.message_id ? { ...msg, is_read: true } : msg
                ));
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

    // Helper for ticks
    const StatusTicks = ({ isRead }) => (
        <span className="ml-1 inline-flex">
            {isRead ? (
                <div className="flex text-blue-400">
                    <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20"><path d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" /></svg>
                    <svg className="w-3 h-3 -ml-1" fill="currentColor" viewBox="0 0 20 20"><path d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" /></svg>
                </div>
            ) : (
                <svg className="w-3 h-3 text-gray-400" fill="currentColor" viewBox="0 0 20 20"><path d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" /></svg>
            )}
        </span>
    );

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });

        // Mark unread messages as read when opening chat
        if (ws && ws.readyState === WebSocket.OPEN && messages.length > 0) {
            messages.forEach(msg => {
                if (!msg.is_read && msg.sender_username !== currentUsername) {
                    ws.send(JSON.stringify({
                        type: 'read_receipt',
                        message_id: msg.id,
                        reader_username: currentUsername
                    }));
                }
            });
        }
    }, [messages, ws]);

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
            e.target.value = '';
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
                    message: `📍 Location: ${latitude.toFixed(4)}, ${longitude.toFixed(4)}`,
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

    const getInitials = (name) => {
        return name.substring(0, 2).toUpperCase();
    };

    const getAvatarColor = (name) => {
        const colors = [
            'from-purple-500 to-pink-500',
            'from-blue-500 to-cyan-500',
            'from-green-500 to-emerald-500',
            'from-orange-500 to-red-500',
            'from-indigo-500 to-purple-500',
            'from-pink-500 to-rose-500',
        ];
        const index = name.charCodeAt(0) % colors.length;
        return colors[index];
    };

    const formatTime = (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    };

    if (!chat) {
        return (
            <div className="flex-1 flex items-center justify-center bg-gray-900">
                <div className="text-center">
                    <div className="w-32 h-32 mx-auto mb-6 bg-gray-800 rounded-full flex items-center justify-center">
                        <svg className="w-16 h-16 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                        </svg>
                    </div>
                    <h2 className="text-2xl font-bold text-gray-300 mb-2">TrueTalk.Ai</h2>
                    <p className="text-gray-500">Select a chat to start messaging</p>
                </div>
            </div>
        );
    }

    return (
        <div className="flex-1 flex flex-col bg-gray-900 h-screen">
            {/* Header */}
            <div className="px-6 py-4 bg-gray-800 border-b border-gray-700 flex items-center justify-between">
                <div className="flex items-center space-x-4">
                    <div className={`w-12 h-12 rounded-full bg-gradient-to-br ${chat.type === 'group'
                        ? 'from-blue-500 to-cyan-500'
                        : getAvatarColor(chat.data.username || chat.data.name)
                        } flex items-center justify-center text-white font-semibold shadow-lg`}>
                        {chat.type === 'group' ? (
                            <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                                <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3zM6 8a2 2 0 11-4 0 2 2 0 014 0zM16 18v-3a5.972 5.972 0 00-.75-2.906A3.005 3.005 0 0119 15v3h-3zM4.75 12.094A5.973 5.973 0 004 15v3H1v-3a3 3 0 013.75-2.906z" />
                            </svg>
                        ) : (
                            getInitials(chat.data.username)
                        )}
                    </div>
                    <div>
                        <h3 className="font-semibold text-lg text-white">{chat.data.name || chat.data.username}</h3>
                        <p className="text-sm text-gray-400">
                            {chat.type === 'group' ? `${chat.data.members?.length || 0} members` : 'Online'}
                        </p>
                    </div>
                </div>

                <div className="flex items-center space-x-2">
                    <button className="p-2 hover:bg-gray-700 rounded-full transition-colors">
                        <svg className="w-6 h-6 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                    </button>
                    <button className="p-2 hover:bg-gray-700 rounded-full transition-colors">
                        <svg className="w-6 h-6 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
                        </svg>
                    </button>
                </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI0MCIgaGVpZ2h0PSI0MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSAwIDEwIEwgNDAgMTAgTSAxMCAwIEwgMTAgNDAgTSAwIDIwIEwgNDAgMjAgTSAyMCAwIEwgMjAgNDAgTSAwIDMwIEwgNDAgMzAgTSAzMCAwIEwgMzAgNDAiIGZpbGw9Im5vbmUiIHN0cm9rZT0icmdiYSgyNTUsMjU1LDI1NSwwLjAyKSIgc3Ryb2tlLXdpZHRoPSIxIi8+PC9wYXR0ZXJuPjwvZGVmcz48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSJ1cmwoI2dyaWQpIi8+PC9zdmc+')] bg-gray-900">
                {messages.map((msg, idx) => {
                    const isOwn = msg.sender_username === currentUsername;

                    return (
                        <div key={idx} className={`flex ${isOwn ? 'justify-end' : 'justify-start'} animate-fadeIn`}>
                            <div className={`flex items-end space-x-2 max-w-lg ${isOwn ? 'flex-row-reverse space-x-reverse' : ''}`}>
                                {!isOwn && (
                                    <div className={`w-8 h-8 rounded-full bg-gradient-to-br ${getAvatarColor(msg.sender_username)} flex items-center justify-center text-white text-xs font-semibold flex-shrink-0`}>
                                        {getInitials(msg.sender_username)}
                                    </div>
                                )}

                                <div className="flex flex-col">
                                    {!isOwn && chat.type === 'group' && (
                                        <p className="text-xs text-gray-400 mb-1 ml-2">{msg.sender_username}</p>
                                    )}

                                    <div className={`rounded-2xl px-4 py-2 shadow-lg ${isOwn
                                        ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-br-sm'
                                        : 'bg-gray-800 text-white rounded-bl-sm'
                                        }`}>
                                        {msg.msg_type === 'text' && (
                                            <p className="break-words">{msg.text}</p>
                                        )}

                                        {msg.msg_type === 'image' && (
                                            <div>
                                                <img
                                                    src={msg.attachment_url}
                                                    alt="Shared"
                                                    className="rounded-lg max-w-sm mb-2 cursor-pointer hover:opacity-90 transition-opacity"
                                                />
                                                {msg.text && <p className="text-sm">{msg.text}</p>}
                                            </div>
                                        )}

                                        {msg.msg_type === 'video' && (
                                            <div>
                                                <video
                                                    src={msg.attachment_url}
                                                    controls
                                                    className="rounded-lg max-w-sm mb-2"
                                                />
                                                {msg.text && <p className="text-sm">{msg.text}</p>}
                                            </div>
                                        )}

                                        {msg.msg_type === 'file' && (
                                            <a
                                                href={msg.attachment_url}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="flex items-center space-x-3 hover:opacity-80 transition-opacity"
                                            >
                                                <div className="w-12 h-12 bg-gray-700 rounded-lg flex items-center justify-center">
                                                    <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                                                        <path fillRule="evenodd" d="M8 4a3 3 0 00-3 3v4a5 5 0 0010 0V7a1 1 0 112 0v4a7 7 0 11-14 0V7a5 5 0 0110 0v4a3 3 0 11-6 0V7a1 1 0 012 0v4a1 1 0 102 0V7a3 3 0 00-3-3z" clipRule="evenodd" />
                                                    </svg>
                                                </div>
                                                <div>
                                                    <p className="font-medium">{msg.text}</p>
                                                    <p className="text-xs opacity-75">Click to download</p>
                                                </div>
                                            </a>
                                        )}

                                        {msg.msg_type === 'location' && (
                                            <a
                                                href={msg.attachment_url}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="flex items-center space-x-3 hover:opacity-80 transition-opacity"
                                            >
                                                <div className="w-12 h-12 bg-red-500 rounded-lg flex items-center justify-center">
                                                    <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                                                        <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
                                                    </svg>
                                                </div>
                                                <div>
                                                    <p className="font-medium">Location Shared</p>
                                                    <p className="text-xs opacity-75">Click to view on map</p>
                                                </div>
                                            </a>
                                        )}

                                        <div className={`flex items-center justify-end space-x-1 mt-1`}>
                                            <p className={`text-xs ${isOwn ? 'text-purple-200' : 'text-gray-400'}`}>
                                                {formatTime(msg.created_at)}
                                            </p>
                                            {isOwn && <StatusTicks isRead={msg.is_read} />}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    );
                })}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="px-6 py-4 bg-gray-800 border-t border-gray-700">
                {uploading && (
                    <div className="mb-2 text-sm text-gray-400 flex items-center space-x-2">
                        <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        <span>Uploading...</span>
                    </div>
                )}

                <form onSubmit={sendMessage} className="flex items-center space-x-3">
                    <input
                        type="file"
                        ref={fileInputRef}
                        onChange={(e) => handleFileUpload(e, 'file')}
                        className="hidden"
                    />

                    <input
                        type="file"
                        ref={imageInputRef}
                        accept="image/*,video/*"
                        onChange={(e) => {
                            const file = e.target.files[0];
                            if (file) {
                                const type = file.type.startsWith('video/') ? 'video' : 'image';
                                handleFileUpload(e, type);
                            }
                        }}
                        className="hidden"
                    />

                    <div className="flex items-center space-x-1">
                        <button
                            type="button"
                            onClick={() => imageInputRef.current?.click()}
                            className="p-2 hover:bg-gray-700 rounded-full transition-colors text-gray-400 hover:text-purple-400"
                            disabled={uploading}
                            title="Send image/video"
                        >
                            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                            </svg>
                        </button>

                        <button
                            type="button"
                            onClick={() => fileInputRef.current?.click()}
                            className="p-2 hover:bg-gray-700 rounded-full transition-colors text-gray-400 hover:text-purple-400"
                            disabled={uploading}
                            title="Send file"
                        >
                            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                            </svg>
                        </button>

                        <button
                            type="button"
                            onClick={shareLocation}
                            className="p-2 hover:bg-gray-700 rounded-full transition-colors text-gray-400 hover:text-purple-400"
                            title="Share location"
                        >
                            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                            </svg>
                        </button>
                    </div>

                    <input
                        type="text"
                        value={newMessage}
                        onChange={(e) => setNewMessage(e.target.value)}
                        placeholder="Type a message..."
                        className="flex-1 px-4 py-3 bg-gray-700 border border-gray-600 rounded-full focus:outline-none focus:ring-2 focus:ring-purple-500 text-white placeholder-gray-400"
                    />

                    <button
                        type="submit"
                        disabled={!newMessage.trim()}
                        className="p-3 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 disabled:from-gray-600 disabled:to-gray-600 text-white rounded-full transition-all transform hover:scale-105 disabled:scale-100 disabled:cursor-not-allowed shadow-lg"
                    >
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                        </svg>
                    </button>
                </form>
            </div>
        </div>
    );
}
