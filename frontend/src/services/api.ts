/**
 * AfterIDE - API Service
 * 
 * Centralized API service for making HTTP requests to the backend.
 */

import { SubmissionStatus } from '../types/submissions';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

interface ApiResponse<T> {
  data: T;
  error?: string;
}

class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    
    // Get auth token from localStorage (match the key used in authStore)
    const token = localStorage.getItem('authToken');
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` }),
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return { data };
    } catch (error) {
      return {
        data: null as T,
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      };
    }
  }

  // Auth endpoints
  async login(credentials: { username: string; password: string }) {
    return this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
  }

  async register(userData: { username: string; email: string; password: string }) {
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  async getCurrentUser() {
    return this.request('/auth/me');
  }

  // Session endpoints
  async getSessions() {
    return this.request('/sessions/');
  }

  async createSession(sessionData: { name: string; description?: string }) {
    return this.request('/sessions/', {
      method: 'POST',
      body: JSON.stringify(sessionData),
    });
  }

  async getSession(sessionId: string) {
    return this.request(`/sessions/${sessionId}`);
  }

  // File endpoints
  async getFiles(sessionId: string) {
    return this.request(`/files/?session_id=${sessionId}`);
  }

  async getFile(fileId: string) {
    return this.request(`/files/${fileId}`);
  }

  async updateFile(fileId: string, content: string) {
    return this.request(`/files/${fileId}`, {
      method: 'PUT',
      body: JSON.stringify({ content }),
    });
  }

  // Submission endpoints
  async createSubmission(submissionData: {
    title: string;
    description?: string;
    file_id: string;
    reviewer_username?: string;
  }) {
    return this.request('/submissions/', {
      method: 'POST',
      body: JSON.stringify(submissionData),
    });
  }

  async getAvailableReviewers() {
    return this.request('/submissions/reviewers');
  }

  async getSubmissions(params?: {
    page?: number;
    per_page?: number;
    status_filter?: string;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.append('page', params.page.toString());
    if (params?.per_page) searchParams.append('per_page', params.per_page.toString());
    if (params?.status_filter) searchParams.append('status_filter', params.status_filter);

    const queryString = searchParams.toString();
    return this.request(`/submissions/?${queryString}`);
  }

  async getPendingSubmissions() {
    return this.request('/submissions/pending');
  }

  async getSubmission(submissionId: string) {
    return this.request(`/submissions/${submissionId}`);
  }

  async reviewSubmission(
    submissionId: string,
    reviewData: {
      status: SubmissionStatus;
      review_comments?: string;
      review_metadata?: Record<string, any>;
    }
  ) {
    return this.request(`/submissions/${submissionId}/review`, {
      method: 'PUT',
      body: JSON.stringify(reviewData),
    });
  }

  async updateSubmission(
    submissionId: string,
    updateData: {
      title?: string;
      description?: string;
    }
  ) {
    return this.request(`/submissions/${submissionId}`, {
      method: 'PUT',
      body: JSON.stringify(updateData),
    });
  }

  async deleteSubmission(submissionId: string) {
    return this.request(`/submissions/${submissionId}`, {
      method: 'DELETE',
    });
  }

  async getSubmissionStats() {
    return this.request('/submissions/stats/overview');
  }

  // Workspace endpoints
  async getWorkspaceFiles(sessionId: string, directory: string = '/') {
    return this.request(`/workspace/files?session_id=${sessionId}&directory=${encodeURIComponent(directory)}`);
  }

  async createWorkspaceFile(sessionId: string, fileData: {
    filename: string;
    filepath: string;
    content: string;
  }) {
    return this.request('/workspace/files', {
      method: 'POST',
      body: JSON.stringify({ ...fileData, session_id: sessionId }),
    });
  }

  async updateWorkspaceFile(sessionId: string, filepath: string, content: string) {
    return this.request('/workspace/files', {
      method: 'PUT',
      body: JSON.stringify({
        session_id: sessionId,
        filepath,
        content,
      }),
    });
  }

  async deleteWorkspaceFile(sessionId: string, filepath: string) {
    return this.request('/workspace/files', {
      method: 'DELETE',
      body: JSON.stringify({
        session_id: sessionId,
        filepath,
      }),
    });
  }
}

// Export singleton instance
export const apiService = new ApiService(API_BASE_URL);
export default apiService; 