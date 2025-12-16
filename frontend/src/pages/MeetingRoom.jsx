// MeetingRoom.jsx
import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useWebSocket } from '../hooks/useWebSocket';
import { useWebRTC } from '../hooks/useWebRTC';
import VideoGrid from '../components/VideoGrid';
import ChatSidebar from '../components/ChatSidebar';
import PreJoinScreen from '../components/PreJoinScreen';
import ParticipantsSidebar from '../components/participantsSidebar';
import ControlBar from '../components/ControlBar';
import { Users, Copy, Check, Grid3x3, LayoutGrid, MoreHorizontal, MoreVertical, Volume2, VolumeX } from 'lucide-react';
import TopToolbar from '../components/TopToolbar';
import { meetingAPI } from '../services/api';

// Simple counter for user IDs (defined outside component to persist)
let userIdCounter = 0;

// Generate a simple user ID without impure functions
const generateUserId = () => {
    return `user_${++userIdCounter}`;
};

export default function MeetingRoom() {
    const { meetingId } = useParams();
    const navigate = useNavigate();
    
    const [userId] = useState(() => generateUserId());
    const [userName, setUserName] = useState('');
    const [hasJoined, setHasJoined] = useState(false);
    const [localStream, setLocalStream] = useState(null);
    const [isMuted, setIsMuted] = useState(false);
    const [isVideoOff, setIsVideoOff] = useState(true);
    const [isScreenSharing, setIsScreenSharing] = useState(false);
    const [screenStream, setScreenStream] = useState(null);
    const [showChat, setShowChat] = useState(false);
    const [showParticipants, setShowParticipants] = useState(false);
    const [viewMode, _setViewMode] = useState('grid');
    const [chatMessages, setChatMessages] = useState([]);
    const [participants, setParticipants] = useState([]);
    const [copied, setCopied] = useState(false);
    const [reactions, setReactions] = useState([]);
    const [reactionPositions, setReactionPositions] = useState({});
    const [showMoreOptions, setShowMoreOptions] = useState(false);

    const moreOptionsRef = useRef(null);
    const audioTrackRef = useRef(null);

    const { isConnected, sendMessage, on } = useWebSocket(meetingId, userId, userName);
    const { remoteStreams, handleUserJoined, handleOffer, handleAnswer, handleICECandidate } =
        useWebRTC(localStream, sendMessage, userId);

    const showReaction = useCallback((emoji, fromUserId) => {
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

    // (Debug logs removed in production UI)
    // Store audio track reference when localStream changes
    useEffect(() => {
        if (localStream) {
            const audioTracks = localStream.getAudioTracks();
            if (audioTracks.length > 0) {
                audioTrackRef.current = audioTracks[0];
                console.log('🎵 Audio track stored in ref:', audioTrackRef.current?.enabled);
            }
        }
    }, [localStream]);

    // Close more options when clicking outside
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (moreOptionsRef.current && !moreOptionsRef.current.contains(event.target)) {
                setShowMoreOptions(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, []);

    useEffect(() => {
        if (!isConnected || !hasJoined) return;

        on('user_joined', (data) => {
            handleUserJoined(data);
            setParticipants(prev => {
                if (prev.find(p => p.id === data.userId)) return prev;
                return [...prev, { id: data.userId, name: data.user, isMuted: data.isMuted ?? false }];
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

    // Clean up streams on unmount
    useEffect(() => {
        return () => {
            if (localStream) {
                localStream.getTracks().forEach(track => track.stop());
            }
            if (screenStream) {
                screenStream.getTracks().forEach(track => track.stop());
            }
        };
    }, [localStream, screenStream]);

    const handlePreJoin = (name, stream) => {
        setUserName(name);
        setLocalStream(stream);
        setHasJoined(true);
        
        // Store audio track reference
        const audioTracks = stream.getAudioTracks();
        if (audioTracks.length > 0) {
            audioTrackRef.current = audioTracks[0];
            setIsMuted(!audioTracks[0].enabled);
            console.log('✅ PreJoin - Audio track initialized, enabled:', audioTracks[0].enabled);
        }
    };

    // FIXED MUTE FUNCTION - Uses audioTrackRef for reliability
    const toggleMute = () => {
        console.log('🔄 toggleMute called');
        
        // Try to use audioTrackRef first (most reliable)
        if (audioTrackRef.current) {
            const currentEnabled = audioTrackRef.current.enabled;
            const newEnabledState = !currentEnabled;
            
            audioTrackRef.current.enabled = newEnabledState;
            setIsMuted(!newEnabledState);
            
            console.log(`🎤 Audio ${newEnabledState ? 'UNMUTED' : 'MUTED'} via audioTrackRef`);
            
            // Send mute status to other participants
            sendMessage('user_mute_toggle', {
                userId,
                userName,
                isMuted: !newEnabledState
            });
            
        } else if (localStream) {
            // Fallback to localStream
            const audioTracks = localStream.getAudioTracks();
            if (audioTracks.length > 0) {
                const audioTrack = audioTracks[0];
                const currentEnabled = audioTrack.enabled;
                const newEnabledState = !currentEnabled;
                
                audioTrack.enabled = newEnabledState;
                setIsMuted(!newEnabledState);
                audioTrackRef.current = audioTrack;
                
                console.log(`🎤 Audio ${newEnabledState ? 'UNMUTED' : 'MUTED'} via localStream`);
                
                sendMessage('user_mute_toggle', {
                    userId,
                    userName,
                    isMuted: !newEnabledState
                });
            } else {
                console.warn('⚠️ No audio tracks found');
                setIsMuted(!isMuted); // UI fallback
            }
        } else {
            console.warn('⚠️ No audio available');
            setIsMuted(!isMuted); // UI fallback
        }
    };

    // SIMPLIFIED VIDEO TOGGLE - Preserves audio track properly
    const toggleVideo = async () => {
        try {
            if (isVideoOff) {
                // Turn camera ON
                console.log('📹 Turning camera ON...');
                
                // Get current audio tracks (preserve them)
                const currentAudioTracks = localStream ? localStream.getAudioTracks() : [];
                
                // Create video stream
                const videoConstraints = {
                    video: {
                        width: { ideal: 1280 },
                        height: { ideal: 720 },
                        frameRate: { ideal: 30 }
                    },
                    audio: false // We'll add our existing audio
                };
                
                const videoStream = await navigator.mediaDevices.getUserMedia(videoConstraints);
                const videoTrack = videoStream.getVideoTracks()[0];
                
                // Create new stream with existing audio + new video
                const newStream = new MediaStream();
                
                // Add existing audio tracks
                currentAudioTracks.forEach(track => {
                    newStream.addTrack(track);
                    console.log('🎵 Preserved audio track:', track.enabled);
                });
                
                // Add new video track
                newStream.addTrack(videoTrack);
                
                // Stop temporary video stream tracks
                videoStream.getTracks().forEach(track => {
                    if (track !== videoTrack) track.stop();
                });
                
                // Update state
                setLocalStream(newStream);
                setIsVideoOff(false);
                
                console.log('✅ Camera ON, audio preserved');
                
            } else {
                // Turn camera OFF
                console.log('📹 Turning camera OFF...');
                
                if (localStream) {
                    // Stop video tracks
                    const videoTracks = localStream.getVideoTracks();
                    videoTracks.forEach(track => {
                        track.stop();
                        console.log('📹 Stopped video track');
                    });
                    
                    // Create new stream with only audio
                    const audioTracks = localStream.getAudioTracks();
                    const newStream = new MediaStream();
                    
                    audioTracks.forEach(track => {
                        newStream.addTrack(track);
                        console.log('🎵 Preserved audio track:', track.enabled);
                    });
                    
                    // Update state
                    setLocalStream(newStream);
                    setIsVideoOff(true);
                    
                    console.log('✅ Camera OFF, audio preserved');
                }
            }
            
            // Notify other participants
            sendMessage('user_video_toggle', {
                userId,
                userName,
                hasVideo: !isVideoOff
            });
            
        } catch (error) {
            console.error('❌ Error toggling video:', error);
            alert('Could not access camera. Please check permissions and try again.');
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

    /* Microphone test helper removed (debug-only) */

    const handleLeave = () => {
        if (confirm('Are you sure you want to leave?')) {
            if (localStream) {
                localStream.getTracks().forEach(track => track.stop());
            }
            if (screenStream) {
                screenStream.getTracks().forEach(track => track.stop());
            }
            sendMessage('user_leave', { userId, user: userName });
            navigate('/');
        }
    };

    // More options functions
    const openMeetingSettings = () => {
        alert('Meeting settings would open here');
        setShowMoreOptions(false);
    };

    const toggleFullscreen = () => {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen();
        } else {
            if (document.exitFullscreen) {
                document.exitFullscreen();
            }
        }
        setShowMoreOptions(false);
    };

    const openHelp = () => {
        alert('Help documentation would open here');
        setShowMoreOptions(false);
    };

    const reportIssue = () => {
        alert('Report issue modal would open here');
        setShowMoreOptions(false);
    };

    // Force mute function
    const forceMute = (mute) => {
        if (audioTrackRef.current) {
            audioTrackRef.current.enabled = !mute;
            setIsMuted(mute);
            console.log(`🔇 Audio ${mute ? 'FORCE MUTED' : 'FORCE UNMUTED'}`);
        } else if (localStream) {
            const audioTracks = localStream.getAudioTracks();
            if (audioTracks.length > 0) {
                audioTracks[0].enabled = !mute;
                setIsMuted(mute);
            }
        }
    };

    /* Audio reset helper removed (debug-only) */

    // Participant moderation handlers
    const handleMuteParticipant = async (participantId) => {
        try {
            await meetingAPI.muteParticipant(meetingId, participantId);
            setParticipants(prev => prev.map(p => p.id === participantId ? { ...p, isMuted: true } : p));
            // Notify other participants via websocket
            sendMessage('participant_muted', { participantId });
        } catch (err) {
            console.error('Mute failed:', err);
            alert('Could not mute participant');
        }
    };

    const handleRemoveParticipant = async (participantId) => {
        try {
            await meetingAPI.removeParticipant(meetingId, participantId);
            setParticipants(prev => prev.filter(p => p.id !== participantId));
            sendMessage('participant_removed', { participantId });
        } catch (err) {
            console.error('Remove failed:', err);
            alert('Could not remove participant');
        }
    };

    const handleMakeCohost = async (participantId) => {
        try {
            await meetingAPI.makeCohost(meetingId, participantId);
            setParticipants(prev => prev.map(p => p.id === participantId ? { ...p, role: 'co_host' } : p));
            alert('Participant promoted to co-host');
        } catch (err) {
            console.error('Make cohost failed:', err);
            alert('Could not promote participant');
        }
    };

    if (!hasJoined) {
        return <PreJoinScreen meetingId={meetingId} onJoin={handlePreJoin} />;
    }

    return (
        <div className="h-screen bg-[#1f1f1f] flex flex-col relative overflow-hidden">
            {/* Header */}
            <div className="meeting-header px-4 py-2 flex items-center justify-between">
                {/* Header: use TopToolbar for title and controls (keeps UI minimal like Teams) */}
                <div className="flex items-center gap-3">
                    {/* Meeting title & status moved to TopToolbar to avoid duplication */}
                </div>

                <div className="flex items-center gap-2">
                    {/* Debug buttons - only show in debug mode */}
                    {/* Top toolbar (visible on md+) - simplified */}
                    <TopToolbar
                        title={meetingId || 'TrueTalk Meeting'}
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

                    {/* (Removed Debug and View Mode buttons for cleaner header) */}

                    {/* Participant count */}
                    <button
                        onClick={() => setShowParticipants(!showParticipants)}
                        className="flex items-center gap-2 px-3 py-1.5 bg-[#3d3d3d] hover:bg-[#4d4d4d] rounded-md transition-all text-white text-sm"
                        title="Participants"
                    >
                        <div className="flex -space-x-2">
                            <div className="w-6 h-6 rounded-full bg-[#5b5fc7] flex items-center justify-center text-white text-xs font-semibold">{userName.charAt(0).toUpperCase()}</div>
                            {participants.slice(0,2).map((p)=> (
                                <div key={p.id} className="w-6 h-6 rounded-full bg-[#6264a7] flex items-center justify-center text-white text-xs font-semibold">{p.name.charAt(0).toUpperCase()}</div>
                            ))}
                        </div>
                        <span className="ml-2">{remoteStreams.size + 1}</span>
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
                    <div className="relative" ref={moreOptionsRef}>
                        <button 
                            onClick={() => setShowMoreOptions(!showMoreOptions)}
                            className="p-1.5 bg-[#3d3d3d] hover:bg-[#4d4d4d] rounded-md transition-all text-white"
                        >
                            <MoreHorizontal className="w-4 h-4" />
                        </button>
                        
                        {/* More options dropdown */}
                        {showMoreOptions && (
                            <div className="absolute right-0 top-full mt-1 w-48 bg-[#3d3d3d] rounded-md shadow-lg z-50 py-1 border border-[#4d4d4d]">
                                <button
                                    onClick={toggleFullscreen}
                                    className="w-full px-4 py-2 text-left text-white hover:bg-[#4d4d4d] text-sm"
                                >
                                    Toggle Fullscreen
                                </button>
                                <button
                                    onClick={() => forceMute(true)}
                                    className="w-full px-4 py-2 text-left text-white hover:bg-[#4d4d4d] text-sm"
                                >
                                    Force Mute All
                                </button>
                                <button
                                    onClick={openMeetingSettings}
                                    className="w-full px-4 py-2 text-left text-white hover:bg-[#4d4d4d] text-sm"
                                >
                                    Meeting Settings
                                </button>
                                <button
                                    onClick={openHelp}
                                    className="w-full px-4 py-2 text-left text-white hover:bg-[#4d4d4d] text-sm"
                                >
                                    Help
                                </button>
                                <button
                                    onClick={reportIssue}
                                    className="w-full px-4 py-2 text-left text-white hover:bg-[#4d4d4d] text-sm"
                                >
                                    Report Issue
                                </button>
                            </div>
                        )}
                    </div>
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
                    <ParticipantsSidebar
                        participants={participants}
                        currentUser={{ id: userId, name: userName }}
                        onClose={() => setShowParticipants(false)}
                        onPinParticipant={(id) => console.log('Pin', id)}
                        pinnedParticipant={null}
                        onMuteParticipant={handleMuteParticipant}
                        onRemoveParticipant={handleRemoveParticipant}
                        onMakeCohost={handleMakeCohost}
                    />
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

            {/* Mobile Floating Control Bar (visible only on small screens) */}
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