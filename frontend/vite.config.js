import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      'vue': 'vue/dist/vue.esm-bundler.js'
    }
  },
  envDir: '.',                     // load root .env, .env.development, .env.production
  envPrefix: 'VITE_',             // expose only VITE_* to client
  server: {
    allowedHosts: ['commongraph.org', 'www.commongraph.org']
  },
  build: {
    sourcemap: true,
  },
});
