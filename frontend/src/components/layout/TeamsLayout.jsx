import { Outlet } from 'react-router-dom';
import { useState } from 'react';
import { 
  Home, 
  MessageSquare, 
  Users, 
  Calendar, 
  Phone, 
  File, 
  Settings,
  Bell,
  Search,
  ChevronDown
} from 'lucide-react';

export default function TeamsLayout() {
    const [activeTab, setActiveTab] = useState('activity');

    const navigationItems = [
        { id: 'activity', label: 'Activity', icon: Home },
        { id: 'chat', label: 'Chat', icon: MessageSquare },
        { id: 'teams', label: 'Teams', icon: Users },
        { id: 'calendar', label: 'Calendar', icon: Calendar },
        { id: 'calls', label: 'Calls', icon: Phone },
        { id: 'files', label: 'Files', icon: File },
    ];

    return (
        <div className="h-screen flex bg-gray-50">
            {/* Sidebar */}
            <div className="w-16 bg-gray-900 flex flex-col items-center py-4">
                {/* App Icon */}
                <div className="w-12 h-12 bg-[#464775] rounded-lg flex items-center justify-center mb-8">
                    <div className="w-6 h-6 bg-white rounded-sm"></div>
                </div>

                {/* Navigation */}
                <nav className="flex-1 space-y-6">
                    {navigationItems.map((item) => {
                        const Icon = item.icon;
                        return (
                            <button
                                key={item.id}
                                onClick={() => setActiveTab(item.id)}
                                className={`p-3 rounded-lg ${activeTab === item.id ? 'bg-gray-800 text-white' : 'text-gray-400 hover:text-white hover:bg-gray-800'}`}
                                title={item.label}
                            >
                                <Icon className="w-6 h-6" />
                            </button>
                        );
                    })}
                </nav>

                {/* Bottom Icons */}
                <div className="space-y-4">
                    <button className="p-3 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg">
                        <Bell className="w-6 h-6" />
                    </button>
                    <button className="p-3 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg">
                        <Settings className="w-6 h-6" />
                    </button>
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 flex flex-col">
                {/* Top Bar */}
                <header className="h-16 bg-white border-b border-gray-200 px-6 flex items-center justify-between">
                    <div className="flex items-center">
                        <h1 className="text-xl font-semibold text-gray-800">TeamsMeet</h1>
                        <div className="ml-6 flex items-center bg-gray-100 rounded-lg px-4 py-2">
                            <Search className="w-5 h-5 text-gray-400 mr-2" />
                            <input
                                type="text"
                                placeholder="Search"
                                className="bg-transparent outline-none text-gray-700 placeholder-gray-400"
                            />
                        </div>
                    </div>

                    <div className="flex items-center space-x-4">
                        <button className="p-2 hover:bg-gray-100 rounded-full">
                            <div className="w-8 h-8 bg-gradient-to-br from-[#464775] to-[#5b5fc7] rounded-full flex items-center justify-center text-white font-medium">
                                U
                            </div>
                        </button>
                    </div>
                </header>

                {/* Page Content */}
                <main className="flex-1 overflow-auto p-6">
                    <Outlet />
                </main>
            </div>
        </div>
    );
}