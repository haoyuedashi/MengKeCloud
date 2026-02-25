import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [vue()],
    build: {
        rollupOptions: {
            output: {
                manualChunks(id) {
                    if (id.includes('node_modules')) {
                        if (id.includes('echarts')) return 'vendor-echarts'
                        if (id.includes('element-plus')) return 'vendor-element-plus'
                        if (id.includes('vue') || id.includes('vue-router')) return 'vendor-vue'
                        if (id.includes('axios')) return 'vendor-axios'
                        return 'vendor-misc'
                    }
                }
            }
        }
    },
    resolve: {
        alias: {
            '@': path.resolve(__dirname, './src'),
        },
    },
    server: {
        proxy: {
            '/api': {
                target: 'http://127.0.0.1:8001',
                changeOrigin: true,
                ws: true
            }
        }
    }
})
