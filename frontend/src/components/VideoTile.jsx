import { useEffect, useRef } from 'react';
import { MicOff, User, Video, VideoOff } from 'lucide-react';

export default function VideoTile({ 
    stream, 
    isLocal, 
    isMuted, 
    isVideoOff, 
    name,
    onToggleVideo,
    onToggleMute
}) {
    const videoRef = useRef(null);

    // Update video element when stream changes
    useEffect(() => {
        if (videoRef.current && stream) {
            videoRef.current.srcObject = stream;
        }
    }, [stream]);

    // Handle video toggle for local user
    const handleToggleVideo = () => {
        if (isLocal && onToggleVideo) {
            onToggleVideo();
        }
    };

    // Handle mute toggle for local user
    const handleToggleMute = () => {
        if (isLocal && onToggleMute) {
            onToggleMute();
        }
    };

    // Check if stream has video tracks
    const hasVideoTracks = stream && stream.getVideoTracks && stream.getVideoTracks().length > 0;
    const shouldShowVideo = !isVideoOff && hasVideoTracks;

    return (
        <div className="relative h-full bg-[#1a1a1a] rounded-lg overflow-hidden border-2 border-[#2d2d2d] hover:border-[#464775] transition-colors">
            {/* Video element - show only if video is enabled AND stream has video tracks */}
            {shouldShowVideo ? (
                <video
                    ref={videoRef}
                    autoPlay
                    playsInline
                    muted={isLocal}
                    className="w-full h-full object-cover"
                />
            ) : (
                <div className="w-full h-full flex items-center justify-center bg-[#2d2d2d]">
                    <div className="text-center">
                        <div className="w-24 h-24 bg-[#464775] rounded-full flex items-center justify-center mx-auto mb-3">
                            <User className="w-12 h-12 text-white" />
                        </div>
                        <p className="text-white text-lg font-medium">{name}</p>
                    </div>
                </div>
            )}

            {/* Name label at bottom */}
            <div className="absolute bottom-2 left-2 right-2 z-10">
                <div className="bg-black/70 backdrop-blur-sm px-3 py-1.5 rounded flex items-center justify-between">
                    <span className="text-white text-sm font-medium truncate">
                        {isLocal ? 'You' : name}
                    </span>
                    <div className="flex items-center gap-1.5 ml-2">
                        {/* Show controls for local user */}
                        {isLocal ? (
                            <div className="flex gap-2">
                                <button
                                    onClick={handleToggleVideo}
                                    className={`p-1.5 rounded ${isVideoOff ? 'bg-[#c4314b]' : 'bg-[#3d3d3d]'}`}
                                    title={isVideoOff ? 'Turn on camera' : 'Turn off camera'}
                                >
                                    {isVideoOff ? (
                                        <VideoOff className="w-4 h-4 text-white" />
                                    ) : (
                                        <Video className="w-4 h-4 text-white" />
                                    )}
                                </button>
                                <button
                                    onClick={handleToggleMute}
                                    className={`p-1.5 rounded ${isMuted ? 'bg-[#c4314b]' : 'bg-[#3d3d3d]'}`}
                                    title={isMuted ? 'Unmute microphone' : 'Mute microphone'}
                                >
                                    <MicOff className={`w-4 h-4 ${isMuted ? 'text-white' : 'text-gray-300'}`} />
                                </button>
                            </div>
                        ) : (
                            // Show status for remote users
                            <>
                                {isVideoOff && (
                                    <span className="text-xs text-gray-300 bg-black/50 px-2 py-1 rounded flex items-center gap-1" title="Camera off">
                                        <VideoOff className="w-3 h-3" />
                                    </span>
                                )}
                                {isMuted && (
                                    <div className="bg-[#c4314b] p-1 rounded" title="Microphone muted">
                                        <MicOff className="w-3.5 h-3.5 text-white" />
                                    </div>
                                )}
                            </>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}