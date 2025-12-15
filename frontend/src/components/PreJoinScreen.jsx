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

  /* ✅ Bind MediaStream to video */
  useEffect(() => {
    if (videoRef.current && previewStream) {
      videoRef.current.srcObject = previewStream;
    }
  }, [previewStream]);

  useEffect(() => {
    let active = true;
    let stream;

    const initPreview = async () => {
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: videoEnabled,
          audio: audioEnabled,
        });

        if (active) setPreviewStream(stream);
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
  }, [videoEnabled, audioEnabled]);

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
    <div className="h-screen bg-gray-900 flex items-center justify-center">
      <div className="max-w-5xl w-full grid grid-cols-1 lg:grid-cols-2 gap-6 p-6">

        {/* LEFT */}
        <div className="bg-gray-800 rounded-xl p-6">
          <h2 className="text-white text-xl font-bold mb-4">Meeting Preview</h2>

          <div className="aspect-video bg-black rounded-lg overflow-hidden mb-4">
            {previewStream && videoEnabled ? (
              <video
                ref={videoRef}
                autoPlay
                muted
                playsInline
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="h-full flex items-center justify-center text-gray-400">
                Camera Off
              </div>
            )}
          </div>

          <div className="flex justify-center gap-4">
            <button
              onClick={() => setVideoEnabled(v => !v)}
              className="bg-gray-700 px-4 py-2 rounded text-white"
            >
              {videoEnabled ? <Camera /> : <CameraOff />}
            </button>

            <button
              onClick={() => setAudioEnabled(a => !a)}
              className="bg-gray-700 px-4 py-2 rounded text-white"
            >
              {audioEnabled ? <Mic /> : <MicOff />}
            </button>
          </div>
        </div>

        {/* RIGHT */}
        <div className="bg-gray-800 rounded-xl p-6">
          <h1 className="text-white text-2xl font-bold mb-4">Join TrueTalk</h1>

          <p className="text-gray-400 mb-2">Meeting ID</p>
          <div className="bg-gray-900 p-3 rounded mb-4 text-white font-mono">
            {meetingId}
          </div>

          <input
            value={userName}
            onChange={e => setUserName(e.target.value)}
            placeholder="Your Name"
            className="w-full p-3 rounded bg-gray-900 text-white mb-4"
          />

          {error && (
            <div className="bg-red-500/20 text-red-400 p-3 rounded mb-4 flex gap-2">
              <AlertCircle /> {error}
            </div>
          )}

          <button
            disabled={!userName || isLoading}
            onClick={handleJoinMeeting}
            className="w-full py-3 rounded bg-blue-600 text-white font-semibold"
          >
            {isLoading ? 'Joining...' : 'Join Meeting'}
          </button>
        </div>

      </div>
    </div>
  );
}
