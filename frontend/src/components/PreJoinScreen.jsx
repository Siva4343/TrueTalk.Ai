import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Video, VideoOff, Mic, MicOff, Settings, Sparkles } from 'lucide-react';

export default function PreJoinScreen({ meetingId, onJoin }) {
    const [userName, setUserName] = useState('Guest User');
    const [isMuted, setIsMuted] = useState(false);
    const [isVideoOff, setIsVideoOff] = useState(false);
    const [stream, setStream] = useState(null);
    const videoRef = useRef(null);
    const navigate = useNavigate();

    useEffect(() => {
        // Get media stream for preview
        const getMedia = async () => {
            try {
                const mediaStream = await navigator.mediaDevices.getUserMedia({
                    video: true,
                    audio: true,
                });
                setStream(mediaStream);
                if (videoRef.current) {
                    videoRef.current.srcObject = mediaStream;
                }
            } catch (error) {
                console.error('Error accessing media:', error);
                alert('Please grant camera and microphone permissions');
            }
        };

        getMedia();

        return () => {
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
            }
        };
    }, []);

    useEffect(() => {
        if (stream && videoRef.current) {
            videoRef.current.srcObject = stream;
        }
    }, [stream]);

    const toggleMute = () => {
        if (stream) {
            stream.getAudioTracks().forEach(track => {
                track.enabled = !track.enabled;
            });
            setIsMuted(!isMuted);
        }
    };

    const toggleVideo = () => {
        if (stream) {
            stream.getVideoTracks().forEach(track => {
                track.enabled = !track.enabled;
            });
            setIsVideoOff(!isVideoOff);
        }
    };

    const handleJoin = () => {
        onJoin(userName, stream, isMuted, isVideoOff);
    };

    return (
        <div className="h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center p-6">
            {/* Background effects */}
            <div className="absolute inset-0 overflow-hidden">
                <div className="absolute top-0 left-0 w-[500px] h-[500px] bg-gradient-to-br from-purple-500/20 to-pink-500/20 rounded-full filter blur-3xl animate-float-slow"></div>
                <div className="absolute bottom-0 right-0 w-[600px] h-[600px] bg-gradient-to-br from-blue-500/20 to-cyan-500/20 rounded-full filter blur-3xl animate-float-slow-reverse"></div>
            </div>

            <div className="relative z-10 max-w-4xl w-full">
                {/* Header */}
                <div className="text-center mb-8">
                    <div className="inline-flex items-center gap-3 mb-4">
                        <div className="relative">
                            <div className="absolute inset-0 bg-gradient-to-r from-purple-500 to-blue-500 rounded-xl blur-lg opacity-75 animate-pulse"></div>
                            <div className="relative w-16 h-16 bg-gradient-to-br from-purple-500 via-blue-500 to-cyan-500 rounded-xl flex items-center justify-center shadow-lg">
                                <Sparkles className="w-8 h-8 text-white" />
                            </div>
                        </div>
                        <h1 className="text-4xl font-bold bg-gradient-to-r from-white via-purple-200 to-blue-200 bg-clip-text text-transparent">
                            TrueTalk Meeting
                        </h1>
                    </div>
                    <p className="text-xl text-gray-300">Ready to join?</p>
                </div>

                {/* Main content */}
                <div className="bg-black/30 backdrop-blur-2xl rounded-3xl border border-white/20 shadow-2xl overflow-hidden">
                    <div className="grid md:grid-cols-2 gap-6 p-8">
                        {/* Video preview */}
                        <div className="space-y-4">
                            <div className="relative aspect-video bg-gray-900 rounded-2xl overflow-hidden border border-white/10">
                                {stream && !isVideoOff ? (
                                    <video
                                        ref={videoRef}
                                        autoPlay
                                        muted
                                        playsInline
                                        className="w-full h-full object-cover"
                                    />
                                ) : (
                                    <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-purple-900/50 to-blue-900/50">
                                        <div className="text-center">
                                            <div className="w-24 h-24 bg-gradient-to-br from-purple-500 to-blue-500 rounded-full flex items-center justify-center mx-auto mb-4">
                                                <VideoOff className="w-12 h-12 text-white" />
                                            </div>
                                            <p className="text-white font-medium">Camera is off</p>
                                        </div>
                                    </div>
                                )}

                                {/* Overlay gradient */}
                                <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent pointer-events-none"></div>

                                {/* Name badge */}
                                <div className="absolute bottom-4 left-4 right-4">
                                    <div className="bg-black/60 backdrop-blur-md rounded-xl px-4 py-2 border border-white/20">
                                        <p className="text-white font-semibold">{userName || 'Guest User'}</p>
                                    </div>
                                </div>
                            </div>

                            {/* Controls */}
                            <div className="flex items-center justify-center gap-3">
                                <button
                                    onClick={toggleMute}
                                    className={`p-4 rounded-xl transition-all ${isMuted
                                            ? 'bg-red-500 hover:bg-red-600'
                                            : 'bg-white/10 hover:bg-white/20 border border-white/20'
                                        }`}
                                >
                                    {isMuted ? (
                                        <MicOff className="w-6 h-6 text-white" />
                                    ) : (
                                        <Mic className="w-6 h-6 text-white" />
                                    )}
                                </button>

                                <button
                                    onClick={toggleVideo}
                                    className={`p-4 rounded-xl transition-all ${isVideoOff
                                            ? 'bg-red-500 hover:bg-red-600'
                                            : 'bg-white/10 hover:bg-white/20 border border-white/20'
                                        }`}
                                >
                                    {isVideoOff ? (
                                        <VideoOff className="w-6 h-6 text-white" />
                                    ) : (
                                        <Video className="w-6 h-6 text-white" />
                                    )}
                                </button>

                                <button className="p-4 rounded-xl bg-white/10 hover:bg-white/20 border border-white/20 transition-all">
                                    <Settings className="w-6 h-6 text-white" />
                                </button>
                            </div>
                        </div>

                        {/* Join form */}
                        <div className="flex flex-col justify-center space-y-6">
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-2">
                                    Your Name
                                </label>
                                <input
                                    type="text"
                                    value={userName}
                                    onChange={(e) => setUserName(e.target.value)}
                                    placeholder="Enter your name"
                                    className="w-full px-4 py-3 bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl text-white placeholder-gray-400 focus:border-purple-500 focus:ring-2 focus:ring-purple-500/50 outline-none transition-all"
                                />
                            </div>

                            <div className="bg-blue-500/20 border border-blue-500/30 rounded-xl p-4">
                                <p className="text-sm text-blue-200">
                                    <strong className="text-blue-100">Tip:</strong> Make sure your camera and microphone are working before joining.
                                </p>
                            </div>

                            <button
                                onClick={handleJoin}
                                disabled={!userName.trim()}
                                className="w-full bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold py-4 px-6 rounded-xl transition-all transform hover:scale-105 shadow-lg shadow-purple-500/50 text-lg"
                            >
                                Join Meeting
                            </button>

                            <button
                                onClick={() => navigate('/')}
                                className="w-full bg-white/10 hover:bg-white/20 border border-white/20 text-white font-semibold py-3 px-6 rounded-xl transition-all"
                            >
                                Cancel
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
