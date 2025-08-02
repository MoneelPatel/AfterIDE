import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3004,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'http://localhost:8000',
        ws: true,
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false, // Disable sourcemaps to reduce memory usage
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          monaco: ['monaco-editor'],
          xterm: ['xterm', 'xterm-addon-fit', 'xterm-addon-web-links'],
          ui: ['@heroicons/react', 'lucide-react', 'react-hot-toast'],
          utils: ['axios', 'clsx', 'date-fns', 'tailwind-merge', 'zustand'],
        },
      },
    },
    chunkSizeWarningLimit: 1000, // Increase warning limit
  },
  optimizeDeps: {
    include: ['react', 'react-dom'], // Pre-bundle core dependencies
  },
}) 