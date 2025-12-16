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

    // Participant moderation actions
    muteParticipant: async (meetingId, participantId) => {
        const response = await api.post(`/meetings/${meetingId}/participants/${participantId}/mute/`);
        return response.data;
    },

    removeParticipant: async (meetingId, participantId) => {
        const response = await api.post(`/meetings/${meetingId}/participants/${participantId}/remove/`);
        return response.data;
    },

    makeCohost: async (meetingId, participantId) => {
        const response = await api.post(`/meetings/${meetingId}/participants/${participantId}/make_cohost/`);
        return response.data;
    },

    admitParticipant: async (meetingId, participantId) => {
        const response = await api.post(`/meetings/${meetingId}/participants/${participantId}/admit/`);
        return response.data;
    },

    muteAll: async (meetingId) => {
        const response = await api.post(`/meetings/${meetingId}/participants/mute_all/`);
        return response.data;
    },
};

export default api;
