import axios from "axios"

// In Vercel multi-service deployment, the backend is routed under '/api' on the same domain.
// In local development, Vite proxies '/api' to http://127.0.0.1:8000.
// VITE_API_BASE_URL allows override when necessary, defaulting cleanly to '/api'.
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  import.meta.env.VITE_API_URL ||
  '/api'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("kanakkuflow_token")
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("kanakkuflow_token")
      localStorage.removeItem("kanakkuflow_user")
      if (window.location.pathname !== "/login") {
        window.location.href = "/login"
      }
    }
    return Promise.reject(error)
  }
)
