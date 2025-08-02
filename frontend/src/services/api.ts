/**
 * AfterIDE - API Service
 * 
 * Centralized API service for making HTTP requests to the backend.
 */

// Get the API base URL based on environment
const getApiBaseUrl = (): string => {
  console.log('🔍 getApiBaseUrl called');
  console.log('🔍 VITE_API_URL from env:', import.meta.env.VITE_API_URL);
  console.log('🔍 window.location.protocol:', window.location.protocol);
  console.log('🔍 window.location.hostname:', window.location.hostname);
  console.log('🔍 import.meta.env.DEV:', import.meta.env.DEV);
  
  // Check if we have a production API URL configured
  const apiBaseUrl = import.meta.env.VITE_API_URL;
  
  if (apiBaseUrl) {
    console.log('🔍 Using VITE_API_URL:', apiBaseUrl);
    // Ensure HTTPS is used in production
    if (window.location.protocol === 'https:' && apiBaseUrl.startsWith('http://')) {
      console.warn('Mixed content detected: Converting HTTP API URL to HTTPS');
      const httpsUrl = apiBaseUrl.replace('http://', 'https://');
      console.log('🔍 Converted to HTTPS:', httpsUrl);
      return httpsUrl;
    }
    console.log('🔍 Returning apiBaseUrl as-is:', apiBaseUrl);
    return apiBaseUrl;
  }
  
  // Check if we're running on Railway (production)
  if (window.location.hostname.includes('railway.app')) {
    console.log('🔍 Running on Railway, using hardcoded HTTPS URL');
    // Use the backend Railway URL for API calls - ensure HTTPS
    return 'https://sad-chess-production.up.railway.app/api/v1';
  }
  
  // Check if we're in development mode
  if (import.meta.env.DEV) {
    console.log('🔍 Development mode, using relative URL');
    // In development, use relative URLs (will be proxied by Vite)
    return '/api/v1';
  }
  
  // Fallback for production without environment variable
  console.log('🔍 Fallback: using hardcoded HTTPS URL');
  // Use the backend Railway URL as default - ensure HTTPS
  return 'https://sad-chess-production.up.railway.app/api/v1';
};

// Create API service with proper base URL
class ApiService {
  private version: string;
  private instanceId: string;

  constructor() {
    console.log('🔍 ApiService constructor called');
    this.version = Date.now().toString(); // Force new instance
    this.instanceId = Math.random().toString(36).substr(2, 9); // Unique instance ID
    console.log('🔍 ApiService version:', this.version);
    console.log('🔍 ApiService instance ID:', this.instanceId);
  }

  private getBaseUrl(): string {
    return getApiBaseUrl();
  }

  private getFullUrl(endpoint: string): string {
    const baseUrl = this.getBaseUrl();
    if (baseUrl) {
      return `${baseUrl}${endpoint}`;
    }
    return endpoint;
  }

  async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = this.getFullUrl(endpoint);
    console.log('🔍 API request to:', url);
    console.log('🔍 Base URL:', this.getBaseUrl());
    console.log('🔍 Endpoint:', endpoint);
    console.log('🔍 Instance ID:', this.instanceId);
    
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0',
        'X-Request-ID': Date.now().toString(), // Cache busting
        'X-Instance-ID': this.instanceId, // Track which instance made the request
        ...options.headers,
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('API request failed:', response.status, errorText);
      console.error('Request URL:', url);
      console.error('Request headers:', options.headers);
      
      // Handle 401 Unauthorized errors globally
      if (response.status === 401) {
        console.warn('Authentication failed, clearing invalid token');
        console.warn('Current pathname:', window.location.pathname);
        
        // Check if we've already redirected to prevent infinite loops
        const hasRedirected = sessionStorage.getItem('auth_redirected');
        
        // Only clear token and redirect if we're not already on the login page and haven't redirected yet
        if (window.location.pathname !== '/login' && !hasRedirected) {
          console.warn('Redirecting to login page...');
          sessionStorage.setItem('auth_redirected', 'true');
          localStorage.removeItem('authToken');
          
          // Show user-friendly error message
          const errorMessage = 'Your session has expired. Please log in again.';
          
          // Force page reload to redirect to login
          alert(errorMessage);
          window.location.href = '/login';
        } else {
          console.warn('Already on login page or already redirected, not redirecting again');
        }
        
        throw new Error('Authentication failed: Invalid token');
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