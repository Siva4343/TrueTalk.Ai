// components/VideoGrid.jsx
import { useRef, useEffect } from 'react';

export default function VideoGrid({ 
    localStream, 
    remoteStreams, 
    isVideoOff, 
    isMuted, 
    userName, 
    viewMode = 'grid' 
}) {
    const localVideoRef = useRef(null);
    const remoteVideoRefs = useRef(new Map());

    // Update local video stream
    useEffect(() => {
        if (localVideoRef.current && localStream) {
            localVideoRef.current.srcObject = localStream;
        }
    }, [localStream]);

    // Update remote video streams
    useEffect(() => {
        remoteStreams.forEach((stream, userId) => {
            const videoRef = remoteVideoRefs.current.get(userId);
            if (videoRef?.current && stream) {
                videoRef.current.srcObject = stream;
            }
        });
    }, [remoteStreams]);

    // Create array of all participants
    const remoteStreamsArray = Array.from(remoteStreams.entries());
    const totalParticipants = remoteStreams.size + 1;

    // Get grid layout class
    const getGridLayout = () => {
        if (viewMode === 'speaker' || totalParticipants === 1) {
            return 'single-view';
        }
        
        if (totalParticipants === 2) {
            return 'grid-2';
        }
        
        if (totalParticipants === 3) {
            return 'grid-3';
        }
        
        if (totalParticipants === 4) {
            return 'grid-4';
        }
        
        if (totalParticipants <= 6) {
            return 'grid-6';
        }
        
        return 'grid-many';
    };

    // Create ref callback for remote videos
    const createRefCallback = (userId, stream) => (el) => {
        if (el) {
            // Store ref
            if (!remoteVideoRefs.current.has(userId)) {
                remoteVideoRefs.current.set(userId, { current: el });
            } else {
                remoteVideoRefs.current.get(userId).current = el;
            }
            
            // Set stream
            if (stream) {
                el.srcObject = stream;
            }
        }
    };

    // Render Speaker view
    if (viewMode === 'speaker' && totalParticipants > 1) {
        const mainSpeaker = remoteStreamsArray[0];
        
        return (
            <div className="video-grid speaker-view">
                {/* Main speaker video */}
                {mainSpeaker && (
                    <div className="main-speaker-tile">
                        <video
                            key={mainSpeaker[0]}
                            ref={createRefCallback(mainSpeaker[0], mainSpeaker[1])}
                            autoPlay
                            playsInline
                            className="video-element"
                        />
                        <div className="video-label">
                            <span>User {mainSpeaker[0].slice(-4)}</span>
                        </div>
                    </div>
                )}

                {/* Local video as picture-in-picture */}
                <div className="local-pip-tile">
                    <video
                        ref={localVideoRef}
                        autoPlay
                        playsInline
                        muted
                        className="video-element"
                    />
                    
                    {isVideoOff && (
                        <div className="video-placeholder">
                            <div className="avatar">
                                {userName.charAt(0).toUpperCase()}
                            </div>
                        </div>
                    )}
                    
                    <div className="video-label">
                        <span>{userName} (You)</span>
                        {isMuted && <span className="muted-icon">🔇</span>}
                        {isVideoOff && <span className="video-off-icon">📹</span>}
                    </div>
                </div>

                {/* Other participants thumbnails */}
                <div className="thumbnails-container">
                    {remoteStreamsArray.slice(1, 4).map(([userId, stream]) => (
                        <div key={userId} className="thumbnail-tile">
                            <video
                                ref={createRefCallback(userId, stream)}
                                autoPlay
                                playsInline
                                className="video-element"
                            />
                            <div className="thumbnail-label">
                                User {userId.slice(-4)}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        );
    }

    // Render Gallery view (grid)
    return (
        <div className={`video-grid ${getGridLayout()}`}>
            {/* Local Video (You) */}
            <div className={`video-tile local-video ${totalParticipants === 1 ? 'single-participant' : ''}`}>
                <video
                    ref={localVideoRef}
                    autoPlay
                    playsInline
                    muted
                    className="video-element"
                />
                
                {/* Video disabled indicator */}
                {isVideoOff && (
                    <div className="video-placeholder">
                        <div className="avatar">
                            {userName.charAt(0).toUpperCase()}
                        </div>
                    </div>
                )}
                
                {/* Name tag */}
                <div className="video-label">
                    <span>{userName} (You)</span>
                    {isMuted && <span className="muted-icon">🔇</span>}
                    {isVideoOff && <span className="video-off-icon">📹</span>}
                </div>
            </div>

            {/* Remote Participants */}
            {remoteStreamsArray.map(([userId, stream]) => (
                <div key={userId} className="video-tile remote-video">
                    <video
                        ref={createRefCallback(userId, stream)}
                        autoPlay
                        playsInline
                        className="video-element"
                    />
                    <div className="video-label">
                        <span>User {userId.slice(-4)}</span>
                    </div>
                </div>
            ))}
        </div>
    );
}