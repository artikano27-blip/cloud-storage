import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
  },
  build: {
    emptyOutDir: true, // Очищаем папку перед каждой новой сборкой, чтобы не копился мусор
  }
})