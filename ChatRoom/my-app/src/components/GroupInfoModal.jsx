import { useState } from 'react';

export default function GroupInfoModal({ group, onClose, onAddMember }) {
    const [newMember, setNewMember] = useState('');

    const handleAdd = (e) => {
        e.preventDefault();
        if (newMember.trim()) {
            onAddMember(newMember);
            setNewMember('');
        }
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center" onClick={onClose}>
            <div className="bg-gray-900 rounded-xl p-6 w-96 border border-gray-800" onClick={e => e.stopPropagation()}>
                <div className="flex justify-between items-center mb-6">
                    <h3 className="text-xl font-bold text-white">Group Info</h3>
                    <button onClick={onClose} className="text-gray-400 hover:text-white">
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                <div className="flex flex-col items-center mb-6">
                    <div className="w-20 h-20 bg-blue-600 rounded-full flex items-center justify-center text-white text-2xl font-bold mb-3">
                        {group.name.substring(0, 2).toUpperCase()}
                    </div>
                    <h2 className="text-2xl font-bold text-white">{group.name}</h2>
                    <p className="text-gray-400">{group.members?.length || 0} members</p>
                </div>

                <div className="mb-6">
                    <h4 className="text-sm font-semibold text-gray-500 uppercase mb-3">Add Member</h4>
                    <form onSubmit={handleAdd} className="flex space-x-2">
                        <input
                            type="text"
                            value={newMember}
                            onChange={(e) => setNewMember(e.target.value)}
                            placeholder="Username"
                            className="flex-1 px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                        <button
                            type="submit"
                            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                        >
                            Add
                        </button>
                    </form>
                </div>

                <div>
                    <h4 className="text-sm font-semibold text-gray-500 uppercase mb-3">Members</h4>
                    <div className="max-h-48 overflow-y-auto space-y-2">
                        {group.members?.map((member, idx) => (
                            <div key={idx} className="flex items-center space-x-3 p-2 hover:bg-gray-800 rounded-lg">
                                <div className="w-8 h-8 bg-gray-700 rounded-full flex items-center justify-center text-white text-xs">
                                    {member.username.substring(0, 2).toUpperCase()}
                                </div>
                                <span className="text-white">{member.username}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}
