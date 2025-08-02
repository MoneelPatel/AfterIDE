import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from 'react-query'
import { Toaster } from 'react-hot-toast'
import App from './App'
import './index.css'

// Comprehensive monkey-patch to force HTTPS for sad-chess-production.up.railway.app
// Patch fetch
const originalFetch = window.fetch;
window.fetch = function(input, init) {
  if (typeof input === 'string' && input.startsWith('http://sad-chess-production.up.railway.app')) {
    input = input.replace('http://', 'https://');
  }
  return originalFetch(input, init);
};

// Patch XMLHttpRequest
const originalXHROpen = XMLHttpRequest.prototype.open;
XMLHttpRequest.prototype.open = function(method: string, url: string | URL, async: boolean = true, username?: string | null, password?: string | null) {
  if (typeof url === 'string' && url.startsWith('http://sad-chess-production.up.railway.app')) {
    url = url.replace('http://', 'https://');
  }
  return originalXHROpen.call(this, method, url, async, username, password);
};

// Log any attempts to make HTTP requests
console.log('🔒 HTTPS enforcement patches applied');

const queryClient = new QueryClient()

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter
        future={{
          v7_startTransition: true,
          v7_relativeSplatPath: true,
        }}
      >
        <App />
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#363636',
              color: '#fff',
            },
          }}
        />
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>,
) 