import { useState, useEffect, useRef } from 'react';
import { AlertCircle, Camera, CameraOff, Mic, MicOff } from 'lucide-react';

export default function PreJoinScreen({ meetingId, onJoin }) {
  const [userName, setUserName] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [videoEnabled, setVideoEnabled] = useState(true);
  const [audioEnabled, setAudioEnabled] = useState(true);
  const [previewStream, setPreviewStream] = useState(null);

  const videoRef = useRef(null);
  const previewRef = useRef(null);
  const initialVideoRef = useRef(videoEnabled);
  const initialAudioRef = useRef(audioEnabled);

  /* ✅ Bind MediaStream to video */
  useEffect(() => {
    if (videoRef.current && previewStream) {
      videoRef.current.srcObject = previewStream;
      previewRef.current = previewStream;
    }
  }, [previewStream]);

  // Initialize preview stream once on mount (do not re-request on toggle)
  // Initialize preview stream once on mount (do not re-request on toggle)
  useEffect(() => {
    let active = true;
    let stream;

    const initPreview = async () => {
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: initialVideoRef.current,
          audio: initialAudioRef.current,
        });

        if (active) {
          setPreviewStream(stream);
          previewRef.current = stream;
        }
      } catch (err) {
        console.error(err);
        setError('Camera or microphone permission denied');
      }
    };

    initPreview();

    return () => {
      active = false;
      if (stream) stream.getTracks().forEach(t => t.stop());
    };
  }, []);  // run once on mount

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      const s = previewRef.current;
      if (s) s.getTracks().forEach(t => t.stop());
    };
  }, []);

  // Toggle audio without re-requesting whole stream
  const toggleAudio = async () => {
    try {
      const s = previewRef.current;
      if (s) {
        const audioTracks = s.getAudioTracks();
        if (audioTracks.length > 0) {
          audioTracks.forEach(t => {
            t.enabled = !audioEnabled;
          });
          // create a fresh MediaStream object so the video element picks up changes reliably
          const newStream = new MediaStream(s.getTracks());
          previewRef.current = newStream;
          setPreviewStream(newStream);
          setAudioEnabled(prev => !prev);
        } else if (!audioEnabled) {
          // request audio-only and add track
          const audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
          const newTrack = audioStream.getAudioTracks()[0];
          s.addTrack(newTrack);
          const newStream = new MediaStream(s.getTracks());
          previewRef.current = newStream;
          setPreviewStream(newStream);
          setAudioEnabled(true);
        }
      } else {
        // fallback: create full stream
        const stream = await navigator.mediaDevices.getUserMedia({ audio: !audioEnabled, video: videoEnabled });
        setPreviewStream(stream);
        previewRef.current = stream;
        setAudioEnabled(prev => !prev);
      }
    } catch (err) {
      console.error('Audio toggle failed:', err);
      setError('Failed to toggle microphone. Check permissions.');
    }
  };

  // Toggle video without re-requesting whole stream
  const toggleVideo = async () => {
    try {
      const s = previewRef.current;
      if (s) {
        const videoTracks = s.getVideoTracks();
        if (videoTracks.length > 0) {
          // turn off video -> stop and remove tracks
          videoTracks.forEach(t => {
            if (typeof t.stop === 'function') {
              try { t.stop(); } catch (err) { console.warn('Error stopping track', err); }
            }
            if (typeof s.removeTrack === 'function') {
              try { s.removeTrack(t); } catch (err) { console.warn('Error removing track', err); }
            }
          });

          // Rebuild preview stream (audio-only)
          const newStream = new MediaStream(s.getTracks());
          previewRef.current = newStream;
          setPreviewStream(newStream);
          setVideoEnabled(false);

        } else {
          // request video-only and add track
          const videoStream = await navigator.mediaDevices.getUserMedia({ video: true });
          const vTrack = videoStream.getVideoTracks()[0];
          s.addTrack(vTrack);

          // Rebuild preview stream so element detects the new track
          const newStream = new MediaStream(s.getTracks());
          previewRef.current = newStream;
          setPreviewStream(newStream);

          // Force update video element's srcObject and ensure play
          if (videoRef.current) {
            try {
              videoRef.current.srcObject = newStream;
              await videoRef.current.play().catch(() => {});
            } catch (err) {
              console.warn('Could not play video automatically', err);
            }
          }

          setVideoEnabled(true);
        }
      } else {
        // fallback: create full stream
        const stream = await navigator.mediaDevices.getUserMedia({ audio: audioEnabled, video: !videoEnabled });
        setPreviewStream(stream);
        previewRef.current = stream;
        setVideoEnabled(prev => !prev);
      }
    } catch (err) {
      console.error('Video toggle failed:', err);
      setError('Failed to toggle camera. Check permissions.');
    }
  };

  const handleJoinMeeting = async () => {
    if (!userName.trim()) {
      setError('Please enter your name');
      return;
    }

    try {
      setIsLoading(true);
      const stream = await navigator.mediaDevices.getUserMedia({
        video: videoEnabled,
        audio: audioEnabled,
      });

      previewStream?.getTracks().forEach(t => t.stop());
      onJoin(userName.trim(), stream);
    } catch {
      setError('Failed to join meeting');
      setIsLoading(false);
    }
  };

  return (
    <div className="h-screen bg-tt-dark flex items-center justify-center">
      <div className="max-w-4xl w-full grid grid-cols-1 lg:grid-cols-2 gap-6 p-6">

        {/* LEFT */}
        <div className="glass rounded-xl p-6">
          <h2 className="text-white text-xl font-bold mb-4">Meeting Preview</h2>

          <div className="aspect-video bg-black rounded-lg overflow-hidden mb-4 max-h-48 sm:max-h-60 lg:max-h-72">
            {previewStream && videoEnabled ? (
              <video
                ref={videoRef}
                autoPlay
                muted
                playsInline
                className="w-full h-full object-contain"
              />
            ) : (
              <div className="h-full flex items-center justify-center text-gray-400">
                Camera Off
              </div>
            )}
          </div>

          <div className="flex justify-center gap-4">
            <button
              onClick={toggleVideo}
              className={`control-btn ${!videoEnabled ? 'control-btn--toggled' : ''}`}
              title={videoEnabled ? 'Turn off camera' : 'Turn on camera'}
            >
              {videoEnabled ? <Camera className="control-btn-icon"/> : <CameraOff className="control-btn-icon"/>}
            </button>

            <button
              onClick={toggleAudio}
              className={`control-btn ${!audioEnabled ? 'control-btn--toggled' : ''}`}
              title={audioEnabled ? 'Mute mic' : 'Unmute mic'}
            >
              {audioEnabled ? <Mic className="control-btn-icon"/> : <MicOff className="control-btn-icon"/>}
            </button>
          </div>
        </div>

        {/* RIGHT */}
        <div className="glass rounded-xl p-6">
          <h1 className="text-white text-2xl font-bold mb-2">Join TrueTalk</h1>

          <p className="text-gray-400 mb-2">Meeting ID</p>
          <div className="bg-[#101010] p-3 rounded mb-4 text-white font-mono">
            {meetingId}
          </div>

          <input
            value={userName}
            onChange={e => setUserName(e.target.value)}
            placeholder="Your Name"
            className="participant-search mb-4"
          />

          {error && (
            <div className="bg-red-500/20 text-red-400 p-3 rounded mb-4 flex gap-2">
              <AlertCircle /> {error}
            </div>
          )}

          <button
            disabled={!userName || isLoading}
            onClick={handleJoinMeeting}
            className="w-full py-3 rounded control-btn--primary text-white font-semibold"
          >
            {isLoading ? 'Joining...' : 'Join Meeting'}
          </button>
        </div>

      </div>
    </div>
  );
}
