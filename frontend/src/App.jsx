import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import CreateMeeting from './pages/CreateMeeting';
import JoinMeeting from './pages/JoinMeeting';
import MeetingRoom from './pages/MeetingRoom';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/create" element={<CreateMeeting />} />
        <Route path="/join" element={<JoinMeeting />} />
        {/* ADD THIS LINE - This is what's missing! */}
        <Route path="/join/:meetingId" element={<JoinMeeting />} />
        <Route path="/meeting/:meetingId" element={<MeetingRoom />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;