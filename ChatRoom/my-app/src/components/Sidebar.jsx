import { useState, useEffect } from 'react';

export default function Sidebar({ onSelectChat, currentChat }) {
    const [users, setUsers] = useState([]);
    const [groups, setGroups] = useState([]);
    const [messages, setMessages] = useState([]);
    const [showCreateGroup, setShowCreateGroup] = useState(false);
    const [newGroupName, setNewGroupName] = useState('');
    const [selectedMembers, setSelectedMembers] = useState([]);
    const [searchQuery, setSearchQuery] = useState('');
    const currentUsername = localStorage.getItem('username');

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
            setUsers(data.filter(u => u.username !== currentUsername));
        } catch (error) {
            console.error('Error fetching users:', error);
        }
    };

    const fetchGroups = async () => {
        try {
            const response = await fetch('http://localhost:8000/api/chat/groups/');
            const data = await response.json();
            setGroups(data);
        } catch (error) {
            console.error('Error fetching groups:', error);
        }
    };

    const fetchMessages = async () => {
        try {
            const response = await fetch('http://localhost:8000/api/chat/messages/');
            const data = await response.json();
            setMessages(data);
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

    const filteredUsers = users.filter(u =>
        u.username.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const filteredGroups = groups.filter(g =>
        g.name.toLowerCase().includes(searchQuery.toLowerCase())
    );

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

    return (
        <div className="w-96 bg-gray-800 border-r border-gray-700 flex flex-col h-screen">
            {/* Header */}
            <div className="p-4 bg-gray-900 border-b border-gray-700">
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-3">
                        <div className={`w-12 h-12 rounded-full bg-gradient-to-br ${getAvatarColor(currentUsername)} flex items-center justify-center text-white font-bold shadow-lg`}>
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
                            className="p-2 hover:bg-gray-700 rounded-full transition-colors"
                            title="New Group"
                        >
                            <svg className="w-6 h-6 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                            </svg>
                        </button>
                        <button
                            onClick={() => {
                                localStorage.removeItem('username');
                                window.location.reload();
                            }}
                            className="p-2 hover:bg-gray-700 rounded-full transition-colors text-red-400 hover:text-red-300"
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
                        className="w-full px-4 py-2 pl-10 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 text-white placeholder-gray-400 text-sm"
                    />
                    <svg className="w-5 h-5 text-gray-400 absolute left-3 top-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                </div>
            </div>

            {/* Create Group Modal */}
            {showCreateGroup && (
                <div className="p-4 bg-gray-900 border-b border-gray-700">
                    <h3 className="text-lg font-semibold mb-3 text-white">Create New Group</h3>
                    <form onSubmit={handleCreateGroup} className="space-y-3">
                        <input
                            type="text"
                            value={newGroupName}
                            onChange={(e) => setNewGroupName(e.target.value)}
                            placeholder="Group name"
                            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                        />
                        <div className="max-h-40 overflow-y-auto space-y-2 bg-gray-800 rounded-lg p-2">
                            {users.map(user => (
                                <label key={user.id} className="flex items-center space-x-2 p-2 hover:bg-gray-700 rounded cursor-pointer">
                                    <input
                                        type="checkbox"
                                        checked={selectedMembers.includes(user.id)}
                                        onChange={() => toggleMember(user.id)}
                                        className="w-4 h-4 text-purple-600 bg-gray-700 border-gray-600 rounded focus:ring-purple-500"
                                    />
                                    <span className="text-sm text-white">{user.username}</span>
                                </label>
                            ))}
                        </div>
                        <div className="flex space-x-2">
                            <button
                                type="submit"
                                className="flex-1 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white py-2 rounded-lg text-sm font-medium transition-all"
                            >
                                Create
                            </button>
                            <button
                                type="button"
                                onClick={() => setShowCreateGroup(false)}
                                className="flex-1 bg-gray-700 hover:bg-gray-600 text-white py-2 rounded-lg text-sm font-medium transition-all"
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
                        <h3 className="text-xs font-semibold text-gray-400 px-3 py-2">DIRECT MESSAGES</h3>
                        {filteredUsers.map(user => {
                            const lastMsg = getLastMessage('user', user.id, user.username);
                            return (
                                <div
                                    key={user.id}
                                    onClick={() => onSelectChat({ type: 'user', data: user })}
                                    className={`flex items-center space-x-3 p-3 rounded-lg cursor-pointer transition-all mb-1 ${currentChat?.type === 'user' && currentChat?.data?.id === user.id
                                        ? 'bg-gray-700'
                                        : 'hover:bg-gray-700/50'
                                        }`}
                                >
                                    <div className={`w-12 h-12 rounded-full bg-gradient-to-br ${getAvatarColor(user.username)} flex items-center justify-center text-white font-semibold shadow-md flex-shrink-0`}>
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
                                    {/* Online Indicator - could be dynamic later */}
                                    <div className="w-3 h-3 bg-green-500 rounded-full flex-shrink-0 border-2 border-gray-800"></div>
                                </div>
                            );
                        })}
                    </div>
                )}

                {/* Groups */}
                {filteredGroups.length > 0 && (
                    <div className="p-2 border-t border-gray-700">
                        <h3 className="text-xs font-semibold text-gray-400 px-3 py-2">GROUPS</h3>
                        {filteredGroups.map(group => {
                            const lastMsg = getLastMessage('group', group.id);
                            return (
                                <div
                                    key={group.id}
                                    onClick={() => onSelectChat({ type: 'group', data: group })}
                                    className={`flex items-center space-x-3 p-3 rounded-lg cursor-pointer transition-all mb-1 ${currentChat?.type === 'group' && currentChat?.data?.id === group.id
                                        ? 'bg-gray-700'
                                        : 'hover:bg-gray-700/50'
                                        }`}
                                >
                                    <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center text-white font-semibold shadow-md flex-shrink-0">
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
                                </div>
                            );
                        })}
                    </div>
                )}

                {/* Empty State */}
                {filteredUsers.length === 0 && filteredGroups.length === 0 && (
                    <div className="flex flex-col items-center justify-center h-64 text-gray-500">
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
