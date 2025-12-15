import { useState } from 'react';
import { X, Search, Pin, MoreVertical } from 'lucide-react';

export default function ParticipantsSidebar({ 
    participants = [], 
    currentUser,
    onClose,
    onPinParticipant,
    pinnedParticipant
}) {
    const [searchTerm, setSearchTerm] = useState('');

    const allParticipants = [
        { 
            ...currentUser, 
            isCurrent: true,
            isConnected: true
        },
        ...participants
    ];

    const filteredParticipants = allParticipants.filter(participant =>
        participant.name.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="w-80 bg-[#292929] border-l border-[#3d3d3d] flex flex-col">
            {/* Header */}
            <div className="p-4 border-b border-[#3d3d3d] flex items-center justify-between">
                <div>
                    <h2 className="font-semibold text-white text-sm">Participants</h2>
                    <p className="text-gray-500 text-xs">{allParticipants.length} people</p>
                </div>
                <button
                    onClick={onClose}
                    className="hover:bg-[#3d3d3d] p-1.5 rounded-md transition-all text-gray-400 hover:text-white"
                >
                    <X className="w-4 h-4" />
                </button>
            </div>

            {/* Search */}
            <div className="p-3 border-b border-[#3d3d3d]">
                <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input
                        type="text"
                        placeholder="Search participants"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full pl-9 pr-3 py-2 bg-[#1e1e1e] border border-[#3d3d3d] rounded text-white text-sm placeholder-gray-500 focus:outline-none focus:border-[#5b5fc7]"
                    />
                </div>
            </div>

            {/* Participants List */}
            <div className="flex-1 overflow-y-auto p-2">
                {filteredParticipants.map((participant) => (
                    <div
                        key={participant.id}
                        className="flex items-center justify-between p-3 hover:bg-[#3d3d3d] rounded transition-all group"
                    >
                        <div className="flex items-center gap-3 flex-1 min-w-0">
                            {/* Avatar */}
                            <div className="relative">
                                <div className="w-10 h-10 bg-gradient-to-br from-[#464775] to-[#5b5fc7] rounded-full flex items-center justify-center">
                                    <span className="text-white text-sm font-semibold">
                                        {participant.name.charAt(0).toUpperCase()}
                                    </span>
                                </div>
                                {participant.isCurrent && (
                                    <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-[#5b5fc7] rounded-full border-2 border-[#292929]"></div>
                                )}
                            </div>

                            {/* Info */}
                            <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2">
                                    <p className="text-white text-sm font-medium truncate">
                                        {participant.name}
                                    </p>
                                </div>
                                <div className="flex items-center gap-2 mt-1">
                                    <div className="flex items-center gap-1">
                                        <div className={`w-2 h-2 rounded-full ${participant.isConnected ? 'bg-green-500' : 'bg-gray-500'}`}></div>
                                        <span className="text-gray-400 text-xs">
                                            {participant.isConnected ? 'Connected' : 'Disconnected'}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Controls */}
                        <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button
                                onClick={() => onPinParticipant(participant.id)}
                                className={`p-1.5 rounded ${pinnedParticipant === participant.id ? 'text-[#5b5fc7] bg-[#5b5fc7]/20' : 'text-gray-400 hover:text-white hover:bg-[#3d3d3d]'}`}
                                title={pinnedParticipant === participant.id ? 'Unpin' : 'Pin participant'}
                            >
                                <Pin className="w-4 h-4" />
                            </button>
                            <button className="p-1.5 rounded text-gray-400 hover:text-white hover:bg-[#3d3d3d]">
                                <MoreVertical className="w-4 h-4" />
                            </button>
                        </div>
                    </div>
                ))}
            </div>

            {/* Footer */}
            <div className="p-4 border-t border-[#3d3d3d] bg-[#1e1e1e]">
                <button className="w-full py-2 px-4 bg-[#5b5fc7] hover:bg-[#4d52b8] text-white text-sm font-medium rounded transition-all">
                    Invite people
                </button>
            </div>
        </div>
    );
}