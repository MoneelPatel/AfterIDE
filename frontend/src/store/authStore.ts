/**
 * AfterIDE - Authentication Store
 * 
 * Zustand store for managing authentication state and operations.
 */

import { create } from 'zustand';
import { apiService } from '../services/api';
import { updateWebSocketSessions } from '../services/websocket';
import { clearAuthData } from '../utils/auth';

interface User {
  id: string;
  username: string;
  email: string;
  role: 'user' | 'admin' | 'reviewer';
}

interface AuthResponse {
  access_token: string;
  user?: User;
}

interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
  login: (username: string, password: string) => Promise<boolean>;
  register: (username: string, email: string, password: string) => Promise<boolean>;
  logout: () => void;
  setToken: (token: string) => void;
  initialize: () => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  isAuthenticated: false,
  user: null,
  token: null,
  
  login: async (username: string, password: string) => {
    try {
      console.log('🔐 Attempting login for user:', username);
      const data = await apiService.login(username, password) as any;
      
      console.log('✅ Login API response:', { 
        hasToken: !!data.access_token, 
        hasUser: !!data.user,
        userData: data.user 
      });
      
      // Clear any auth redirect flags
      sessionStorage.removeItem('auth_redirected');
      
      // Set authentication state first
      const authState = {
        isAuthenticated: true, 
        user: data.user || { id: '1', username, email: '', role: 'user' as const }, 
        token: data.access_token 
      };
      
      console.log('🔧 Setting auth state:', authState);
      set(authState);
      
      // Store token in localStorage
      localStorage.setItem('authToken', data.access_token);
      console.log('💾 Token stored in localStorage');
      
      // Update WebSocket sessions with new user session after a small delay
      // to ensure the authentication state is properly set
      console.log('Login successful, updating WebSocket sessions');
      setTimeout(async () => {
        try {
          await updateWebSocketSessions();
        } catch (error) {
          console.error('Failed to update WebSocket sessions after login:', error);
        }
      }, 100);
      
      console.log('✅ Login completed successfully');
      return true;
    } catch (error) {
      console.error('❌ Login error:', error);
      return false;
    }
  },
  
  register: async (username: string, email: string, password: string) => {
    try {
      const data = await apiService.register(username, email, password) as AuthResponse;
      
      // Set authentication state first
      set({ 
        isAuthenticated: true, 
        user: data.user || { id: '1', username, email: '', role: 'user' as const }, 
        token: data.access_token 
      });
      
      // Store token in localStorage
      localStorage.setItem('authToken', data.access_token);
      
      // Update WebSocket sessions with new user session after a small delay
      console.log('Registration successful, updating WebSocket sessions');
      setTimeout(async () => {
        try {
          await updateWebSocketSessions();
        } catch (error) {
          console.error('Failed to update WebSocket sessions after registration:', error);
        }
      }, 100);
      
      return true;
    } catch (error) {
      console.error('Registration error:', error);
      return false;
    }
  },
  
  logout: () => {
    const { token } = get();
    
    // Call logout API if we have a token
    if (token) {
      apiService.logout(token).catch(error => {
        console.error('Logout API call failed:', error);
      });
    }
    
    localStorage.removeItem('authToken');
    set({ isAuthenticated: false, user: null, token: null });
    
    // Update WebSocket sessions
    updateWebSocketSessions().catch(error => {
      console.error('Failed to update WebSocket sessions on logout:', error);
    });
  },
  
  setToken: (token: string) => {
    localStorage.setItem('authToken', token);
    set({ token, isAuthenticated: true });
  },
  
  clearAuth: () => {
    clearAuthData();
  },
  
  initialize: () => {
    const token = localStorage.getItem('authToken');
    if (token) {
      // Try to get current user info
      apiService.getCurrentUser(token)
        .then((data: any) => {
          set({ 
            isAuthenticated: true, 
            user: data.user || { id: '1', username: 'user', email: '', role: 'user' as const }, 
            token 
          });
          updateWebSocketSessions();
        })
        .catch(error => {
          console.error('Failed to get current user:', error);
          // Only clear token if it's a 401 error (invalid token)
          // Don't clear for network errors or other issues
          if (error.message && error.message.includes('401')) {
            console.log('Invalid token detected, clearing authentication');
            localStorage.removeItem('authToken');
            set({ isAuthenticated: false, user: null, token: null });
          } else {
            console.log('Network error or other issue, keeping token for now');
            // Keep the token but mark as not authenticated
            set({ isAuthenticated: false, user: null, token });
          }
        });
    }
  }
})); 