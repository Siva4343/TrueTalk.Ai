// PreJoinScreen.jsx
import { useState, useRef, useEffect } from 'react';
import { Camera, CameraOff, Mic, MicOff, User, AlertCircle } from 'lucide-react';

export default function PreJoinScreen({ meetingId, onJoin, initialVideoOff = false }) {
    const [userName, setUserName] = useState('');
    const [isMuted, setIsMuted] = useState(false);
    const [isVideoOff, setIsVideoOff] = useState(initialVideoOff);
    const [localStream, setLocalStream] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [showSettings, setShowSettings] = useState(false);
    const [availableDevices, setAvailableDevices] = useState({
        audio: [],
        video: []
    });
    
    const videoRef = useRef(null);

    // Get available devices
    useEffect(() => {
        const getDevices = async () => {
            try {
                const devices = await navigator.mediaDevices.enumerateDevices();
                const audioInputs = devices.filter(device => device.kind === 'audioinput');
                const videoInputs = devices.filter(device => device.kind === 'videoinput');
                
                setAvailableDevices({
                    audio: audioInputs,
                    video: videoInputs
                });
            } catch (err) {
                console.error('Error getting devices:', err);
            }
        };
        
        getDevices();
    }, []);

    // Initialize camera preview
    useEffect(() => {
        const initCameraPreview = async () => {
            if (!isVideoOff) {
                try {
                    setIsLoading(true);
                    setError('');
                    
                    const constraints = {
                        audio: true,
                        video: {
                            width: { ideal: 640 },
                            height: { ideal: 480 },
                            facingMode: 'user'
                        }
                    };

                    const stream = await navigator.mediaDevices.getUserMedia(constraints);
                    setLocalStream(stream);
                    
                    if (videoRef.current) {
                        videoRef.current.srcObject = stream;
                    }
                    
                } catch (err) {
                    console.error('Error accessing media devices:', err);
                    if (err.name === 'NotAllowedError') {
                        setError('Camera/microphone access denied. Please allow permissions.');
                    } else if (err.name === 'NotFoundError') {
                        setError('No camera/microphone found.');
                    } else {
                        setError('Could not access camera/microphone.');
                    }
                    setIsVideoOff(true);
                } finally {
                    setIsLoading(false);
                }
            } else if (localStream) {
                // Stop stream if turning video off
                localStream.getTracks().forEach(track => track.stop());
                setLocalStream(null);
                if (videoRef.current) {
                    videoRef.current.srcObject = null;
                }
            }
        };

        initCameraPreview();
    }, [isVideoOff]);

    // Clean up on unmount
    useEffect(() => {
        return () => {
            if (localStream) {
                localStream.getTracks().forEach(track => track.stop());
            }
        };
    }, []);

    const handleJoinMeeting = () => {
        if (!userName.trim()) {
            setError('Please enter your name');
            return;
        }

        if (!localStream && !isVideoOff) {
            // Try to get stream if not already available
            const getStream = async () => {
                try {
                    setIsLoading(true);
                    const constraints = {
                        audio: !isMuted,
                        video: !isVideoOff && {
                            width: { ideal: 640 },
                            height: { ideal: 480 }
                        }
                    };

                    const stream = await navigator.mediaDevices.getUserMedia(constraints);
                    
                    // Apply mute settings
                    if (stream.getAudioTracks().length > 0) {
                        stream.getAudioTracks()[0].enabled = !isMuted;
                    }
                    
                    onJoin(userName.trim(), stream, isMuted, isVideoOff);
                } catch (err) {
                    console.error('Error getting stream:', err);
                    setError('Failed to access media devices. Please check permissions.');
                    setIsLoading(false);
                }
            };
            
            getStream();
        } else {
            // Create a new stream with current settings
            const createStream = async () => {
                try {
                    setIsLoading(true);
                    
                    // If video is off but we want audio, create audio-only stream
                    const constraints = {
                        audio: true,
                        video: !isVideoOff && {
                            width: { ideal: 640 },
                            height: { ideal: 480 }
                        }
                    };

                    let stream;
                    
                    if (isVideoOff) {
                        // Audio only
                        try {
                            const audioStream = await navigator.mediaDevices.getUserMedia({
                                audio: true,
                                video: false
                            });
                            
                            if (audioStream.getAudioTracks().length > 0) {
                                audioStream.getAudioTracks()[0].enabled = !isMuted;
                            }
                            stream = audioStream;
                        } catch (audioErr) {
                            // If audio fails too, create an empty stream
                            stream = new MediaStream();
                        }
                    } else {
                        // Audio and video
                        stream = await navigator.mediaDevices.getUserMedia(constraints);
                        
                        // Apply mute settings
                        if (stream.getAudioTracks().length > 0) {
                            stream.getAudioTracks()[0].enabled = !isMuted;
                        }
                        
                        // Apply video settings
                        if (stream.getVideoTracks().length > 0) {
                            stream.getVideoTracks()[0].enabled = true;
                        }
                    }
                    
                    onJoin(userName.trim(), stream, isMuted, isVideoOff);
                } catch (err) {
                    console.error('Error creating stream:', err);
                    setError('Failed to setup media devices. Please check permissions.');
                    
                    // Even if media fails, join with empty stream
                    const emptyStream = new MediaStream();
                    onJoin(userName.trim(), emptyStream, true, true);
                } finally {
                    setIsLoading(false);
                }
            };
            
            createStream();
        }
    };

    const toggleAudio = () => {
        setIsMuted(!isMuted);
        if (localStream && localStream.getAudioTracks().length > 0) {
            localStream.getAudioTracks()[0].enabled = !isMuted;
        }
    };

    const toggleVideo = async () => {
        const newVideoState = !isVideoOff;
        setIsVideoOff(newVideoState);
        
        if (!newVideoState && !localStream) {
            // Turning video on
            try {
                setIsLoading(true);
                const constraints = {
                    video: {
                        width: { ideal: 640 },
                        height: { ideal: 480 },
                        facingMode: 'user'
                    },
                    audio: true
                };

                const stream = await navigator.mediaDevices.getUserMedia(constraints);
                setLocalStream(stream);
                
                // Apply audio settings
                if (stream.getAudioTracks().length > 0) {
                    stream.getAudioTracks()[0].enabled = !isMuted;
                }
                
                if (videoRef.current) {
                    videoRef.current.srcObject = stream;
                }
            } catch (err) {
                console.error('Error turning video on:', err);
                setError('Could not access camera');
                setIsVideoOff(true);
            } finally {
                setIsLoading(false);
            }
        } else if (localStream) {
            // Turning video off
            const videoTracks = localStream.getVideoTracks();
            videoTracks.forEach(track => track.stop());
            
            if (videoRef.current) {
                videoRef.current.srcObject = null;
            }
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !isLoading) {
            handleJoinMeeting();
        }
    };

    return (
        <div className="h-screen bg-gradient-to-br from-gray-900 to-gray-800 flex items-center justify-center p-4">
            <div className="max-w-6xl w-full grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Left Panel - Preview and Controls */}
                <div className="bg-gray-800 rounded-2xl p-6 flex flex-col">
                    <h2 className="text-white text-2xl font-semibold mb-6">Setup your audio and video</h2>
                    
                    {/* Preview Area */}
                    <div className="flex-1 bg-gray-900 rounded-xl overflow-hidden mb-6 relative">
                        {!isVideoOff ? (
                            <>
                                <video
                                    ref={videoRef}
                                    autoPlay
                                    muted
                                    playsInline
                                    className="w-full h-full object-cover"
                                />
                                {isLoading && (
                                    <div className="absolute inset-0 bg-gray-900/80 flex items-center justify-center">
                                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white"></div>
                                    </div>
                                )}
                            </>
                        ) : (
                            <div className="w-full h-full flex items-center justify-center bg-gray-900">
                                <div className="text-center">
                                    <div className="w-24 h-24 bg-gray-700 rounded-full flex items-center justify-center mx-auto mb-4">
                                        <CameraOff className="w-12 h-12 text-gray-500" />
                                    </div>
                                    <p className="text-gray-400">Camera is off</p>
                                </div>
                            </div>
                        )}
                        
                        {/* User Name Badge */}
                        {userName && (
                            <div className="absolute bottom-4 left-4 bg-black/60 backdrop-blur-sm px-3 py-1.5 rounded-lg">
                                <p className="text-white text-sm font-medium">{userName}</p>
                            </div>
                        )}
                    </div>
                    
                    {/* Quick Controls */}
                    <div className="flex items-center justify-center gap-6 mb-8">
                        <button
                            onClick={toggleAudio}
                            className={`flex flex-col items-center gap-2 p-3 rounded-xl transition-all ${isMuted
                                    ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30'
                                    : 'bg-gray-700 text-white hover:bg-gray-600'
                                }`}
                        >
                            <div className={`p-3 rounded-full ${isMuted ? 'bg-red-500' : 'bg-gray-600'}`}>
                                {isMuted ? (
                                    <MicOff className="w-6 h-6" />
                                ) : (
                                    <Mic className="w-6 h-6" />
                                )}
                            </div>
                            <span className="text-sm font-medium">
                                {isMuted ? 'Unmute' : 'Mute'}
                            </span>
                        </button>
                        
                        <button
                            onClick={toggleVideo}
                            className={`flex flex-col items-center gap-2 p-3 rounded-xl transition-all ${isVideoOff
                                    ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30'
                                    : 'bg-gray-700 text-white hover:bg-gray-600'
                                }`}
                        >
                            <div className={`p-3 rounded-full ${isVideoOff ? 'bg-red-500' : 'bg-gray-600'}`}>
                                {isVideoOff ? (
                                    <CameraOff className="w-6 h-6" />
                                ) : (
                                    <Camera className="w-6 h-6" />
                                )}
                            </div>
                            <span className="text-sm font-medium">
                                {isVideoOff ? 'Turn on' : 'Turn off'}
                            </span>
                        </button>
                    </div>
                    
                    {/* Settings Toggle */}
                    <button
                        onClick={() => setShowSettings(!showSettings)}
                        className="text-gray-400 text-sm hover:text-white mb-4"
                    >
                        {showSettings ? 'Hide settings' : 'Show settings'}
                    </button>
                    
                    {/* Device Settings */}
                    {showSettings && (
                        <div className="bg-gray-900 rounded-xl p-4 mb-6 space-y-4">
                            <div>
                                <label className="text-gray-400 text-sm block mb-2">Camera</label>
                                <select className="w-full bg-gray-800 text-white rounded-lg px-3 py-2">
                                    {availableDevices.video.map(device => (
                                        <option key={device.deviceId} value={device.deviceId}>
                                            {device.label || `Camera ${device.deviceId.slice(0, 8)}`}
                                        </option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label className="text-gray-400 text-sm block mb-2">Microphone</label>
                                <select className="w-full bg-gray-800 text-white rounded-lg px-3 py-2">
                                    {availableDevices.audio.map(device => (
                                        <option key={device.deviceId} value={device.deviceId}>
                                            {device.label || `Microphone ${device.deviceId.slice(0, 8)}`}
                                        </option>
                                    ))}
                                </select>
                            </div>
                        </div>
                    )}
                </div>
                
                {/* Right Panel - Join Info */}
                <div className="flex flex-col">
                    <div className="flex-1 bg-gray-800 rounded-2xl p-8 flex flex-col">
                        <div className="mb-8">
                            <h1 className="text-3xl font-bold text-white mb-2">TrueTalk Meeting</h1>
                            <p className="text-gray-400">Ready to join?</p>
                        </div>
                        
                        {/* Meeting Info */}
                        <div className="mb-8">
                            <p className="text-gray-400 text-sm mb-2">Meeting ID</p>
                            <div className="bg-gray-900 rounded-xl p-4">
                                <p className="text-white text-xl font-mono">{meetingId}</p>
                            </div>
                        </div>
                        
                        {/* User Name Input */}
                        <div className="mb-8">
                            <label className="text-gray-400 text-sm block mb-2">Your Name</label>
                            <div className="relative">
                                <div className="absolute left-3 top-1/2 transform -translate-y-1/2">
                                    <User className="w-5 h-5 text-gray-500" />
                                </div>
                                <input
                                    type="text"
                                    value={userName}
                                    onChange={(e) => setUserName(e.target.value)}
                                    onKeyPress={handleKeyPress}
                                    placeholder="Enter your name"
                                    className="w-full bg-gray-900 text-white pl-10 pr-4 py-3 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    autoFocus
                                />
                            </div>
                        </div>
                        
                        {/* Device Status */}
                        <div className="bg-gray-900 rounded-xl p-4 mb-8 space-y-3">
                            <div className="flex items-center justify-between">
                                <span className="text-gray-400">Camera</span>
                                <div className="flex items-center gap-2">
                                    <div className={`w-2 h-2 rounded-full ${isVideoOff ? 'bg-red-500' : 'bg-green-500'}`}></div>
                                    <span className="text-white">{isVideoOff ? 'Off' : 'On'}</span>
                                </div>
                            </div>
                            <div className="flex items-center justify-between">
                                <span className="text-gray-400">Microphone</span>
                                <div className="flex items-center gap-2">
                                    <div className={`w-2 h-2 rounded-full ${isMuted ? 'bg-red-500' : 'bg-green-500'}`}></div>
                                    <span className="text-white">{isMuted ? 'Muted' : 'Unmuted'}</span>
                                </div>
                            </div>
                        </div>
                        
                        {/* Error Message */}
                        {error && (
                            <div className="mb-6 p-4 bg-red-500/20 border border-red-500/30 rounded-xl">
                                <div className="flex items-center gap-2 text-red-400">
                                    <AlertCircle className="w-5 h-5" />
                                    <p className="text-sm">{error}</p>
                                </div>
                            </div>
                        )}
                        
                        {/* Tip */}
                        <div className="text-gray-500 text-sm mb-8">
                            <p className="mb-2">TIP: Make sure your camera and microphone are working before joining.</p>
                            <p>Click the buttons above to test your audio and video.</p>
                        </div>
                        
                        {/* Join Button */}
                        <button
                            onClick={handleJoinMeeting}
                            disabled={isLoading || !userName.trim()}
                            className={`w-full py-4 rounded-xl font-semibold text-lg transition-all ${isLoading || !userName.trim()
                                    ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                                    : 'bg-blue-600 hover:bg-blue-700 text-white hover:shadow-lg hover:shadow-blue-600/25'
                                }`}
                        >
                            {isLoading ? (
                                <div className="flex items-center justify-center gap-2">
                                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                                    <span>Setting up...</span>
                                </div>
                            ) : (
                                'Join Meeting'
                            )}
                        </button>
                    </div>
                    
                    {/* Footer */}
                    <div className="mt-6 text-center">
                        <p className="text-gray-500 text-sm">
                            By joining, you agree to our Terms of Service and Privacy Policy
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}