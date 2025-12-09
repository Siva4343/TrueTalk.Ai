import { useState, useEffect } from 'react';

export default function CallModal({ call, onAccept, onReject, onEnd }) {
    const [duration, setDuration] = useState(0);

    useEffect(() => {
        let interval;
        if (call.status === 'connected') {
            interval = setInterval(() => {
                setDuration(prev => prev + 1);
            }, 1000);
        }
        return () => clearInterval(interval);
    }, [call.status]);

    const formatDuration = (seconds) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    if (!call) return null;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-80 z-50 flex items-center justify-center">
            <div className="bg-gray-900 rounded-2xl p-8 w-80 flex flex-col items-center shadow-2xl border border-gray-800">
                <div className="w-24 h-24 rounded-full bg-gray-700 mb-6 flex items-center justify-center overflow-hidden">
                    {call.otherUser?.avatar ? (
                        <img src={call.otherUser.avatar} alt="Avatar" className="w-full h-full object-cover" />
                    ) : (
                        <span className="text-3xl text-white font-bold">
                            {call.otherUser?.username?.substring(0, 2).toUpperCase()}
                        </span>
                    )}
                </div>

                <h3 className="text-xl font-bold text-white mb-2">{call.otherUser?.username}</h3>
                <p className="text-gray-400 mb-8 animate-pulse">
                    {call.status === 'incoming' && 'Incoming Call...'}
                    {call.status === 'outgoing' && 'Calling...'}
                    {call.status === 'connected' && formatDuration(duration)}
                </p>

                <div className="flex space-x-8">
                    {call.status === 'incoming' ? (
                        <>
                            <button
                                onClick={onReject}
                                className="w-16 h-16 rounded-full bg-red-600 hover:bg-red-700 flex items-center justify-center transition-transform hover:scale-110"
                            >
                                <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                            <button
                                onClick={onAccept}
                                className="w-16 h-16 rounded-full bg-green-600 hover:bg-green-700 flex items-center justify-center transition-transform hover:scale-110 animate-bounce"
                            >
                                <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                                </svg>
                            </button>
                        </>
                    ) : (
                        <button
                            onClick={onEnd}
                            className="w-16 h-16 rounded-full bg-red-600 hover:bg-red-700 flex items-center justify-center transition-transform hover:scale-110"
                        >
                            <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}
