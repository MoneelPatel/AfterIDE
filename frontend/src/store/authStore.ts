import { create } from 'zustand'

interface AuthState {
  isAuthenticated: boolean
  user: any | null
  token: string | null
  login: (username: string, password: string) => Promise<boolean>
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
          user: { username }, 
          token: data.access_token 
        })
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
  logout: () => {
    localStorage.removeItem('authToken')
    set({ isAuthenticated: false, user: null, token: null })
  },
  setToken: (token: string) => {
    set({ token })
  },
  initialize: () => {
    const token = localStorage.getItem('authToken')
    if (token) {
      set({ 
        isAuthenticated: true, 
        token,
        user: { username: 'admin' } // Default user for now
      })
    }
  },
})) 