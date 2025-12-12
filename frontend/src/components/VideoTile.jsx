import { useEffect, useRef } from 'react';
import { MicOff, User } from 'lucide-react';

export default function VideoTile({ stream, isLocal, isMuted, isVideoOff, name }) {
    const videoRef = useRef(null);

    useEffect(() => {
        if (videoRef.current && stream) {
            videoRef.current.srcObject = stream;
        }
    }, [stream]);

    return (
        <div className="relative h-full bg-[#1a1a1a] rounded-lg overflow-hidden border-2 border-[#2d2d2d] hover:border-[#464775] transition-colors">
            {stream && !isVideoOff ? (
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
                    <span className="text-white text-sm font-medium truncate">{name}</span>
                    <div className="flex items-center gap-1.5 ml-2">
                        {isMuted && (
                            <div className="bg-[#c4314b] p-1 rounded">
                                <MicOff className="w-3.5 h-3.5 text-white" />
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
