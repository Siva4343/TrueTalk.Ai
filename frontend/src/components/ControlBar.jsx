import { Mic, MicOff, Video, VideoOff, MessageSquare, PhoneOff, Smile, Users, MoreHorizontal, Monitor, MonitorOff } from 'lucide-react';
import { useState } from 'react';

function ControlBar({
    isMuted,
    isVideoOff,
    isScreenSharing,
    onToggleMute,
    onToggleVideo,
    onToggleScreenShare,
    onToggleChat,
    onToggleParticipants,
    onLeave,
    onSendReaction,
    showChat,
    showParticipants,
}) {
    const [showReactions, setShowReactions] = useState(false);

    const reactions = [
        { emoji: '👍', label: 'Like' },
        { emoji: '❤️', label: 'Love' },
        { emoji: '😂', label: 'Laugh' },
        { emoji: '👏', label: 'Applause' },
        { emoji: '🎉', label: 'Celebrate' },
        { emoji: '✋', label: 'Raise hand' },
    ];

    const handleReaction = (emoji) => {
        onSendReaction(emoji);
        setShowReactions(false);
    };

    return (
        <div className="bg-[#292929] border-t border-[#3d3d3d] px-4 py-3">
            <div className="flex items-center justify-center gap-2">
                {/* Mute Button - SIMPLIFIED AND CORRECT */}
                <button
                    onClick={onToggleMute}
                    className={`group relative flex flex-col items-center gap-1 px-4 py-2 rounded-md transition-all ${isMuted
                        ? 'bg-[#c4314b] hover:bg-[#a92b40]'
                        : 'bg-[#3d3d3d] hover:bg-[#4d4d4d]'
                        }`}
                    title={isMuted ? 'Click to unmute' : 'Click to mute'}
                >
                    {/* Icon changes based on isMuted */}
                    {isMuted ? (
                        <>
                            <MicOff className="w-5 h-5 text-white" />
                            <span className="text-xs text-white">Unmute</span>
                        </>
                    ) : (
                        <>
                            <Mic className="w-5 h-5 text-white" />
                            <span className="text-xs text-white">Mute</span>
                        </>
                    )}
                </button>

                {/* Video Button */}
                <button
                    onClick={onToggleVideo}
                    className={`group relative flex flex-col items-center gap-1 px-4 py-2 rounded-md transition-all ${isVideoOff
                        ? 'bg-[#c4314b] hover:bg-[#a92b40]'
                        : 'bg-[#3d3d3d] hover:bg-[#4d4d4d]'
                        }`}
                >
                    {isVideoOff ? (
                        <>
                            <VideoOff className="w-5 h-5 text-white" />
                            <span className="text-xs text-white">Camera Off</span>
                        </>
                    ) : (
                        <>
                            <Video className="w-5 h-5 text-white" />
                            <span className="text-xs text-white">Camera On</span>
                        </>
                    )}
                </button>

                {/* Screen Share Button */}
                <button
                    onClick={onToggleScreenShare}
                    className={`group relative flex flex-col items-center gap-1 px-4 py-2 rounded-md transition-all ${isScreenSharing
                        ? 'bg-[#5b5fc7] hover:bg-[#4d52b8]'
                        : 'bg-[#3d3d3d] hover:bg-[#4d4d4d]'
                        }`}
                >
                    {isScreenSharing ? (
                        <MonitorOff className="w-5 h-5 text-white" />
                    ) : (
                        <Monitor className="w-5 h-5 text-white" />
                    )}
                    <span className="text-xs text-white">{isScreenSharing ? 'Stop' : 'Share'}</span>
                </button>

                {/* Reactions Button */}
                <div className="relative">
                    <button
                        onClick={() => setShowReactions(!showReactions)}
                        className="group relative flex flex-col items-center gap-1 px-4 py-2 rounded-md bg-[#3d3d3d] hover:bg-[#4d4d4d] transition-all"
                    >
                        <Smile className="w-5 h-5 text-white" />
                        <span className="text-xs text-white">React</span>
                    </button>

                    {/* Reactions Popup */}
                    {showReactions && (
                        <div className="absolute bottom-full mb-2 left-1/2 transform -translate-x-1/2 bg-[#292929] border border-[#3d3d3d] rounded-lg p-2 shadow-2xl">
                            <div className="grid grid-cols-3 gap-1">
                                {reactions.map((reaction) => (
                                    <button
                                        key={reaction.emoji}
                                        onClick={() => handleReaction(reaction.emoji)}
                                        className="p-2 hover:bg-[#3d3d3d] rounded transition-all text-2xl"
                                        title={reaction.label}
                                    >
                                        {reaction.emoji}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}
                </div>

                {/* Chat Button */}
                <button
                    onClick={onToggleChat}
                    className={`group relative flex flex-col items-center gap-1 px-4 py-2 rounded-md transition-all ${showChat
                        ? 'bg-[#5b5fc7] hover:bg-[#4d52b8]'
                        : 'bg-[#3d3d3d] hover:bg-[#4d4d4d]'
                        }`}
                >
                    <MessageSquare className="w-5 h-5 text-white" />
                    <span className="text-xs text-white">Chat</span>
                </button>

                {/* Participants Button */}
                <button
                    onClick={onToggleParticipants}
                    className={`group relative flex flex-col items-center gap-1 px-4 py-2 rounded-md transition-all ${showParticipants
                        ? 'bg-[#5b5fc7] hover:bg-[#4d52b8]'
                        : 'bg-[#3d3d3d] hover:bg-[#4d4d4d]'
                        }`}
                >
                    <Users className="w-5 h-5 text-white" />
                    <span className="text-xs text-white">People</span>
                </button>

                {/* More Options */}
                <button className="group relative flex flex-col items-center gap-1 px-4 py-2 rounded-md bg-[#3d3d3d] hover:bg-[#4d4d4d] transition-all">
                    <MoreHorizontal className="w-5 h-5 text-white" />
                    <span className="text-xs text-white">More</span>
                </button>

                {/* Leave Button */}
                <button
                    onClick={onLeave}
                    className="group relative flex flex-col items-center gap-1 px-6 py-2 rounded-md bg-[#c4314b] hover:bg-[#a92b40] transition-all ml-4"
                >
                    <PhoneOff className="w-5 h-5 text-white" />
                    <span className="text-xs text-white font-semibold">Leave</span>
                </button>
            </div>
        </div>
    );
}

export default ControlBar;