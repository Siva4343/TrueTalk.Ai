import { useState } from 'react';
import { X, Send } from 'lucide-react';

export default function ChatSidebar({ messages, onSendMessage, onClose, currentUserId, userName }) {
    const [input, setInput] = useState('');

    const handleSend = (e) => {
        e.preventDefault();
        if (input.trim()) {
            onSendMessage(input);
            setInput('');
        }
    };

    return (
        <div className="w-80 bg-[#292929] border-l border-[#3d3d3d] flex flex-col">
            {/* Header */}
            <div className="p-4 border-b border-[#3d3d3d] flex items-center justify-between">
                <h2 className="font-semibold text-white text-sm">Chat</h2>
                <button
                    onClick={onClose}
                    className="hover:bg-[#3d3d3d] p-1 rounded transition-all text-gray-400 hover:text-white"
                >
                    <X className="w-4 h-4" />
                </button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {messages.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full text-center">
                        <p className="text-gray-500 text-sm">No messages yet</p>
                        <p className="text-gray-600 text-xs mt-1">Start the conversation</p>
                    </div>
                ) : (
                    messages.map((msg, index) => {
                        const isOwn = msg.senderId === currentUserId;
                        return (
                            <div key={index} className="space-y-1">
                                {!isOwn && (
                                    <div className="text-xs text-gray-400 font-medium">
                                        {msg.sender || 'Guest'}
                                    </div>
                                )}
                                <div
                                    className={`${isOwn
                                            ? 'bg-[#5b5fc7] ml-8'
                                            : 'bg-[#3d3d3d] mr-8'
                                        } rounded-lg p-3`}
                                >
                                    <div className="text-sm text-white break-words">
                                        {msg.content}
                                    </div>
                                    <div className="text-xs text-gray-400 mt-1">
                                        {new Date(msg.timestamp).toLocaleTimeString('en-US', {
                                            hour: '2-digit',
                                            minute: '2-digit',
                                        })}
                                    </div>
                                </div>
                            </div>
                        );
                    })
                )}
            </div>

            {/* Input */}
            <form onSubmit={handleSend} className="p-4 border-t border-[#3d3d3d]">
                <div className="flex gap-2">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Type a message"
                        className="flex-1 bg-[#3d3d3d] border border-[#4d4d4d] rounded px-3 py-2 outline-none focus:border-[#5b5fc7] text-white placeholder-gray-500 text-sm transition-all"
                    />
                    <button
                        type="submit"
                        disabled={!input.trim()}
                        className="bg-[#5b5fc7] hover:bg-[#4d52b8] disabled:opacity-50 disabled:cursor-not-allowed text-white p-2 rounded transition-all"
                    >
                        <Send className="w-4 h-4" />
                    </button>
                </div>
            </form>
        </div>
    );
}
