import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface FinalResponseRequest {
  content?: string; // Optional - agent can gather info using tools if empty
  user_query?: string; // Required if content is empty
}

export interface FinalResponseResponse {
  success: boolean;
  response: string;
  message?: string;
}

export interface AdditionalInfoRequest {
  query: string;
}

export interface AdditionalInfoResponse {
  success: boolean;
  info: string;
  query: string;
  message?: string;
}

export interface HealthResponse {
  status: string;
  message: string;
  version: string;
}

export const apiService = {
  // Health check
  async checkHealth(): Promise<HealthResponse> {
    const response = await api.get<HealthResponse>('/health');
    return response.data;
  },

  // Get API info
  async getApiInfo() {
    const response = await api.get('/');
    return response.data;
  },

  // Generate final response
  async generateFinalResponse(
    request: FinalResponseRequest
  ): Promise<FinalResponseResponse> {
    const response = await api.post<FinalResponseResponse>(
      '/api/v1/final-response',
      request
    );
    return response.data;
  },

  // Gather additional information
  async gatherAdditionalInfo(
    request: AdditionalInfoRequest
  ): Promise<AdditionalInfoResponse> {
    const response = await api.post<AdditionalInfoResponse>(
      '/api/v1/additional-info',
      request
    );
    return response.data;
  },
};

export default apiService;





