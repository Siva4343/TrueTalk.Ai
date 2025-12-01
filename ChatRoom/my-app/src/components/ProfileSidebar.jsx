import React, { useState } from 'react';

export default function ProfileSidebar({ user, messages, onClose }) {
    const [activeTab, setActiveTab] = useState('media');

    if (!user) return null;

    // Filter messages for media and files
    const mediaMessages = messages.filter(m =>
        (m.msg_type === 'image' || m.msg_type === 'video') &&
        ((m.sender_username === user.username) || (m.receiver_username === user.username))
    );

    const fileMessages = messages.filter(m =>
        m.msg_type === 'file' &&
        ((m.sender_username === user.username) || (m.receiver_username === user.username))
    );

    const getAvatarColor = (name) => {
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

    const getInitials = (name) => {
        return name ? name.substring(0, 2).toUpperCase() : '??';
    };

    return (
        <div className="fixed inset-0 bg-black z-50 flex flex-col animate-fadeIn">
            {/* Header */}
            <div className="p-4 bg-gray-900 border-b border-gray-800 flex items-center justify-between">
                <div className="max-w-4xl mx-auto w-full flex items-center justify-between">
                    <h2 className="text-xl font-bold text-white">Contact Info</h2>
                    <button onClick={onClose} className="p-2 hover:bg-gray-800 rounded-full text-gray-400 hover:text-white transition-colors">
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>
            </div>

            <div className="flex-1 overflow-y-auto">
                <div className="max-w-4xl mx-auto w-full">
                    {/* Profile Header */}
                    <div className="p-8 flex flex-col items-center border-b border-gray-800 bg-black">
                        <div className={`w-32 h-32 rounded-full ${getAvatarColor(user.username)} flex items-center justify-center text-white text-4xl font-bold mb-6 shadow-2xl ring-4 ring-gray-900`}>
                            {getInitials(user.username)}
                        </div>
                        <h3 className="text-3xl font-bold text-white mb-2">{user.name || user.username}</h3>
                        <p className="text-xl text-gray-400 mb-6">@{user.username}</p>
                        {user.phone_number && (
                            <div className="flex items-center space-x-3 text-gray-300 bg-gray-900 px-6 py-3 rounded-xl border border-gray-800">
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                                </svg>
                                <span className="text-lg">{user.phone_number}</span>
                            </div>
                        )}
                    </div>

                    {/* Media & Files Tabs */}
                    <div className="p-8">
                        <div className="flex border-b border-gray-800 mb-6">
                            <button
                                className={`flex-1 pb-4 text-lg font-medium transition-colors ${activeTab === 'media'
                                    ? 'text-blue-500 border-b-2 border-blue-500'
                                    : 'text-gray-400 hover:text-gray-200'
                                    }`}
                                onClick={() => setActiveTab('media')}
                            >
                                Media ({mediaMessages.length})
                            </button>
                            <button
                                className={`flex-1 pb-4 text-lg font-medium transition-colors ${activeTab === 'files'
                                    ? 'text-blue-500 border-b-2 border-blue-500'
                                    : 'text-gray-400 hover:text-gray-200'
                                    }`}
                                onClick={() => setActiveTab('files')}
                            >
                                Files ({fileMessages.length})
                            </button>
                        </div>

                        {/* Media Grid */}
                        {activeTab === 'media' && (
                            <div className="grid grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
                                {mediaMessages.map((msg, idx) => (
                                    <div key={idx} className="aspect-square bg-gray-900 rounded-xl overflow-hidden cursor-pointer hover:opacity-80 transition-opacity border border-gray-800 group relative">
                                        {msg.msg_type === 'image' ? (
                                            <img src={msg.attachment_url} alt="Media" className="w-full h-full object-cover" />
                                        ) : (
                                            <video src={msg.attachment_url} className="w-full h-full object-cover" />
                                        )}
                                        <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-all" />
                                    </div>
                                ))}
                                {mediaMessages.length === 0 && (
                                    <p className="col-span-full text-center text-gray-500 py-12 text-lg">No media shared</p>
                                )}
                            </div>
                        )}

                        {/* Files List */}
                        {activeTab === 'files' && (
                            <div className="space-y-3">
                                {fileMessages.map((msg, idx) => (
                                    <a
                                        key={idx}
                                        href={msg.attachment_url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="flex items-center p-4 bg-gray-900 rounded-xl hover:bg-gray-800 transition-colors border border-gray-800 group"
                                    >
                                        <div className="w-12 h-12 bg-gray-800 rounded-lg flex items-center justify-center mr-4 text-gray-400 group-hover:text-blue-500 transition-colors">
                                            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                                            </svg>
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className="text-base font-medium text-white truncate">{msg.text}</p>
                                            <p className="text-sm text-gray-500">Download</p>
                                        </div>
                                    </a>
                                ))}
                                {fileMessages.length === 0 && (
                                    <p className="text-center text-gray-500 py-12 text-lg">No files shared</p>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
