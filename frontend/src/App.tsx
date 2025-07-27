import { Routes, Route } from 'react-router-dom'
import { useEffect } from 'react'
import { ThemeProvider } from './contexts/ThemeContext'
import { WebSocketProvider } from './contexts/WebSocketContext'

import Layout from './components/Layout'
import EditorPage from './pages/EditorPage'
import LoginPage from './pages/LoginPage'
import ReviewPage from './pages/ReviewPage'
import { useAuthStore } from './store/authStore'

function App() {
  const { isAuthenticated, initialize } = useAuthStore()

  // Initialize auth store on app startup
  useEffect(() => {
    initialize()
  }, [initialize])

  return (
    <ThemeProvider>
      <WebSocketProvider>
        <div className="h-full">
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<LoginPage />} />
            
            {/* Protected routes */}
            <Route
              path="/"
              element={
                isAuthenticated ? (
                  <Layout>
                    <EditorPage />
                  </Layout>
                ) : (
                  <LoginPage />
                )
              }
            />
            
            <Route
              path="/review"
              element={
                isAuthenticated ? (
                  <Layout>
                    <ReviewPage />
                  </Layout>
                ) : (
                  <LoginPage />
                )
              }
            />
          </Routes>
        </div>
      </WebSocketProvider>
    </ThemeProvider>
  )
}

export default App 