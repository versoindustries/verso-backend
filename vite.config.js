import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],
    root: 'app/static/src',
    base: '/static/dist/',
    build: {
        outDir: '../../dist',
        emptyOutDir: true,
        manifest: true,
        rollupOptions: {
            input: {
                main: path.resolve(process.cwd(), 'app/static/src/main.tsx'),
            },
        },
    },
    server: {
        origin: 'http://localhost:5173',
        cors: true,
    },
})
