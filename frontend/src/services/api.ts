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
  console.log('🔍 import.meta.env.PROD:', import.meta.env.PROD);
  
  // Check if we have a production API URL configured
  let apiBaseUrl = import.meta.env.VITE_API_URL;
  
  if (apiBaseUrl) {
    console.log('🔍 Using VITE_API_URL:', apiBaseUrl);
    
    // Force HTTPS for any HTTP URLs, especially in production
    if (apiBaseUrl.startsWith('http://')) {
      console.warn('Converting HTTP API URL to HTTPS');
      apiBaseUrl = apiBaseUrl.replace('http://', 'https://');
      console.log('🔍 Converted to HTTPS:', apiBaseUrl);
    }
    
    return apiBaseUrl;
  }
  
  // Check if we're running on Railway (production)
  if (window.location.hostname.includes('railway.app') || import.meta.env.PROD) {
    console.log('🔍 Running on Railway or in production, using HTTPS sad-chess backend');
    // Always use HTTPS for Railway deployments
    return 'https://sad-chess-production.up.railway.app/api/v1';
  }
  
  // Check if we're in development mode
  if (import.meta.env.DEV) {
    console.log('🔍 Development mode, using relative URL');
    // In development, use relative URLs (will be proxied by Vite)
    return '/api/v1';
  }
  
  // Fallback for production without environment variable
  console.log('🔍 Fallback: using HTTPS sad-chess backend');
  // Always use HTTPS for production fallback
  return 'https://sad-chess-production.up.railway.app/api/v1';
};

// Utility to force HTTPS for all API requests to sad-chess-production
function forceHttps(url: string): string {
  console.log('🔍 forceHttps input:', url);
  
  // Force HTTPS for any HTTP URLs
  if (url.startsWith('http://')) {
    const httpsUrl = url.replace('http://', 'https://');
    console.log('🔍 forceHttps converted HTTP to HTTPS:', httpsUrl);
    return httpsUrl;
  }
  
  // Also handle sad-chess-production specifically - ensure it's always HTTPS
  if (url.includes('sad-chess-production.up.railway.app')) {
    const httpsUrl = url.replace(/^http:\/\/sad-chess-production\.up\.railway\.app/, 'https://sad-chess-production.up.railway.app');
    if (httpsUrl !== url) {
      console.log('🔍 forceHttps converted sad-chess URL to HTTPS:', httpsUrl);
      return httpsUrl;
    }
  }
  
  // Additional safety: if we're on HTTPS page, ensure all URLs are HTTPS
  if (window.location.protocol === 'https:' && url.startsWith('http://')) {
    const httpsUrl = url.replace('http://', 'https://');
    console.log('🔍 forceHttps: HTTPS page detected, converting to HTTPS:', httpsUrl);
    return httpsUrl;
  }
  
  console.log('🔍 forceHttps no conversion needed:', url);
  return url;
}

// Create API service with proper base URL
class ApiService {
  private version: string;
  private instanceId: string;

  constructor() {
    console.log('🔍 ApiService constructor called');
    this.version = `v${Date.now()}`; // Force new instance with timestamp
    this.instanceId = Math.random().toString(36).substr(2, 9); // Unique instance ID
    console.log('🔍 ApiService version:', this.version);
    console.log('🔍 ApiService instance ID:', this.instanceId);
    console.log('🔍 ApiService getFileByPath method signature:', this.getFileByPath.toString());
  }

  private getBaseUrl(): string {
    return getApiBaseUrl();
  }

  private getFullUrl(endpoint: string): string {
    const baseUrl = this.getBaseUrl();
    if (baseUrl) {
      let fullUrl = `${baseUrl}${endpoint}`;
      
      console.log('🔍 getFullUrl - baseUrl:', baseUrl);
      console.log('🔍 getFullUrl - endpoint:', endpoint);
      console.log('🔍 getFullUrl - initial fullUrl:', fullUrl);
      
      // Final safety check: ensure HTTPS when page is loaded over HTTPS
      if (window.location.protocol === 'https:' && fullUrl.startsWith('http://')) {
        console.warn('Final HTTPS enforcement: converting HTTP to HTTPS');
        fullUrl = fullUrl.replace('http://', 'https://');
        console.log('🔍 Final URL after HTTPS enforcement:', fullUrl);
      }
      
      // Additional check for Railway domains
      if (fullUrl.includes('railway.app') && fullUrl.startsWith('http://')) {
        console.warn('Railway domain detected with HTTP, converting to HTTPS');
        fullUrl = fullUrl.replace('http://', 'https://');
        console.log('🔍 Final URL after Railway HTTPS enforcement:', fullUrl);
      }
      
      console.log('🔍 getFullUrl - final fullUrl:', fullUrl);
      return fullUrl;
    }
    return endpoint;
  }

  async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    let url = this.getFullUrl(endpoint);
    console.log('🔍 Original URL before forceHttps:', url);
    url = forceHttps(url); // Ensure HTTPS for all requests
    console.log('🔍 Final URL after forceHttps:', url);
    console.log('🔍 API request to:', url);
    console.log('🔍 Base URL:', this.getBaseUrl());
    console.log('🔍 Endpoint:', endpoint);
    console.log('🔍 Instance ID:', this.instanceId);
    console.log('🔍 Request method:', options.method || 'GET');
    console.log('🔍 Request headers:', options.headers);
    
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

  async createCodeReview(token: string, submissionData: any) {
    return this.request('/code-reviews', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(submissionData),
    });
  }

  async getSubmissions(token: string, params?: any) {
    // Filter out undefined values from params
    const cleanParams = params ? Object.fromEntries(
      Object.entries(params).filter(([_, value]) => value !== undefined && value !== 'undefined')
    ) as Record<string, string> : {};
    
    const queryString = Object.keys(cleanParams).length > 0 ? `?${new URLSearchParams(cleanParams).toString()}` : '';
    return this.request(`/submissions/all${queryString}`, {
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
    return this.request('/submissions/stats', {
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

  async getFileByPath(token: string, filepath: string) {
    // Add cache-busting parameter to force new endpoint usage
    const cacheBuster = Date.now();
    const endpoint = `/submissions/file-by-path/${encodeURIComponent(filepath)}?cb=${cacheBuster}`;
    console.log('🔍 getFileByPath called with:', { token: token ? 'present' : 'missing', filepath, endpoint });
    console.log('🔍 Full URL will be:', `${this.getBaseUrl()}${endpoint}`);
    return this.request(endpoint, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  }

  async getFileByPathCodeReview(token: string, filepath: string) {
    // Use the existing submissions endpoint since code-reviews endpoint doesn't exist
    const cacheBuster = Date.now();
    const endpoint = `/submissions/file-by-path/${encodeURIComponent(filepath)}?cb=${cacheBuster}`;
    console.log('🔍 getFileByPathCodeReview called with:', { token: token ? 'present' : 'missing', filepath, endpoint });
    console.log('🔍 Full URL will be:', `${this.getBaseUrl()}${endpoint}`);
    return this.request(endpoint, {
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