import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { meetingAPI } from '../services/api';
import { Video } from 'lucide-react';

export default function Home() {
    const navigate = useNavigate();

    const handleStartMeeting = () => {
        navigate('/create');
    };

    const handleJoinMeeting = () => {
        navigate('/join');
    };

    const handleAdminLogin = () => {
        window.location.href = 'http://localhost:8000/admin/';
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-purple-600 to-blue-600 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-2xl p-12 max-w-lg w-full text-center">
                {/* Icon */}
                <div className="inline-flex items-center justify-center w-20 h-20 bg-purple-600 rounded-full mb-6">
                    <Video className="w-10 h-10 text-white" />
                </div>

                {/* Title */}
                <h1 className="text-4xl font-bold text-gray-800 mb-3">
                    TrueTalk.AI
                </h1>
                <p className="text-lg text-gray-600 mb-8">
                    Professional Video Meetings
                </p>

                {/* Buttons */}
                <div className="grid grid-cols-2 gap-4 mb-6">
                    <button
                        onClick={handleStartMeeting}
                        className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-4 px-6 rounded-lg transition-all text-lg"
                    >
                        Start a Meeting
                    </button>
                    <button
                        onClick={handleJoinMeeting}
                        className="bg-green-600 hover:bg-green-700 text-white font-semibold py-4 px-6 rounded-lg transition-all text-lg"
                    >
                        Join Meeting
                    </button>
                </div>
                <button
                    onClick={handleAdminLogin}
                    className="w-full bg-blue-500 hover:bg-blue-600 text-white font-semibold py-3 px-6 rounded-lg transition-all"
                >
                    Admin Login
                </button>
                <div className="mt-10"></div>

                {/* Features List */}
                <div className="text-left space-y-3">
                    <div className="flex items-center text-gray-700">
                        <span className="text-green-500 mr-3 text-xl">✓</span>
                        <span>Microsoft Teams-style interface</span>
                    </div>
                    <div className="flex items-center text-gray-700">
                        <span className="text-green-500 mr-3 text-xl">✓</span>
                        <span>HD video and audio</span>
                    </div>
                    <div className="flex items-center text-gray-700">
                        <span className="text-green-500 mr-3 text-xl">✓</span>
                        <span>Real-time chat</span>
                    </div>
                    <div className="flex items-center text-gray-700">
                        <span className="text-green-500 mr-3 text-xl">✓</span>
                        <span>Screen sharing</span>
                    </div>
                    <div className="flex items-center text-gray-700">
                        <span className="text-green-500 mr-3 text-xl">✓</span>
                        <span>Emoji reactions</span>
                    </div>
                    <div className="flex items-center text-gray-700">
                        <span className="text-green-500 mr-3 text-xl">✓</span>
                        <span>Up to 300 participants</span>
                    </div>
                </div>
            </div>
        </div>
    );
}
