import apiClient from './client';

export const urlAPI = {
  shortenURL: async (urlData) => {
    const response = await apiClient.post('/api/urls/shorten', urlData);
    return response.data;
  },

  getUserURLs: async (userId, skip = 0, limit = 100) => {
    const response = await apiClient.get(`/api/urls/user/${userId}`, {
      params: { skip, limit }
    });
    return response.data;
  },

  deleteURL: async (shortCode) => {
    const response = await apiClient.delete(`/api/urls/${shortCode}`);
    return response.data;
  },

  getAnalytics: async (shortCode) => {
    const response = await apiClient.get(`/api/analytics/${shortCode}`);
    return response.data;
  },

  getUserAnalyticsSummary: async (userId) => {
    const response = await apiClient.get(`/api/analytics/user/${userId}/summary`);
    return response.data;
  }
};
