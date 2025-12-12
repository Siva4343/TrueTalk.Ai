import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Video, ArrowLeft, LogIn } from 'lucide-react';

export default function JoinMeeting() {
    const [meetingInput, setMeetingInput] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleJoinMeeting = (e) => {
        e.preventDefault();

        if (!meetingInput.trim()) {
            alert('Please enter a meeting ID or code');
            return;
        }

        setLoading(true);

        // Navigate to meeting room
        // The input can be either UUID or meeting code
        navigate(`/meeting/${meetingInput.trim()}`);
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-purple-600 to-blue-600 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full">
                {/* Back Button */}
                <button
                    onClick={() => navigate('/')}
                    className="flex items-center text-gray-600 hover:text-gray-800 mb-6 transition-colors"
                >
                    <ArrowLeft className="w-5 h-5 mr-2" />
                    Back to Home
                </button>

                {/* Header */}
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-16 h-16 bg-purple-600 rounded-full mb-4">
                        <Video className="w-8 h-8 text-white" />
                    </div>
                    <h1 className="text-2xl font-bold text-gray-800 mb-2">
                        Join a Meeting
                    </h1>
                    <p className="text-gray-600">
                        Enter the meeting ID or code to join
                    </p>
                </div>

                {/* Form */}
                <form onSubmit={handleJoinMeeting} className="space-y-6">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Meeting ID or Code
                        </label>
                        <input
                            type="text"
                            value={meetingInput}
                            onChange={(e) => setMeetingInput(e.target.value)}
                            placeholder="e.g., abc-def-ghi or full meeting ID"
                            className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none text-gray-800 transition-all"
                            required
                        />
                        <p className="mt-2 text-sm text-gray-500">
                            Enter the meeting code (e.g., abc-def-ghi) or full meeting ID
                        </p>
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-4 px-6 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed text-lg flex items-center justify-center gap-2"
                    >
                        <LogIn className="w-5 h-5" />
                        {loading ? 'Joining...' : 'Join Meeting'}
                    </button>
                </form>

                {/* Info Box */}
                <div className="mt-6 bg-blue-50 border-l-4 border-blue-500 p-4 rounded">
                    <p className="text-sm text-gray-700">
                        <strong className="text-blue-700">Tip:</strong> Ask the meeting host to share the meeting link or code with you.
                    </p>
                </div>
            </div>
        </div>
    );
}
