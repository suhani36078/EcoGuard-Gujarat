import axios from 'axios'

const BASE = '/api'

// ── Axios instance ─────────────────────────────────────────────────────────
const api = axios.create({
  baseURL: BASE,
  timeout: 30000,
})

// Attach JWT token if present
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export default api
