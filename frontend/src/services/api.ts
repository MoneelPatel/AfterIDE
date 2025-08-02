/**
 * AfterIDE - API Service
 * 
 * Centralized API service for making HTTP requests to the backend.
 */

// Get the API base URL based on environment
const getApiBaseUrl = (): string => {
  // Check if we have a production API URL configured
  const apiBaseUrl = import.meta.env.VITE_API_URL;
  
  if (apiBaseUrl) {
    // Use the configured API URL for production
    return apiBaseUrl;
  }
  
  // Check if we're running on Railway (production)
  if (window.location.hostname.includes('railway.app')) {
    // Use the backend Railway URL for API calls - ensure HTTPS
    return 'https://sad-chess-production.up.railway.app/api/v1';
  }
  
  // Check if we're in development mode
  if (import.meta.env.DEV) {
    // In development, use relative URLs (will be proxied by Vite)
    return '/api/v1';
  }
  
  // Fallback for production without environment variable
  // Use the backend Railway URL as default - ensure HTTPS
  return 'https://sad-chess-production.up.railway.app/api/v1';
};

// Create API service with proper base URL
class ApiService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = getApiBaseUrl();
  }

  private getFullUrl(endpoint: string): string {
    if (this.baseUrl) {
      return `${this.baseUrl}${endpoint}`;
    }
    return endpoint;
  }

  async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = this.getFullUrl(endpoint);
    
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('API request failed:', response.status, errorText);
      
      // Handle 401 Unauthorized errors globally
      if (response.status === 401) {
        console.warn('Authentication failed, clearing invalid token');
        localStorage.removeItem('authToken');
        // Force page reload to redirect to login
        window.location.reload();
      }
      
      throw new Error(`API request failed: ${response.status} ${response.statusText}`);
    }

    // Check if response is JSON
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return response.json();
    } else {
      const text = await response.text();
      console.error('Unexpected response type:', contentType, text);
      throw new Error('Expected JSON response but got: ' + contentType);
    }
  }

  // Auth endpoints
  async login(username: string, password: string) {
    return this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
  }

  async register(username: string, email: string, password: string) {
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ 
        username, 
        email, 
        password,
        confirm_password: password 
      }),
    });
  }

  async logout(token: string) {
    return this.request('/auth/logout', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  }

  // User endpoints
  async getCurrentUser(token: string) {
    return this.request('/auth/me', {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  }

  // Session endpoints
  async createSession(token: string, sessionData: any) {
    return this.request('/sessions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(sessionData),
    });
  }

  async getSessions(token: string) {
    return this.request('/sessions', {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  }

  // File endpoints
  async getFiles(token: string, sessionId: string) {
    return this.request(`/files/${sessionId}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  }

  async saveFile(token: string, sessionId: string, fileData: any) {
    return this.request(`/files/${sessionId}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(fileData),
    });
  }

  // Execution endpoints
  async executeCode(token: string, sessionId: string, codeData: any) {
    return this.request(`/executions/${sessionId}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(codeData),
    });
  }

  // Submission endpoints
  async createSubmission(token: string, submissionData: any) {
    return this.request('/submissions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(submissionData),
    });
  }

  async getSubmissions(token: string, params?: any) {
    const queryString = params ? `?${new URLSearchParams(params).toString()}` : '';
    return this.request(`/submissions${queryString}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  }

  async getPendingSubmissions(token: string) {
    return this.request('/submissions/pending', {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  }

  async getSubmission(token: string, id: string) {
    return this.request(`/submissions/${id}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  }

  async reviewSubmission(token: string, id: string, review: any) {
    return this.request(`/submissions/${id}/review`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(review),
    });
  }

  async updateSubmission(token: string, id: string, data: any) {
    return this.request(`/submissions/${id}`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
  }

  async deleteSubmission(token: string, id: string) {
    return this.request(`/submissions/${id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  }

  async getSubmissionStats(token: string) {
    return this.request('/submissions/stats/overview', {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  }

  async getAvailableReviewers(token: string) {
    return this.request('/submissions/reviewers', {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  }

  // Workspace endpoints
  async getWorkspaceFiles(token: string, sessionId: string, directory: string = '/') {
    return this.request(`/workspace/files?session_id=${sessionId}&directory=${encodeURIComponent(directory)}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  }

  async createWorkspaceFile(token: string, sessionId: string, fileData: any) {
    return this.request('/workspace/files', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ ...fileData, session_id: sessionId }),
    });
  }

  async updateWorkspaceFile(token: string, sessionId: string, filepath: string, content: string) {
    return this.request('/workspace/files', {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({
        session_id: sessionId,
        filepath,
        content,
      }),
    });
  }

  async deleteWorkspaceFile(token: string, sessionId: string, filepath: string) {
    return this.request('/workspace/files', {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({
        session_id: sessionId,
        filepath,
      }),
    });
  }
}

// Export singleton instance
export const apiService = new ApiService();
export default apiService; 