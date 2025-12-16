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
        <div className="fixed bottom-6 left-1/2 transform -translate-x-1/2 z-30 md:hidden">
            <div className="floating-control-bar glass flex items-center justify-center gap-3 px-4 py-3 rounded-full shadow-lg">
                {/* Mute Button */}
                <button
                    onClick={onToggleMute}
                    className={`control-btn ${isMuted ? 'control-btn--toggled' : ''}`}
                    aria-pressed={isMuted}
                    aria-label={isMuted ? 'Unmute' : 'Mute'}
                    title={isMuted ? 'Unmute' : 'Mute'}
                >
                    {isMuted ? <MicOff className="control-btn-icon" /> : <Mic className="control-btn-icon" />}
                    <span className="control-tooltip">{isMuted ? 'Unmute' : 'Mute'}</span>
                </button>

                {/* Video Button */}
                <button
                    onClick={onToggleVideo}
                    className={`control-btn ${isVideoOff ? 'control-btn--toggled' : ''}`}
                    aria-pressed={isVideoOff}
                    aria-label={isVideoOff ? 'Turn camera on' : 'Turn camera off'}
                    title={isVideoOff ? 'Turn camera on' : 'Turn camera off'}
                >
                    {isVideoOff ? <VideoOff className="control-btn-icon" /> : <Video className="control-btn-icon" />}
                    <span className="control-tooltip">{isVideoOff ? 'Camera Off' : 'Camera On'}</span>
                </button>

                {/* Screen Share Button */}
                <button
                    onClick={onToggleScreenShare}
                    className={`control-btn ${isScreenSharing ? 'control-btn--toggled' : ''}`}
                    aria-pressed={isScreenSharing}
                    aria-label={isScreenSharing ? 'Stop sharing' : 'Share screen'}
                    title={isScreenSharing ? 'Stop sharing' : 'Share screen'}
                >
                    {isScreenSharing ? <MonitorOff className="control-btn-icon" /> : <Monitor className="control-btn-icon" />}
                    <span className="control-tooltip">{isScreenSharing ? 'Stop' : 'Share'}</span>
                </button>

                {/* Reactions Button */}
                <div className="relative">
                    <button
                        onClick={() => setShowReactions(!showReactions)}
                        className={`control-btn ${showReactions ? 'control-btn--toggled' : ''}`}
                        aria-pressed={showReactions}
                        aria-label="Reactions"
                        title="Reactions"
                    >
                        <Smile className="control-btn-icon" />
                        <span className="control-tooltip">React</span>
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
                    className={`control-btn ${showChat ? 'control-btn--toggled' : ''}`}
                    aria-pressed={showChat}
                    aria-label="Toggle chat"
                    title="Chat"
                >
                    <MessageSquare className="control-btn-icon" />
                    <span className="control-tooltip">Chat</span>
                </button>

                {/* Participants Button */}
                <button
                    onClick={onToggleParticipants}
                    className={`control-btn ${showParticipants ? 'control-btn--toggled' : ''}`}
                    aria-pressed={showParticipants}
                    aria-label="Toggle participants"
                    title="Participants"
                >
                    <Users className="control-btn-icon" />
                    <span className="control-tooltip">People</span>
                </button>

                {/* More Options - You might want to remove this if it doesn't have functionality */}
                {/* <button className="control-btn bg-[#2f2f2f] hover:bg-[#3f3f3f]" aria-label="More options" title="More">
                    <MoreHorizontal className="control-btn-icon" />
                    <span className="control-tooltip">More</span>
                </button> */}

                {/* Leave Button */}
                <button
                    onClick={onLeave}
                    className="control-btn control-btn--danger ml-4"
                    aria-label="Leave meeting"
                    title="Leave"
                >
                    <PhoneOff className="control-btn-icon" />
                    <span className="ml-2 font-semibold">Leave</span>
                </button>
            </div>
        </div>
    );
}

export default ControlBar;