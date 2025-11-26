import { useState, useEffect, useRef } from 'react';

export default function Sidebar({ onSelectChat, currentChat }) {
    const [users, setUsers] = useState([]);
    const [groups, setGroups] = useState([]);
    const [showCreateGroup, setShowCreateGroup] = useState(false);
    const [newGroupName, setNewGroupName] = useState('');
    const [selectedMembers, setSelectedMembers] = useState([]);
    const currentUsername = localStorage.getItem('username');

    useEffect(() => {
        fetchUsers();
        fetchGroups();
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

    return (
        <div className="w-80 bg-gray-800/50 backdrop-blur-sm border-r border-gray-700 flex flex-col">
            <div className="p-4 border-b border-gray-700">
                <h2 className="text-xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                    Chats
                </h2>
                <p className="text-sm text-gray-400">@{currentUsername}</p>
            </div>

            <div className="flex-1 overflow-y-auto">
                {/* Users Section */}
                <div className="p-4">
                    <h3 className="text-sm font-semibold text-gray-400 mb-2">Direct Messages</h3>
                    {users.map(user => (
                        <div
                            key={user.id}
                            onClick={() => onSelectChat({ type: 'user', data: user })}
                            className={`p-3 rounded-lg cursor-pointer transition-all mb-2 ${currentChat?.type === 'user' && currentChat?.data?.id === user.id
                                    ? 'bg-purple-600/30 border border-purple-500/50'
                                    : 'hover:bg-gray-700/50'
                                }`}
                        >
                            <div className="flex items-center space-x-3">
                                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white font-semibold">
                                    {user.username[0].toUpperCase()}
                                </div>
                                <div>
                                    <p className="font-medium">{user.username}</p>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                {/* Groups Section */}
                <div className="p-4 border-t border-gray-700">
                    <div className="flex justify-between items-center mb-2">
                        <h3 className="text-sm font-semibold text-gray-400">Groups</h3>
                        <button
                            onClick={() => setShowCreateGroup(!showCreateGroup)}
                            className="text-purple-400 hover:text-purple-300 text-sm"
                        >
                            + New
                        </button>
                    </div>

                    {showCreateGroup && (
                        <form onSubmit={handleCreateGroup} className="mb-4 p-3 bg-gray-700/50 rounded-lg">
                            <input
                                type="text"
                                value={newGroupName}
                                onChange={(e) => setNewGroupName(e.target.value)}
                                placeholder="Group name"
                                className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded mb-2 text-sm"
                            />
                            <div className="max-h-32 overflow-y-auto mb-2">
                                {users.map(user => (
                                    <label key={user.id} className="flex items-center space-x-2 text-sm py-1">
                                        <input
                                            type="checkbox"
                                            checked={selectedMembers.includes(user.id)}
                                            onChange={() => toggleMember(user.id)}
                                            className="rounded"
                                        />
                                        <span>{user.username}</span>
                                    </label>
                                ))}
                            </div>
                            <button
                                type="submit"
                                className="w-full bg-purple-600 hover:bg-purple-700 text-white py-2 rounded text-sm"
                            >
                                Create Group
                            </button>
                        </form>
                    )}

                    {groups.map(group => (
                        <div
                            key={group.id}
                            onClick={() => onSelectChat({ type: 'group', data: group })}
                            className={`p-3 rounded-lg cursor-pointer transition-all mb-2 ${currentChat?.type === 'group' && currentChat?.data?.id === group.id
                                    ? 'bg-purple-600/30 border border-purple-500/50'
                                    : 'hover:bg-gray-700/50'
                                }`}
                        >
                            <div className="flex items-center space-x-3">
                                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center text-white font-semibold">
                                    #
                                </div>
                                <div>
                                    <p className="font-medium">{group.name}</p>
                                    <p className="text-xs text-gray-400">{group.members?.length || 0} members</p>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
