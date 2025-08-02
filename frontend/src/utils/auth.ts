/**
 * AfterIDE - Authentication Utilities
 * 
 * Utility functions for managing authentication tokens and user sessions.
 */

/**
 * Clear all authentication data and force re-login
 */
export const clearAuthData = (): void => {
  // Clear token from localStorage
  localStorage.removeItem('authToken')
  
  // Clear any other auth-related data
  sessionStorage.clear()
  
  // Force page reload to reset all state
  window.location.reload()
}

/**
 * Check if the current token is valid by making a test request
 */
export const validateToken = async (): Promise<boolean> => {
  const token = localStorage.getItem('authToken')
  
  if (!token) {
    return false
  }
  
  try {
    const response = await fetch('/api/v1/auth/me', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Accept': 'application/json'
      }
    })
    
    return response.ok
  } catch (error) {
    console.error('Token validation failed:', error)
    return false
  }
}

/**
 * Get the current authentication token
 */
export const getAuthToken = (): string | null => {
  return localStorage.getItem('authToken')
}

/**
 * Set the authentication token
 */
export const setAuthToken = (token: string): void => {
  localStorage.setItem('authToken', token)
}

/**
 * Remove the authentication token
 */
export const removeAuthToken = (): void => {
  localStorage.removeItem('authToken')
} 