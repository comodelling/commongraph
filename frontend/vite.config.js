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
    allowedHosts: [
      process.env.DOMAIN,
      `www.${process.env.DOMAIN}`,
      `api.${process.env.DOMAIN}`,
      'commongraph.org',          // Legacy support
      'www.commongraph.org',      // Legacy support
      'commonoutcomes.org',       // Legacy support
      'www.commonoutcomes.org',   // Legacy support
      'localhost',
      '127.0.0.1'
    ].filter(Boolean)  // Remove any undefined values
  },
  preview: {
    allowedHosts: [
      process.env.DOMAIN,
      `www.${process.env.DOMAIN}`,
      `api.${process.env.DOMAIN}`,
      'commongraph.org',          // Legacy support
      'www.commongraph.org',      // Legacy support
      'commonoutcomes.org',       // Legacy support
      'www.commonoutcomes.org',   // Legacy support
      'localhost',
      '127.0.0.1'
    ].filter(Boolean)  // Remove any undefined values
  },
  build: {
    sourcemap: true,
  },
});
