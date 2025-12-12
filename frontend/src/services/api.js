import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/meeting';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
    withCredentials: true,
});

export const meetingAPI = {
    createMeeting: async (data) => {
        const response = await api.post('/meetings/', data);
        return response.data;
    },

    getMeeting: async (meetingId) => {
        const response = await api.get(`/meetings/${meetingId}/`);
        return response.data;
    },

    joinMeeting: async (meetingId) => {
        const response = await api.post(`/meetings/${meetingId}/join/`);
        return response.data;
    },
};

export default api;
