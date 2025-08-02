/**
 * AfterIDE - Authentication Utilities
 * 
 * Utility functions for managing authentication state.
 */

/**
 * Clear all authentication data and redirect to login
 */
export const clearAuthData = (): void => {
  // Remove token from localStorage
  localStorage.removeItem('authToken');
  
  // Clear any other auth-related data
  sessionStorage.removeItem('authToken');
  
  // Redirect to login page
  if (window.location.pathname !== '/login') {
    window.location.href = '/login';
  }
};

/**
 * Check if user is authenticated
 */
export const isAuthenticated = (): boolean => {
  const token = localStorage.getItem('authToken');
  return !!token;
};

/**
 * Get authentication token
 */
export const getAuthToken = (): string | null => {
  return localStorage.getItem('authToken');
};

/**
 * Set authentication token
 */
export const setAuthToken = (token: string): void => {
  localStorage.setItem('authToken', token);
};

/**
 * Remove authentication token
 */
export const removeAuthToken = (): void => {
  localStorage.removeItem('authToken');
}; 