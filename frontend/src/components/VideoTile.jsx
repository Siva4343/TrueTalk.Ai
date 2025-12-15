// VideoTile.jsx
import { useEffect, useRef } from 'react';
import { MicOff, User } from 'lucide-react';

export default function VideoTile({ 
    stream, 
    isLocal, 
    isMuted, 
    isVideoOff, 
    name 
}) {
    const videoRef = useRef(null);

    // Update video element when stream changes
    useEffect(() => {
        if (videoRef.current && stream) {
            videoRef.current.srcObject = stream;
        }
    }, [stream]);

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
                        <p className="text-white text-lg font-medium">
                            {isLocal ? 'You' : name || 'Participant'}
                        </p>
                    </div>
                </div>
            )}

            {/* Name label at bottom */}
            <div className="absolute bottom-2 left-2 right-2">
                <div className="bg-black/70 backdrop-blur-sm px-3 py-1.5 rounded flex items-center justify-between">
                    <span className="text-white text-sm font-medium truncate">
                        {isLocal ? 'You' : name}
                    </span>
                    
                    {/* Show status indicators only (no controls) */}
                    <div className="flex items-center gap-1.5 ml-2">
                        {/* Camera off indicator */}
                        {isVideoOff && (
                            <div className="w-6 h-6 bg-[#3d3d3d] rounded-full flex items-center justify-center" title="Camera off">
                                <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                            </div>
                        )}
                        
                        {/* Muted indicator */}
                        {isMuted && (
                            <div className="w-6 h-6 bg-[#c4314b] rounded-full flex items-center justify-center" title="Microphone muted">
                                <MicOff className="w-3 h-3 text-white" />
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}