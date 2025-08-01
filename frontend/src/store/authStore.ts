import { create } from 'zustand'
import { updateWebSocketSessions } from '../services/websocket'

interface User {
  id: string
  username: string
  email: string
  role: 'user' | 'admin' | 'reviewer'
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
      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      })

      if (response.ok) {
        const data = await response.json()
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
      } else {
        console.error('Login failed:', response.status, response.statusText)
        return false
      }
    } catch (error) {
      console.error('Login error:', error)
      return false
    }
  },
  register: async (username: string, email: string, password: string) => {
    try {
      const response = await fetch('/api/v1/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          username, 
          email, 
          password, 
          confirm_password: password 
        }),
      })

      if (response.ok) {
        const data = await response.json()
        console.log('Registration successful:', data)
        return true
      } else {
        const errorData = await response.json()
        console.error('Registration failed:', response.status, errorData)
        return false
      }
    } catch (error) {
      console.error('Registration error:', error)
      return false
    }
  },
  logout: () => {
    console.log('Logging out, updating WebSocket sessions');
    localStorage.removeItem('authToken')
    set({ isAuthenticated: false, user: null, token: null })
    
    // Update WebSocket sessions to use default session
    updateWebSocketSessions()
  },
  setToken: (token: string) => {
    set({ token })
  },
  initialize: () => {
    const token = localStorage.getItem('authToken')
    if (token) {
      console.log('Initializing auth store with existing token');
      set({ 
        isAuthenticated: true, 
        token,
        user: { id: '1', username: 'admin', email: 'admin@example.com', role: 'admin' as const }
      })
      
      // Update WebSocket sessions with stored token
      updateWebSocketSessions()
    }
  },
})) 