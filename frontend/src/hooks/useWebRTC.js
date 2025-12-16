import { useRef, useState } from 'react';

export const useWebRTC = (localStream, sendMessage, userId) => {
  const [remoteStreams, setRemoteStreams] = useState(new Map());
  const peerConnectionsRef = useRef(new Map());

  const configuration = {
    iceServers: [
      { urls: 'stun:stun.l.google.com:19302' },
      { urls: 'stun:stun1.l.google.com:19302' },
    ],
  };

  const createPeerConnection = (remoteUserId) => {
    if (peerConnectionsRef.current.has(remoteUserId)) {
      return peerConnectionsRef.current.get(remoteUserId);
    }

    const pc = new RTCPeerConnection(configuration);

    /* ✅ Add tracks ONCE (NO DUPLICATES) */
    if (localStream) {
      localStream.getTracks().forEach(track => {
        const exists = pc.getSenders().some(
          sender => sender.track === track
        );
        if (!exists) {
          pc.addTrack(track, localStream);
        }
      });
    }

    pc.ontrack = (event) => {
      setRemoteStreams(prev => {
        const map = new Map(prev);
        map.set(remoteUserId, event.streams[0]);
        return map;
      });
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
      if (['failed', 'disconnected'].includes(pc.connectionState)) {
        setRemoteStreams(prev => {
          const map = new Map(prev);
          map.delete(remoteUserId);
          return map;
        });
      }
    };

    peerConnectionsRef.current.set(remoteUserId, pc);
    return pc;
  };

  const handleUserJoined = async ({ userId: remoteUserId }) => {
    if (remoteUserId === userId) return;

    const pc = createPeerConnection(remoteUserId);
    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);

    sendMessage('offer', { offer, target: remoteUserId });
  };

  const handleOffer = async ({ sender, offer }) => {
    if (sender === userId) return;

    const pc = createPeerConnection(sender);
    await pc.setRemoteDescription(new RTCSessionDescription(offer));

    const answer = await pc.createAnswer();
    await pc.setLocalDescription(answer);

    sendMessage('answer', { answer, target: sender });
  };

  const handleAnswer = async ({ sender, answer }) => {
    if (sender === userId) return;

    const pc = peerConnectionsRef.current.get(sender);
    if (pc) {
      await pc.setRemoteDescription(new RTCSessionDescription(answer));
    }
  };

  const handleICECandidate = async ({ sender, candidate }) => {
    if (sender === userId) return;

    const pc = peerConnectionsRef.current.get(sender);
    if (pc && candidate) {
      await pc.addIceCandidate(new RTCIceCandidate(candidate));
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
