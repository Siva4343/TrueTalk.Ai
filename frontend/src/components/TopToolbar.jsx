import { Mic, MicOff, Video, VideoOff, Monitor, Users, MessageSquare, PhoneOff, MoreHorizontal, Smile, Grid, User } from 'lucide-react';

export default function TopToolbar({
    title = 'TrueTalk Meeting',
    isMuted,
    isVideoOff,
    isScreenSharing,
    onToggleMute,
    onToggleVideo,
    onToggleScreenShare,
    onToggleChat,
    onToggleParticipants,
    onToggleViewMode,
    onLeave,
    onSendReaction,
    showChat,
    showParticipants,
    viewMode = 'grid',
    participants = [],
    userName = ''
}) {
    return (
        <div className="top-toolbar-bar w-full hidden md:flex items-center px-4">
            <div className="flex items-center gap-3">
                <div className="text-white text-lg font-semibold mr-4">{title}</div>
                
                {/* View Mode Toggle - New button */}
                {onToggleViewMode && (
                    <button
                        onClick={onToggleViewMode}
                        className="px-4 py-2 bg-[#363636] hover:bg-[#464646] rounded-lg transition-all text-white text-sm font-medium flex items-center gap-2"
                        title={`Switch to ${viewMode === 'grid' ? 'Speaker' : 'Grid'} view`}
                    >
                        {viewMode === 'grid' ? (
                            <>
                                <User className="w-4 h-4" />
                                <span>Speaker View</span>
                            </>
                        ) : (
                            <>
                                <Grid className="w-4 h-4" />
                                <span>Grid View</span>
                            </>
                        )}
                    </button>
                )}
            </div>

            <div className="flex-1" />

            <div className="flex items-center gap-3">
                {/* Participant count display - New element */}
                {participants.length > 0 && (
                    <button
                        onClick={onToggleParticipants}
                        className="px-4 py-2 bg-[#363636] hover:bg-[#464646] rounded-lg transition-all text-white text-sm font-medium flex items-center gap-2"
                        title="Participants"
                    >
                        <div className="flex -space-x-2">
                            <div className="w-8 h-8 rounded-full bg-[#5b5fc7] flex items-center justify-center text-white text-xs font-semibold shadow">
                                {userName.charAt(0).toUpperCase()}
                            </div>
                            {participants.slice(0,2).map((p) => (
                                <div key={p.id} className="w-8 h-8 rounded-full bg-[#6264a7] flex items-center justify-center text-white text-xs font-semibold shadow">
                                    {p.name.charAt(0).toUpperCase()}
                                </div>
                            ))}
                        </div>
                        <span className="ml-1">{participants.length + 1}</span>
                    </button>
                )}

                <div className="top-toolbar control-group" role="toolbar" aria-label="Meeting controls">
                    <button
                        onClick={onToggleMute}
                        className={`control-btn ${isMuted ? 'control-btn--toggled' : ''}`}
                        aria-pressed={isMuted}
                        aria-label={isMuted ? 'Unmute' : 'Mute'}
                        title={isMuted ? 'Unmute' : 'Mute'}
                    >
                        {isMuted ? <MicOff className="control-btn-icon" /> : <Mic className="control-btn-icon" />}
                    </button>

                    <button
                        onClick={onToggleVideo}
                        className={`control-btn ${isVideoOff ? 'control-btn--toggled' : ''}`}
                        aria-pressed={isVideoOff}
                        aria-label={isVideoOff ? 'Turn camera on' : 'Turn camera off'}
                        title={isVideoOff ? 'Turn camera on' : 'Turn camera off'}
                    >
                        {isVideoOff ? <VideoOff className="control-btn-icon" /> : <Video className="control-btn-icon" />}
                    </button>

                    <button
                        onClick={onToggleScreenShare}
                        className={`control-btn ${isScreenSharing ? 'control-btn--toggled' : ''}`}
                        aria-pressed={isScreenSharing}
                        aria-label={isScreenSharing ? 'Stop sharing' : 'Share screen'}
                        title={isScreenSharing ? 'Stop sharing' : 'Share screen'}
                    >
                        <Monitor className="control-btn-icon" />
                    </button>

                    <button
                        onClick={onToggleChat}
                        className={`control-btn ${showChat ? 'control-btn--toggled' : ''}`}
                        aria-pressed={showChat}
                        aria-label="Toggle chat"
                        title="Chat"
                    >
                        <MessageSquare className="control-btn-icon" />
                    </button>

                    <button
                        onClick={() => onSendReaction && onSendReaction('👍')}
                        className="control-btn"
                        aria-label="Send reaction"
                        title="React"
                    >
                        <Smile className="control-btn-icon" />
                    </button>

                    <button
                        onClick={onToggleParticipants}
                        className={`control-btn ${showParticipants ? 'control-btn--toggled' : ''}`}
                        aria-pressed={showParticipants}
                        aria-label="Toggle participants"
                        title="Participants"
                    >
                        <Users className="control-btn-icon" />
                    </button>

                    <button
                        onClick={onLeave}
                        className="control-btn control-btn--danger ml-2"
                        aria-label="Leave meeting"
                        title="Leave"
                    >
                        <PhoneOff className="control-btn-icon" />
                        <span className="ml-2 font-semibold hidden lg:inline">Leave</span>
                    </button>
                </div>
            </div>
        </div>
    );
}