/**
 * Session utility functions for WebSocket connections
 */

/**
 * Get user session ID from auth store
 */
export const getUserSessionId = (): string => {
  const token = localStorage.getItem('authToken');
  if (!token) {
    // Fallback to default session for unauthenticated users
    return 'default-session';
  }
  
  // For now, we'll use a simple hash of the token as session ID
  // This will be replaced by the actual user session ID from the backend
  let hash = 0;
  for (let i = 0; i < token.length; i++) {
    const char = token.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32-bit integer
  }
  return `user-${Math.abs(hash)}`;
};

/**
 * Get authentication token
 */
export const getAuthToken = (): string | null => {
  return localStorage.getItem('authToken');
}; 