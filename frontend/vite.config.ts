import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

const backend = process.env.VITE_PROXY_API ?? 'http://localhost:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { '/api': { target: backend, changeOrigin: true } },
  },
  test: {
    environment: 'jsdom',
  },
})
