import { useRef, useState } from 'react';

export const useWebRTC = (localStream, sendMessage, userId) => {
    const [remoteStreams, setRemoteStreams] = useState(new Map());
    const peerConnectionsRef = useRef(new Map());

    const configuration = {
        iceServers: [
            { urls: 'stun:stun.l.google.com:19302' },
            { urls: 'stun:stun1.l.google.com:19302' },
        ]
    };

    const createPeerConnection = (remoteUserId) => {
        if (peerConnectionsRef.current.has(remoteUserId)) {
            return peerConnectionsRef.current.get(remoteUserId);
        }

        const pc = new RTCPeerConnection(configuration);

        if (localStream) {
            localStream.getTracks().forEach(track => {
                pc.addTrack(track, localStream);
            });
        }

        pc.ontrack = (event) => {
            console.log('Received remote track from:', remoteUserId);
            setRemoteStreams(prev => new Map(prev).set(remoteUserId, event.streams[0]));
        };

        pc.onicecandidate = (event) => {
            if (event.candidate) {
                sendMessage('ice-candidate', {
                    candidate: event.candidate,
                    target: remoteUserId,
                });
            }
        };

        pc.onconnectionstatechange = () => {
            console.log('Connection state:', pc.connectionState);
            if (pc.connectionState === 'disconnected' || pc.connectionState === 'failed') {
                setRemoteStreams(prev => {
                    const newMap = new Map(prev);
                    newMap.delete(remoteUserId);
                    return newMap;
                });
            }
        };

        peerConnectionsRef.current.set(remoteUserId, pc);
        return pc;
    };

    const handleUserJoined = async (data) => {
        const remoteUserId = data.userId;
        if (remoteUserId === userId) return;

        const pc = createPeerConnection(remoteUserId);
        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);

        sendMessage('offer', { offer: offer, target: remoteUserId });
    };

    const handleOffer = async (data) => {
        const remoteUserId = data.sender;
        if (remoteUserId === userId) return;

        const pc = createPeerConnection(remoteUserId);
        await pc.setRemoteDescription(new RTCSessionDescription(data.offer));
        const answer = await pc.createAnswer();
        await pc.setLocalDescription(answer);

        sendMessage('answer', { answer: answer, target: remoteUserId });
    };

    const handleAnswer = async (data) => {
        const remoteUserId = data.sender;
        if (remoteUserId === userId) return;

        const pc = peerConnectionsRef.current.get(remoteUserId);
        if (pc) {
            await pc.setRemoteDescription(new RTCSessionDescription(data.answer));
        }
    };

    const handleICECandidate = async (data) => {
        const remoteUserId = data.sender;
        if (remoteUserId === userId) return;

        const pc = peerConnectionsRef.current.get(remoteUserId);
        if (pc && data.candidate) {
            await pc.addIceCandidate(new RTCIceCandidate(data.candidate));
        }
    };

    return {
        remoteStreams,
        handleUserJoined,
        handleOffer,
        handleAnswer,
        handleICECandidate,
    };
};
