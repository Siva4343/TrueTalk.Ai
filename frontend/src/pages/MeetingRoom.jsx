import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useWebSocket } from '../hooks/useWebSocket';
import { useWebRTC } from '../hooks/useWebRTC';
import VideoGrid from '../components/VideoGrid';
import ControlBar from '../components/ControlBar';
import ChatSidebar from '../components/ChatSidebar';
import PreJoinScreen from '../components/PreJoinScreen';
import { Users, Copy, Check, Grid3x3, LayoutGrid, MoreHorizontal } from 'lucide-react';

// Simple counter for user IDs (defined outside component to persist)
let userIdCounter = 0;

// Generate a simple user ID without impure functions
const generateUserId = () => {
    return `user_${++userIdCounter}`;
};

export default function MeetingRoom() {
    const { meetingId } = useParams();
    const navigate = useNavigate();
    
    // Use useState with lazy initializer to avoid impure render
    const [userId] = useState(() => generateUserId());
    
    const [userName, setUserName] = useState('');
    const [hasJoined, setHasJoined] = useState(false);
    const [localStream, setLocalStream] = useState(null);
    const [isMuted, setIsMuted] = useState(false);
    const [isVideoOff, setIsVideoOff] = useState(false);
    const [isScreenSharing, setIsScreenSharing] = useState(false);
    const [screenStream, setScreenStream] = useState(null);
    const [showChat, setShowChat] = useState(false);
    const [showParticipants, setShowParticipants] = useState(false);
    const [viewMode, setViewMode] = useState('grid');
    const [chatMessages, setChatMessages] = useState([]);
    const [participants, setParticipants] = useState([]);
    const [copied, setCopied] = useState(false);
    const [reactions, setReactions] = useState([]);
    const [reactionPositions, setReactionPositions] = useState({});

    const { isConnected, sendMessage, on } = useWebSocket(meetingId, userId, userName);
    const { remoteStreams, handleUserJoined, handleOffer, handleAnswer, handleICECandidate } =
        useWebRTC(localStream, sendMessage, userId);

    const showReaction = useCallback((emoji, fromUserId) => {
        // Use performance.now() which is allowed in callbacks
        const id = performance.now();
        const position = Math.random() * 80 + 10;
        
        setReactions(prev => [...prev, { id, emoji, userId: fromUserId }]);
        setReactionPositions(prev => ({ ...prev, [id]: position }));
        
        setTimeout(() => {
            setReactions(prev => prev.filter(r => r.id !== id));
            setReactionPositions(prev => {
                const newPositions = { ...prev };
                delete newPositions[id];
                return newPositions;
            });
        }, 3000);
    }, []);

    useEffect(() => {
        if (!isConnected || !hasJoined) return;

        on('user_joined', (data) => {
            handleUserJoined(data);
            setParticipants(prev => {
                if (prev.find(p => p.id === data.userId)) return prev;
                return [...prev, { id: data.userId, name: data.user }];
            });
        });

        on('user_left', (data) => {
            setParticipants(prev => prev.filter(p => p.id !== data.userId));
        });

        on('offer', handleOffer);
        on('answer', handleAnswer);
        on('ice-candidate', handleICECandidate);

        on('chat_message_received', (data) => {
            setChatMessages(prev => [...prev, data]);
        });

        on('reaction', (data) => {
            showReaction(data.emoji, data.userId);
        });
    }, [isConnected, hasJoined, on, handleUserJoined, handleOffer, handleAnswer, handleICECandidate, showReaction]);

    const handlePreJoin = (name, stream, muted, videoOff) => {
        setUserName(name);
        setLocalStream(stream);
        setIsMuted(muted);
        setIsVideoOff(videoOff);
        setHasJoined(true);
    };

    const toggleMute = () => {
        if (localStream) {
            localStream.getAudioTracks().forEach(track => {
                track.enabled = !track.enabled;
            });
            setIsMuted(!isMuted);
        }
    };

    const toggleVideo = () => {
        if (localStream) {
            localStream.getVideoTracks().forEach(track => {
                track.enabled = !track.enabled;
            });
            setIsVideoOff(!isVideoOff);
        }
    };

    const toggleScreenShare = async () => {
        try {
            if (!isScreenSharing) {
                const stream = await navigator.mediaDevices.getDisplayMedia({
                    video: { cursor: 'always' },
                    audio: false
                });

                setScreenStream(stream);
                setIsScreenSharing(true);

                // Handle when user stops sharing via browser UI
                stream.getVideoTracks()[0].onended = () => {
                    setIsScreenSharing(false);
                    setScreenStream(null);
                };
            } else {
                if (screenStream) {
                    screenStream.getTracks().forEach(track => track.stop());
                }
                setScreenStream(null);
                setIsScreenSharing(false);
            }
        } catch (error) {
            console.error('Error sharing screen:', error);
        }
    };

    const handleSendMessage = (message) => {
        sendMessage('chat_message', {
            content: message,
            sender: userName,
            senderId: userId,
            timestamp: new Date().toISOString(),
        });
    };

    const handleSendReaction = (emoji) => {
        sendMessage('reaction', {
            emoji,
            userId,
            user: userName,
        });
        showReaction(emoji, userId);
    };

    const copyMeetingLink = () => {
        const link = window.location.href;
        navigator.clipboard.writeText(link);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const handleLeave = () => {
        if (confirm('Are you sure you want to leave?')) {
            if (localStream) {
                localStream.getTracks().forEach(track => track.stop());
            }
            sendMessage('user_leave', { userId, user: userName });
            navigate('/');
        }
    };

    if (!hasJoined) {
        return <PreJoinScreen meetingId={meetingId} onJoin={handlePreJoin} />;
    }

    return (
        <div className="h-screen bg-[#1f1f1f] flex flex-col relative overflow-hidden">
            {/* Teams-style Header */}
            <div className="bg-[#292929] border-b border-[#3d3d3d] px-4 py-2 flex items-center justify-between">
                <div className="flex items-center gap-4">
                    {/* Meeting info */}
                    <div className="flex items-center gap-3">
                        <div className="text-white">
                            <div className="flex items-center gap-2">
                                <h1 className="text-sm font-semibold">TrueTalk Meeting</h1>
                                {isConnected ? (
                                    <div className="flex items-center gap-1 text-xs text-green-400">
                                        <div className="w-1.5 h-1.5 bg-green-400 rounded-full"></div>
                                        <span>Connected</span>
                                    </div>
                                ) : (
                                    <div className="flex items-center gap-1 text-xs text-yellow-400">
                                        <div className="w-1.5 h-1.5 bg-yellow-400 rounded-full"></div>
                                        <span>Connecting...</span>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    {/* View Mode Toggle */}
                    <div className="flex bg-[#3d3d3d] rounded-md p-1">
                        <button
                            onClick={() => setViewMode('grid')}
                            className={`p-1.5 rounded transition-all ${viewMode === 'grid'
                                ? 'bg-[#5b5fc7] text-white'
                                : 'text-gray-400 hover:text-white'
                                }`}
                            title="Grid view"
                        >
                            <Grid3x3 className="w-4 h-4" />
                        </button>
                        <button
                            onClick={() => setViewMode('gallery')}
                            className={`p-1.5 rounded transition-all ${viewMode === 'gallery'
                                ? 'bg-[#5b5fc7] text-white'
                                : 'text-gray-400 hover:text-white'
                                }`}
                            title="Gallery view"
                        >
                            <LayoutGrid className="w-4 h-4" />
                        </button>
                    </div>

                    {/* Participant count */}
                    <button
                        onClick={() => setShowParticipants(!showParticipants)}
                        className="flex items-center gap-2 px-3 py-1.5 bg-[#3d3d3d] hover:bg-[#4d4d4d] rounded-md transition-all text-white text-sm"
                    >
                        <Users className="w-4 h-4" />
                        <span>{remoteStreams.size + 1}</span>
                    </button>

                    {/* Copy link */}
                    <button
                        onClick={copyMeetingLink}
                        className="px-3 py-1.5 bg-[#3d3d3d] hover:bg-[#4d4d4d] rounded-md transition-all text-white text-sm flex items-center gap-2"
                    >
                        {copied ? (
                            <>
                                <Check className="w-4 h-4 text-green-400" />
                                <span>Copied</span>
                            </>
                        ) : (
                            <>
                                <Copy className="w-4 h-4" />
                                <span>Copy link</span>
                            </>
                        )}
                    </button>

                    {/* More options */}
                    <button className="p-1.5 bg-[#3d3d3d] hover:bg-[#4d4d4d] rounded-md transition-all text-white">
                        <MoreHorizontal className="w-4 h-4" />
                    </button>
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 flex overflow-hidden bg-[#1f1f1f]">
                <div className="flex-1 p-2">
                    <VideoGrid
                        localStream={localStream}
                        remoteStreams={remoteStreams}
                        isVideoOff={isVideoOff}
                        isMuted={isMuted}
                        userName={userName}
                        viewMode={viewMode}
                    />
                </div>

                {/* Chat Sidebar */}
                {showChat && (
                    <ChatSidebar
                        messages={chatMessages}
                        onSendMessage={handleSendMessage}
                        onClose={() => setShowChat(false)}
                        currentUserId={userId}
                        userName={userName}
                    />
                )}

                {/* Participants Panel */}
                {showParticipants && (
                    <div className="w-80 bg-[#292929] border-l border-[#3d3d3d] flex flex-col">
                        <div className="p-4 border-b border-[#3d3d3d]">
                            <h2 className="font-semibold text-white text-sm">Participants ({participants.length + 1})</h2>
                        </div>
                        <div className="flex-1 overflow-y-auto p-3 space-y-1">
                            <div className="flex items-center gap-3 p-2 hover:bg-[#3d3d3d] rounded transition-all">
                                <div className="w-8 h-8 bg-[#5b5fc7] rounded-full flex items-center justify-center">
                                    <span className="text-white text-sm font-semibold">{userName.charAt(0).toUpperCase()}</span>
                                </div>
                                <div className="flex-1">
                                    <p className="text-white text-sm">{userName} (You)</p>
                                </div>
                            </div>
                            {participants.map((participant) => (
                                <div key={participant.id} className="flex items-center gap-3 p-2 hover:bg-[#3d3d3d] rounded transition-all">
                                    <div className="w-8 h-8 bg-[#6264a7] rounded-full flex items-center justify-center">
                                        <span className="text-white text-sm font-semibold">{participant.name.charAt(0).toUpperCase()}</span>
                                    </div>
                                    <div className="flex-1">
                                        <p className="text-white text-sm">{participant.name}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            {/* Floating Reactions */}
            <div className="absolute inset-0 pointer-events-none z-20">
                {reactions.map((reaction) => (
                    <div
                        key={reaction.id}
                        className="absolute bottom-32 text-6xl animate-float-up"
                        style={{
                            left: `${reactionPositions[reaction.id] || 50}%`,
                        }}
                    >
                        {reaction.emoji}
                    </div>
                ))}
            </div>

            {/* Control Bar */}
            <div className="relative z-10">
                <ControlBar
                    isMuted={isMuted}
                    isVideoOff={isVideoOff}
                    isScreenSharing={isScreenSharing}
                    onToggleMute={toggleMute}
                    onToggleVideo={toggleVideo}
                    onToggleScreenShare={toggleScreenShare}
                    onToggleChat={() => setShowChat(!showChat)}
                    onToggleParticipants={() => setShowParticipants(!showParticipants)}
                    onLeave={handleLeave}
                    onSendReaction={handleSendReaction}
                    showChat={showChat}
                    showParticipants={showParticipants}
                />
            </div>
        </div>
    );
}