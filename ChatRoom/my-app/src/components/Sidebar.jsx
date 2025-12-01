import { useState, useEffect } from 'react';

export default function Sidebar({ onSelectChat, currentChat, onShowProfile }) {
    const [users, setUsers] = useState([]);
    const [groups, setGroups] = useState([]);
    const [messages, setMessages] = useState([]);
    const [showCreateGroup, setShowCreateGroup] = useState(false);
    const [newGroupName, setNewGroupName] = useState('');
    const [selectedMembers, setSelectedMembers] = useState([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [activeMenuId, setActiveMenuId] = useState(null);
    const currentUsername = localStorage.getItem('username');
    const [currentUserData, setCurrentUserData] = useState(null);

    useEffect(() => {
        fetchUsers();
        fetchGroups();
        fetchMessages();

        // Poll for new messages every 3 seconds to keep sidebar updated
        const interval = setInterval(fetchMessages, 3000);
        return () => clearInterval(interval);
    }, []);

    const fetchUsers = async () => {
        try {
            const response = await fetch('http://localhost:8000/api/chat/users/');
            const data = await response.json();
            if (Array.isArray(data)) {
                setUsers(data.filter(u => u.username !== currentUsername));
                const me = data.find(u => u.username === currentUsername);
                if (me) setCurrentUserData(me);
            } else {
                console.error('Expected array of users, got:', data);
            }
        } catch (error) {
            console.error('Error fetching users:', error);
        }
    };

    const fetchGroups = async () => {
        try {
            const response = await fetch('http://localhost:8000/api/chat/groups/');
            const data = await response.json();
            if (Array.isArray(data)) {
                setGroups(data);
            }
        } catch (error) {
            console.error('Error fetching groups:', error);
        }
    };

    const fetchMessages = async () => {
        try {
            const response = await fetch('http://localhost:8000/api/chat/messages/');
            const data = await response.json();
            if (Array.isArray(data)) {
                setMessages(data);
            }
        } catch (error) {
            console.error('Error fetching messages:', error);
        }
    };

    const getLastMessage = (type, id, username) => {
        let chatMessages = [];
        if (type === 'group') {
            chatMessages = messages.filter(m => m.group_id === id);
        } else {
            chatMessages = messages.filter(m =>
                (m.sender_username === currentUsername && m.receiver_username === username) ||
                (m.sender_username === username && m.receiver_username === currentUsername)
            );
        }

        if (chatMessages.length === 0) return null;

        const lastMsg = chatMessages[chatMessages.length - 1];
        let preview = lastMsg.text;

        if (lastMsg.msg_type === 'image') preview = '📷 Photo';
        else if (lastMsg.msg_type === 'video') preview = '🎥 Video';
        else if (lastMsg.msg_type === 'file') preview = '📄 File';
        else if (lastMsg.msg_type === 'location') preview = '📍 Location';

        return {
            text: preview,
            time: new Date(lastMsg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            isOwn: lastMsg.sender_username === currentUsername
        };
    };

    const handleCreateGroup = async (e) => {
        e.preventDefault();
        if (!newGroupName.trim() || selectedMembers.length === 0) return;

        try {
            const response = await fetch('http://localhost:8000/api/chat/groups/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: newGroupName,
                    members: selectedMembers
                })
            });

            if (response.ok) {
                setNewGroupName('');
                setSelectedMembers([]);
                setShowCreateGroup(false);
                fetchGroups();
            }
        } catch (error) {
            console.error('Error creating group:', error);
        }
    };

    const toggleMember = (userId) => {
        setSelectedMembers(prev =>
            prev.includes(userId)
                ? prev.filter(id => id !== userId)
                : [...prev, userId]
        );
    };

    const getLastMessageTime = (type, id, username) => {
        let chatMessages = [];
        if (type === 'group') {
            chatMessages = messages.filter(m => m.group_id === id);
        } else {
            chatMessages = messages.filter(m =>
                (m.sender_username === currentUsername && m.receiver_username === username) ||
                (m.sender_username === username && m.receiver_username === currentUsername)
            );
        }

        if (chatMessages.length === 0) return 0;
        return new Date(chatMessages[chatMessages.length - 1].created_at).getTime();
    };

    const filteredUsers = users
        .filter(u => u.username.toLowerCase().includes(searchQuery.toLowerCase()))
        .sort((a, b) => {
            const timeA = getLastMessageTime('user', a.id, a.username);
            const timeB = getLastMessageTime('user', b.id, b.username);
            return timeB - timeA;
        });

    const filteredGroups = groups
        .filter(g => g.name.toLowerCase().includes(searchQuery.toLowerCase()))
        .sort((a, b) => {
            const timeA = getLastMessageTime('group', a.id);
            const timeB = getLastMessageTime('group', b.id);
            return timeB - timeA;
        });

    const getInitials = (name) => {
        if (!name) return '';
        return name.substring(0, 2).toUpperCase();
    };

    const getAvatarColor = (name) => {
        if (!name) return 'bg-gray-500';
        // Solid colors instead of gradients
        const colors = [
            'bg-blue-600',
            'bg-indigo-600',
            'bg-sky-600',
            'bg-teal-600',
            'bg-cyan-600',
            'bg-blue-700',
        ];
        const index = name.charCodeAt(0) % colors.length;
        return colors[index];
    };

    const deleteChat = async (type, id, otherUsername) => {
        if (!window.confirm('Are you sure you want to delete this chat?')) return;

        try {
            let url = `http://localhost:8000/api/chat/messages/delete_conversation/?username=${currentUsername}`;
            if (type === 'group') {
                url += `&group_id=${id}`;
            } else {
                url += `&other_username=${otherUsername}`;
            }

            const response = await fetch(url, { method: 'DELETE' });

            if (response.ok) {
                // Refresh data
                fetchMessages();
                fetchGroups();
                if (currentChat?.data?.id === id) {
                    onSelectChat(null);
                }
            }
        } catch (error) {
            console.error('Error deleting chat:', error);
        }
        setActiveMenuId(null);
    };

    return (
        <div className="w-96 bg-black border-r border-gray-800 flex flex-col h-screen" onClick={() => setActiveMenuId(null)}>
            {/* Header */}
            <div className="p-4 bg-gray-900 border-b border-gray-800">
                <div className="flex items-center justify-between mb-4">
                    <div
                        className="flex items-center space-x-3 cursor-pointer hover:bg-gray-800 p-2 rounded-lg transition-colors"
                        onClick={() => currentUserData && onShowProfile(currentUserData)}
                    >
                        <div className={`w-12 h-12 rounded-full ${getAvatarColor(currentUsername)} flex items-center justify-center text-white font-bold shadow-lg`}>
                            {getInitials(currentUsername)}
                        </div>
                        <div>
                            <h2 className="text-xl font-bold text-white">Chats</h2>
                            <p className="text-xs text-gray-400">@{currentUsername}</p>
                        </div>
                    </div>
                    <div className="flex space-x-2">
                        <button
                            onClick={() => setShowCreateGroup(!showCreateGroup)}
                            className="p-2 hover:bg-gray-800 rounded-full transition-colors"
                            title="New Group"
                        >
                            <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                            </svg>
                        </button>
                        <button
                            onClick={() => {
                                localStorage.removeItem('username');
                                window.location.reload();
                            }}
                            className="p-2 hover:bg-gray-800 rounded-full transition-colors text-red-400 hover:text-red-300"
                            title="Logout"
                        >
                            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                            </svg>
                        </button>
                    </div>
                </div>

                {/* Search Bar */}
                <div className="relative">
                    <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="Search chats..."
                        className="w-full px-4 py-2 pl-10 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-white placeholder-gray-500 text-sm"
                    />
                    <svg className="w-5 h-5 text-gray-500 absolute left-3 top-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                </div>
            </div>

            {/* Create Group Modal */}
            {showCreateGroup && (
                <div className="p-4 bg-gray-900 border-b border-gray-800">
                    <h3 className="text-lg font-semibold mb-3 text-white">Create New Group</h3>
                    <form onSubmit={handleCreateGroup} className="space-y-3">
                        <input
                            type="text"
                            value={newGroupName}
                            onChange={(e) => setNewGroupName(e.target.value)}
                            placeholder="Group name"
                            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                        <div className="max-h-40 overflow-y-auto space-y-2 bg-gray-800 rounded-lg p-2">
                            {users.map(user => (
                                <label key={user.id} className="flex items-center space-x-2 p-2 hover:bg-gray-700 rounded cursor-pointer">
                                    <input
                                        type="checkbox"
                                        checked={selectedMembers.includes(user.id)}
                                        onChange={() => toggleMember(user.id)}
                                        className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500"
                                    />
                                    <span className="text-sm text-white">{user.username}</span>
                                </label>
                            ))}
                        </div>
                        <div className="flex space-x-2">
                            <button
                                type="submit"
                                className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg text-sm font-medium transition-all"
                            >
                                Create
                            </button>
                            <button
                                type="button"
                                onClick={() => setShowCreateGroup(false)}
                                className="flex-1 bg-gray-800 hover:bg-gray-700 text-white py-2 rounded-lg text-sm font-medium transition-all"
                            >
                                Cancel
                            </button>
                        </div>
                    </form>
                </div>
            )}

            {/* Chat List */}
            <div className="flex-1 overflow-y-auto">
                {/* Direct Messages */}
                {filteredUsers.length > 0 && (
                    <div className="p-2">
                        <h3 className="text-xs font-semibold text-gray-500 px-3 py-2">DIRECT MESSAGES</h3>
                        {filteredUsers.map(user => {
                            const lastMsg = getLastMessage('user', user.id, user.username);
                            return (
                                <div
                                    key={user.id}
                                    className={`group relative flex items-center space-x-3 p-3 rounded-lg cursor-pointer transition-all mb-1 ${currentChat?.type === 'user' && currentChat?.data?.id === user.id
                                        ? 'bg-gray-800 border-l-4 border-blue-500'
                                        : 'hover:bg-gray-900'
                                        }`}
                                    onClick={() => onSelectChat({ type: 'user', data: user })}
                                >
                                    <div className={`w-12 h-12 rounded-full ${getAvatarColor(user.username)} flex items-center justify-center text-white font-semibold shadow-md flex-shrink-0`}>
                                        {getInitials(user.username)}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <div className="flex justify-between items-baseline">
                                            <p className="font-medium text-white truncate">{user.username}</p>
                                            {lastMsg && <span className="text-xs text-gray-500">{lastMsg.time}</span>}
                                        </div>
                                        <p className="text-sm text-gray-400 truncate">
                                            {lastMsg ? (
                                                <span>{lastMsg.isOwn ? 'You: ' : ''}{lastMsg.text}</span>
                                            ) : (
                                                'Click to chat'
                                            )}
                                        </p>
                                    </div>

                                    {/* Hover Menu Button */}
                                    <button
                                        className="absolute right-2 top-1/2 transform -translate-y-1/2 p-2 rounded-full bg-gray-800 text-gray-400 opacity-0 group-hover:opacity-100 hover:bg-gray-700 hover:text-white transition-all shadow-lg z-10"
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            setActiveMenuId(activeMenuId === `user-${user.id}` ? null : `user-${user.id}`);
                                        }}
                                    >
                                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                                            <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
                                        </svg>
                                    </button>

                                    {/* Dropdown Menu */}
                                    {activeMenuId === `user-${user.id}` && (
                                        <div className="absolute right-0 top-10 w-48 bg-gray-900 rounded-lg shadow-xl border border-gray-800 z-50 overflow-hidden animate-fadeIn">
                                            <button
                                                className="w-full text-left px-4 py-3 text-sm text-gray-300 hover:bg-gray-800 hover:text-white transition-colors flex items-center"
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    onShowProfile(user);
                                                    setActiveMenuId(null);
                                                }}
                                            >
                                                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                                </svg>
                                                Show Info
                                            </button>
                                            <button
                                                className="w-full text-left px-4 py-3 text-sm text-red-400 hover:bg-gray-800 hover:text-red-300 transition-colors flex items-center border-t border-gray-800"
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    deleteChat('user', user.id, user.username);
                                                }}
                                            >
                                                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                                </svg>
                                                Delete Chat
                                            </button>
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                )}

                {/* Groups */}
                {filteredGroups.length > 0 && (
                    <div className="p-2 border-t border-gray-800">
                        <h3 className="text-xs font-semibold text-gray-500 px-3 py-2">GROUPS</h3>
                        {filteredGroups.map(group => {
                            const lastMsg = getLastMessage('group', group.id);
                            return (
                                <div
                                    key={group.id}
                                    className={`group relative flex items-center space-x-3 p-3 rounded-lg cursor-pointer transition-all mb-1 ${currentChat?.type === 'group' && currentChat?.data?.id === group.id
                                        ? 'bg-gray-800 border-l-4 border-blue-500'
                                        : 'hover:bg-gray-900'
                                        }`}
                                    onClick={() => onSelectChat({ type: 'group', data: group })}
                                >
                                    <div className="w-12 h-12 rounded-full bg-blue-600 flex items-center justify-center text-white font-semibold shadow-md flex-shrink-0">
                                        <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                                            <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3zM6 8a2 2 0 11-4 0 2 2 0 014 0zM16 18v-3a5.972 5.972 0 00-.75-2.906A3.005 3.005 0 0119 15v3h-3zM4.75 12.094A5.973 5.973 0 004 15v3H1v-3a3 3 0 013.75-2.906z" />
                                        </svg>
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <div className="flex justify-between items-baseline">
                                            <p className="font-medium text-white truncate">{group.name}</p>
                                            {lastMsg && <span className="text-xs text-gray-500">{lastMsg.time}</span>}
                                        </div>
                                        <p className="text-sm text-gray-400 truncate">
                                            {lastMsg ? (
                                                <span>{lastMsg.isOwn ? 'You: ' : ''}{lastMsg.text}</span>
                                            ) : (
                                                `${group.members?.length || 0} members`
                                            )}
                                        </p>
                                    </div>

                                    {/* Hover Menu Button */}
                                    <button
                                        className="absolute right-2 top-1/2 transform -translate-y-1/2 p-2 rounded-full bg-gray-800 text-gray-400 opacity-0 group-hover:opacity-100 hover:bg-gray-700 hover:text-white transition-all shadow-lg z-10"
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            setActiveMenuId(activeMenuId === `group-${group.id}` ? null : `group-${group.id}`);
                                        }}
                                    >
                                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                                            <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
                                        </svg>
                                    </button>

                                    {/* Dropdown Menu */}
                                    {activeMenuId === `group-${group.id}` && (
                                        <div className="absolute right-0 top-10 w-48 bg-gray-900 rounded-lg shadow-xl border border-gray-800 z-50 overflow-hidden animate-fadeIn">
                                            <button
                                                className="w-full text-left px-4 py-3 text-sm text-red-400 hover:bg-gray-800 hover:text-red-300 transition-colors flex items-center border-t border-gray-800"
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    deleteChat('group', group.id);
                                                }}
                                            >
                                                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                                </svg>
                                                Delete Group
                                            </button>
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                )}

                {/* Empty State */}
                {filteredUsers.length === 0 && filteredGroups.length === 0 && (
                    <div className="flex flex-col items-center justify-center h-64 text-gray-600">
                        <svg className="w-16 h-16 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                        </svg>
                        <p className="text-sm">No chats found</p>
                    </div>
                )}
            </div>
        </div>
    );
}
