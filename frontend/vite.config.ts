import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// In development, sending the data routes to `uv run python -m order_selection.server`
export default defineConfig({
  plugins: [react()],
  // Recharts alone is most of the bundle, and the page is served locally
  build: { chunkSizeWarningLimit: 1000 },
  server: { proxy: { '/api': 'http://localhost:8000' } },
})
