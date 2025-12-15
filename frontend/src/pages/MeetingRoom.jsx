// MeetingRoom.jsx
import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useWebSocket } from '../hooks/useWebSocket';
import { useWebRTC } from '../hooks/useWebRTC';
import VideoGrid from '../components/VideoGrid';
import ControlBar from '../components/ControlBar';
import ChatSidebar from '../components/ChatSidebar';
import PreJoinScreen from '../components/PreJoinScreen';
import { Users, Copy, Check, Grid3x3, LayoutGrid, MoreHorizontal, Volume2, VolumeX } from 'lucide-react';

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
    const [viewMode, setViewMode] = useState('grid');
    const [chatMessages, setChatMessages] = useState([]);
    const [participants, setParticipants] = useState([]);
    const [copied, setCopied] = useState(false);
    const [reactions, setReactions] = useState([]);
    const [reactionPositions, setReactionPositions] = useState({});
    const [showMoreOptions, setShowMoreOptions] = useState(false);
    const [debugMode, setDebugMode] = useState(false);

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

    // Debug useEffect to track mute state
    useEffect(() => {
        console.log('🔊 DEBUG Mute State:', {
            isMuted,
            hasLocalStream: !!localStream,
            audioTracks: localStream?.getAudioTracks()?.length || 0,
            audioTrackEnabled: localStream?.getAudioTracks()[0]?.enabled,
            audioTrackRef: audioTrackRef.current?.enabled
        });
    }, [isMuted, localStream]);

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

    // Test microphone function
    const testMicrophone = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const track = stream.getAudioTracks()[0];
            console.log('🎤 Microphone test - Track enabled:', track.enabled);
            
            // Play a test sound
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.value = 440;
            oscillator.type = 'sine';
            gainNode.gain.value = 0.1;
            
            oscillator.start();
            setTimeout(() => {
                oscillator.stop();
                audioContext.close();
            }, 500);
            
            stream.getTracks().forEach(t => t.stop());
            
            alert('Microphone test complete! Check console for details.');
            
        } catch (error) {
            console.error('❌ Microphone test failed:', error);
            alert('Microphone access denied or failed. Check browser permissions.');
        }
    };

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

    // Reset audio function
    const resetAudio = async () => {
        if (confirm('Reset audio? This will reinitialize your microphone.')) {
            try {
                // Stop current audio
                if (localStream) {
                    const audioTracks = localStream.getAudioTracks();
                    audioTracks.forEach(track => track.stop());
                }
                
                // Get new audio
                const audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
                const newAudioTrack = audioStream.getAudioTracks()[0];
                
                // Get current video if any
                const videoTracks = localStream ? localStream.getVideoTracks() : [];
                
                // Create new stream
                const newStream = new MediaStream();
                newStream.addTrack(newAudioTrack);
                videoTracks.forEach(track => newStream.addTrack(track));
                
                // Update ref and state
                audioTrackRef.current = newAudioTrack;
                setLocalStream(newStream);
                setIsMuted(false);
                
                console.log('🔄 Audio reset complete');
                alert('Audio reset successfully!');
                
            } catch (error) {
                console.error('❌ Audio reset failed:', error);
                alert('Failed to reset audio. Check microphone permissions.');
            }
        }
    };

    if (!hasJoined) {
        return <PreJoinScreen meetingId={meetingId} onJoin={handlePreJoin} />;
    }

    return (
        <div className="h-screen bg-[#1f1f1f] flex flex-col relative overflow-hidden">
            {/* Header */}
            <div className="bg-[#292929] border-b border-[#3d3d3d] px-4 py-2 flex items-center justify-between">
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

                <div className="flex items-center gap-2">
                    {/* Debug buttons - only show in debug mode */}
                    <button
                        onClick={() => setDebugMode(!debugMode)}
                        className="px-2 py-1 text-xs bg-gray-700 text-white rounded"
                    >
                        {debugMode ? 'Hide Debug' : 'Debug'}
                    </button>
                    
                    {debugMode && (
                        <>
                            <button
                                onClick={testMicrophone}
                                className="px-3 py-1.5 bg-blue-500 hover:bg-blue-600 rounded-md transition-all text-white text-sm flex items-center gap-2"
                            >
                                <Volume2 className="w-4 h-4" />
                                Test Mic
                            </button>
                            
                            <button
                                onClick={resetAudio}
                                className="px-3 py-1.5 bg-orange-500 hover:bg-orange-600 rounded-md transition-all text-white text-sm"
                            >
                                Reset Audio
                            </button>
                            
                            <button
                                onClick={() => console.log('Audio track ref:', audioTrackRef.current)}
                                className="px-3 py-1.5 bg-purple-500 hover:bg-purple-600 rounded-md transition-all text-white text-sm"
                            >
                                Log Audio
                            </button>
                        </>
                    )}

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
                                    <div className="flex items-center gap-2 mt-1">
                                        {isVideoOff && (
                                            <span className="text-xs text-gray-400 bg-black/30 px-1.5 py-0.5 rounded">Camera off</span>
                                        )}
                                        {isMuted ? (
                                            <span className="text-xs text-red-400 bg-black/30 px-1.5 py-0.5 rounded">
                                                <VolumeX className="w-3 h-3 inline mr-1" />
                                                Muted
                                            </span>
                                        ) : (
                                            <span className="text-xs text-green-400 bg-black/30 px-1.5 py-0.5 rounded">
                                                <Volume2 className="w-3 h-3 inline mr-1" />
                                                Unmuted
                                            </span>
                                        )}
                                    </div>
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