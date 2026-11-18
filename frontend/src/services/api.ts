import axios from "axios"

const host = typeof window !== 'undefined' && window.location.hostname ? window.location.hostname : 'localhost'
const API_BASE_URL = import.meta.env.VITE_API_URL || `http://${host}:8000`

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
