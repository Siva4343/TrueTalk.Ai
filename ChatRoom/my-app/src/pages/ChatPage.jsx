import { useState } from 'react';
import Sidebar from '../components/Sidebar';
import ChatWindow from '../components/ChatWindow';
import ProfileSidebar from '../components/ProfileSidebar';

export default function ChatPage() {
    const [currentChat, setCurrentChat] = useState(null);
    const [showSelfProfile, setShowSelfProfile] = useState(false);
    const [selfProfileUser, setSelfProfileUser] = useState(null);

    const handleShowSelfProfile = (user) => {
        setSelfProfileUser(user);
        setShowSelfProfile(true);
    };

    return (
        <div className="h-screen flex relative">
            <Sidebar
                onSelectChat={setCurrentChat}
                currentChat={currentChat}
                onShowProfile={handleShowSelfProfile}
            />
            <ChatWindow chat={currentChat} />

            {showSelfProfile && selfProfileUser && (
                <ProfileSidebar
                    user={selfProfileUser}
                    messages={[]}
                    onClose={() => setShowSelfProfile(false)}
                />
            )}
        </div>
    );
}
