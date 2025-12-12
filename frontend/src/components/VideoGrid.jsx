import VideoTile from './VideoTile';

export default function VideoGrid({ localStream, remoteStreams, isVideoOff, isMuted, userName, viewMode = 'grid' }) {
    const allStreams = [
        { id: 'local', stream: localStream, name: userName, isLocal: true, isMuted, isVideoOff },
        ...Array.from(remoteStreams.entries()).map(([id, stream]) => ({
            id,
            stream,
            name: 'Participant',
            isLocal: false,
            isMuted: false,
            isVideoOff: false,
        })),
    ];

    const totalParticipants = allStreams.length;

    // Teams-style layout logic
    const getGridLayout = () => {
        if (totalParticipants === 1) {
            return 'grid-cols-1';
        } else if (totalParticipants === 2) {
            return 'grid-cols-2';
        } else if (totalParticipants <= 4) {
            return 'grid-cols-2 grid-rows-2';
        } else if (totalParticipants <= 6) {
            return 'grid-cols-3 grid-rows-2';
        } else if (totalParticipants <= 9) {
            return 'grid-cols-3 grid-rows-3';
        } else {
            return 'grid-cols-4 grid-rows-3';
        }
    };

    // Gallery view: Show main speakers + thumbnails
    if (viewMode === 'gallery') {
        const mainSpeakers = allStreams.slice(0, 3); // Show first 3 as main
        const thumbnails = allStreams.slice(3); // Rest as thumbnails

        return (
            <div className="h-full flex gap-3">
                {/* Main video area */}
                <div className="flex-1 flex flex-col gap-3">
                    {mainSpeakers.length === 1 && (
                        <div className="h-full">
                            <VideoTile
                                stream={mainSpeakers[0].stream}
                                isLocal={mainSpeakers[0].isLocal}
                                isMuted={mainSpeakers[0].isMuted}
                                isVideoOff={mainSpeakers[0].isVideoOff}
                                name={mainSpeakers[0].name}
                            />
                        </div>
                    )}
                    {mainSpeakers.length === 2 && (
                        <div className="h-full grid grid-cols-2 gap-3">
                            {mainSpeakers.map((participant) => (
                                <VideoTile
                                    key={participant.id}
                                    stream={participant.stream}
                                    isLocal={participant.isLocal}
                                    isMuted={participant.isMuted}
                                    isVideoOff={participant.isVideoOff}
                                    name={participant.name}
                                />
                            ))}
                        </div>
                    )}
                    {mainSpeakers.length >= 3 && (
                        <div className="h-full grid grid-cols-2 gap-3">
                            {/* Large speaker on left */}
                            <div className="row-span-2">
                                <VideoTile
                                    stream={mainSpeakers[0].stream}
                                    isLocal={mainSpeakers[0].isLocal}
                                    isMuted={mainSpeakers[0].isMuted}
                                    isVideoOff={mainSpeakers[0].isVideoOff}
                                    name={mainSpeakers[0].name}
                                />
                            </div>
                            {/* Two smaller on right */}
                            {mainSpeakers.slice(1, 3).map((participant) => (
                                <VideoTile
                                    key={participant.id}
                                    stream={participant.stream}
                                    isLocal={participant.isLocal}
                                    isMuted={participant.isMuted}
                                    isVideoOff={participant.isVideoOff}
                                    name={participant.name}
                                />
                            ))}
                        </div>
                    )}
                </div>

                {/* Thumbnail sidebar - Teams style */}
                {thumbnails.length > 0 && (
                    <div className="w-32 flex flex-col gap-2 overflow-y-auto">
                        {thumbnails.map((participant) => (
                            <div key={participant.id} className="aspect-square">
                                <VideoTile
                                    stream={participant.stream}
                                    isLocal={participant.isLocal}
                                    isMuted={participant.isMuted}
                                    isVideoOff={participant.isVideoOff}
                                    name={participant.name}
                                />
                            </div>
                        ))}
                    </div>
                )}
            </div>
        );
    }

    // Grid view: Equal tiles for all participants
    return (
        <div className={`h-full grid ${getGridLayout()} gap-2 auto-rows-fr`}>
            {allStreams.map((participant) => (
                <VideoTile
                    key={participant.id}
                    stream={participant.stream}
                    isLocal={participant.isLocal}
                    isMuted={participant.isMuted}
                    isVideoOff={participant.isVideoOff}
                    name={participant.name}
                />
            ))}
        </div>
    );
}
