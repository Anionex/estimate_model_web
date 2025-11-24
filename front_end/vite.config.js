import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'fs'
import path from 'path'
import yaml from 'js-yaml'

const rootDir = path.resolve(__dirname, '..')
const configPath = path.join(rootDir, 'config.yaml')

const appConfig = (() => {
  try {
    return yaml.load(fs.readFileSync(configPath, 'utf8')) || {}
  } catch (error) {
    console.warn(`Unable to load config.yaml at ${configPath}. Falling back to defaults.`, error)
    return {}
  }
})()

const frontendConfig = appConfig.frontend || {}
const frontendHost = frontendConfig.host || '127.0.0.1'
const frontendPort = frontendConfig.port || 5173

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: frontendHost,
    port: frontendPort,
    fs: {
      allow: [rootDir],
    },
  },
  build: {
    chunkSizeWarningLimit: 1000,
  },
})
