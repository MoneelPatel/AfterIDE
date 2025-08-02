import { create } from 'zustand'
import { updateWebSocketSessions } from '../services/websocket'
import apiService from '../services/api'

interface User {
  id: string
  username: string
  email: string
  role: 'user' | 'admin' | 'reviewer'
}

interface AuthResponse {
  access_token: string
  user?: User
}

interface AuthState {
  isAuthenticated: boolean
  user: User | null
  token: string | null
  login: (username: string, password: string) => Promise<boolean>
  register: (username: string, email: string, password: string) => Promise<boolean>
  logout: () => void
  setToken: (token: string) => void
  initialize: () => void
}

export const useAuthStore = create<AuthState>((set, get) => ({
  isAuthenticated: false,
  user: null,
  token: null,
  login: async (username: string, password: string) => {
    try {
      const data = await apiService.login(username, password) as AuthResponse
      
      localStorage.setItem('authToken', data.access_token)
      set({ 
        isAuthenticated: true, 
        user: data.user || { id: '1', username, email: '', role: 'user' as const }, 
        token: data.access_token 
      })
      
      // Update WebSocket sessions with new user session
      console.log('Login successful, updating WebSocket sessions');
      updateWebSocketSessions()
      
      return true
    } catch (error) {
      console.error('Login error:', error)
      return false
    }
  },
  register: async (username: string, email: string, password: string) => {
    try {
      const data = await apiService.register(username, email, password) as AuthResponse
      
      localStorage.setItem('authToken', data.access_token)
      set({ 
        isAuthenticated: true, 
        user: data.user || { id: '1', username, email, role: 'user' as const }, 
        token: data.access_token 
      })
      
      // Update WebSocket sessions with new user session
      console.log('Registration successful, updating WebSocket sessions');
      updateWebSocketSessions()
      
      return true
    } catch (error) {
      console.error('Registration error:', error)
      return false
    }
  },
  logout: () => {
    const { token } = get()
    
    // Call logout API if we have a token
    if (token) {
      apiService.logout(token).catch(error => {
        console.error('Logout API call failed:', error)
      })
    }
    
    localStorage.removeItem('authToken')
    set({ isAuthenticated: false, user: null, token: null })
    
    // Update WebSocket sessions
    updateWebSocketSessions()
  },
  setToken: (token: string) => {
    localStorage.setItem('authToken', token)
    set({ token, isAuthenticated: true })
  },
  initialize: () => {
    const token = localStorage.getItem('authToken')
    if (token) {
      // Try to get current user info
      apiService.getCurrentUser(token)
        .then((data: any) => {
          set({ 
            isAuthenticated: true, 
            user: data.user || { id: '1', username: 'user', email: '', role: 'user' as const }, 
            token 
          })
          updateWebSocketSessions()
        })
        .catch(error => {
          console.error('Failed to get current user:', error)
          // Token might be invalid, clear it
          localStorage.removeItem('authToken')
          set({ isAuthenticated: false, user: null, token: null })
        })
    }
  }
})) 