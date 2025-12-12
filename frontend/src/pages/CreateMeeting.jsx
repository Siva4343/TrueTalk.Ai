import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { meetingAPI } from '../services/api';
import { Video, ArrowLeft, Copy, Check, ExternalLink } from 'lucide-react';

export default function CreateMeeting() {
    const [title, setTitle] = useState('Test Meeting');
    const [description, setDescription] = useState('');
    const [maxParticipants, setMaxParticipants] = useState(10);
    const [loading, setLoading] = useState(false);
    const [createdMeeting, setCreatedMeeting] = useState(null);
    const [copied, setCopied] = useState(false);
    const navigate = useNavigate();

    const handleCreateMeeting = async (e) => {
        e.preventDefault();
        setLoading(true);

        try {
            const meeting = await meetingAPI.createMeeting({
                title: title || 'Test Meeting',
                description: description,
                max_participants: parseInt(maxParticipants),
                is_lobby_enabled: false,
                is_chat_enabled: true,
                is_screen_share_enabled: true,
            });

            setCreatedMeeting(meeting);
        } catch (error) {
            console.error('Error creating meeting:', error);
            alert('Failed to create meeting. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const getMeetingLink = () => {
        if (!createdMeeting) return '';
        return `${window.location.origin}/meeting/${createdMeeting.id}`;
    };

    const copyMeetingLink = () => {
        navigator.clipboard.writeText(getMeetingLink());
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const joinMeeting = () => {
        navigate(`/meeting/${createdMeeting.id}`);
    };

    // If meeting is created, show success screen
    if (createdMeeting) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-purple-600 to-blue-600 flex items-center justify-center p-4">
                <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-2xl w-full">
                    {/* Success Header */}
                    <div className="text-center mb-8">
                        <div className="inline-flex items-center justify-center w-16 h-16 bg-green-500 rounded-full mb-4">
                            <Check className="w-8 h-8 text-white" />
                        </div>
                        <h1 className="text-3xl font-bold text-gray-800 mb-2">
                            Meeting Created Successfully!
                        </h1>
                        <p className="text-gray-600">
                            Share this link with others to join the meeting
                        </p>
                    </div>

                    {/* Meeting Details */}
                    <div className="bg-gray-50 rounded-lg p-6 mb-6">
                        <h2 className="text-xl font-semibold text-gray-800 mb-4">
                            {createdMeeting.title}
                        </h2>

                        <div className="space-y-3 text-sm text-gray-600 mb-6">
                            <div className="flex items-center">
                                <span className="font-medium w-32">Meeting ID:</span>
                                <code className="bg-white px-3 py-1 rounded border text-gray-800">
                                    {createdMeeting.id}
                                </code>
                            </div>
                            <div className="flex items-center">
                                <span className="font-medium w-32">Meeting Code:</span>
                                <code className="bg-white px-3 py-1 rounded border text-gray-800 font-mono">
                                    {createdMeeting.meeting_code}
                                </code>
                            </div>
                            <div className="flex items-center">
                                <span className="font-medium w-32">Max Participants:</span>
                                <span>{createdMeeting.max_participants}</span>
                            </div>
                        </div>

                        {/* Meeting Link */}
                        <div className="mb-4">
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Meeting Link (Share this with others):
                            </label>
                            <div className="flex gap-2">
                                <input
                                    type="text"
                                    value={getMeetingLink()}
                                    readOnly
                                    className="flex-1 px-4 py-3 border-2 border-gray-300 rounded-lg bg-white text-gray-800 font-mono text-sm"
                                />
                                <button
                                    onClick={copyMeetingLink}
                                    className="px-6 py-3 bg-gray-700 hover:bg-gray-800 text-white rounded-lg transition-all flex items-center gap-2"
                                >
                                    {copied ? (
                                        <>
                                            <Check className="w-5 h-5" />
                                            Copied!
                                        </>
                                    ) : (
                                        <>
                                            <Copy className="w-5 h-5" />
                                            Copy
                                        </>
                                    )}
                                </button>
                            </div>
                        </div>

                        {/* Instructions */}
                        <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded">
                            <p className="text-sm text-gray-700">
                                <strong className="text-blue-700">How to share:</strong>
                                <br />
                                1. Copy the meeting link above
                                <br />
                                2. Send it to participants via email, chat, or any messaging app
                                <br />
                                3. They can click the link to join instantly!
                            </p>
                        </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex gap-4">
                        <button
                            onClick={joinMeeting}
                            className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-4 px-6 rounded-lg transition-all text-lg flex items-center justify-center gap-2"
                        >
                            <ExternalLink className="w-5 h-5" />
                            Join Meeting Now
                        </button>
                        <button
                            onClick={() => {
                                setCreatedMeeting(null);
                                setTitle('Test Meeting');
                                setDescription('');
                                setMaxParticipants(10);
                            }}
                            className="px-6 py-4 bg-gray-200 hover:bg-gray-300 text-gray-800 font-semibold rounded-lg transition-all"
                        >
                            Create Another
                        </button>
                    </div>

                    <button
                        onClick={() => navigate('/')}
                        className="w-full mt-4 text-gray-600 hover:text-gray-800 py-2"
                    >
                        Back to Home
                    </button>
                </div>
            </div>
        );
    }

    // Create meeting form
    return (
        <div className="min-h-screen bg-gradient-to-br from-purple-600 to-blue-600 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-xl w-full">
                {/* Back Button */}
                <button
                    onClick={() => navigate('/')}
                    className="flex items-center text-gray-600 hover:text-gray-800 mb-6 transition-colors"
                >
                    <ArrowLeft className="w-5 h-5 mr-2" />
                    Back to Home
                </button>

                {/* Header */}
                <div className="flex items-center mb-6">
                    <div className="w-12 h-12 bg-purple-600 rounded-lg flex items-center justify-center mr-4">
                        <Video className="w-6 h-6 text-white" />
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold text-gray-800">
                            TrueTalk Meeting Test
                        </h1>
                        <p className="text-gray-600">Create and join video meetings</p>
                    </div>
                </div>

                {/* Info Box */}
                <div className="bg-blue-50 border-l-4 border-blue-500 p-4 mb-6 rounded">
                    <p className="text-sm text-gray-700">
                        <strong className="text-blue-700">Note:</strong> You must be logged in to create or join meetings.
                        If you're not logged in, please log in first at{' '}
                        <a href="http://localhost:8000/admin/" target="_blank" rel="noopener noreferrer" className="text-blue-600 underline">
                            /admin/
                        </a>
                    </p>
                </div>

                {/* Form */}
                <form onSubmit={handleCreateMeeting} className="space-y-6">
                    <div className="bg-gray-50 rounded-lg p-6">
                        <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                            📝 Create New Meeting
                        </h2>

                        {/* Meeting Title */}
                        <div className="mb-4">
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Meeting Title
                            </label>
                            <input
                                type="text"
                                value={title}
                                onChange={(e) => setTitle(e.target.value)}
                                placeholder="e.g., Team Standup"
                                className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none text-gray-800 transition-all"
                                required
                            />
                        </div>

                        {/* Description */}
                        <div className="mb-4">
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Description (optional)
                            </label>
                            <textarea
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                                placeholder="Meeting description..."
                                rows="3"
                                className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none text-gray-800 transition-all resize-none"
                            />
                        </div>

                        {/* Max Participants */}
                        <div className="mb-4">
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Max Participants
                            </label>
                            <input
                                type="number"
                                value={maxParticipants}
                                onChange={(e) => setMaxParticipants(e.target.value)}
                                min="2"
                                max="50"
                                className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none text-gray-800 transition-all"
                            />
                        </div>

                        {/* Create Button */}
                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-4 px-6 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed text-lg"
                        >
                            {loading ? 'Creating...' : 'Create Meeting'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
