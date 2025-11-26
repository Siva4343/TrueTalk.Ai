import { useState } from 'react';
import Sidebar from '../components/Sidebar';
import ChatWindow from '../components/ChatWindow';

export default function ChatPage() {
    const [currentChat, setCurrentChat] = useState(null);

    return (
        <div className="h-screen flex">
            <Sidebar onSelectChat={setCurrentChat} currentChat={currentChat} />
            <ChatWindow chat={currentChat} />
        </div>
    );
}
