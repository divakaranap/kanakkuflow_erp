import { api } from "./api"
import type { TokenResponse, UserInfo } from "../types/auth"

export const authService = {
  async login(username: string, password: string): Promise<TokenResponse> {
    const response = await api.post<TokenResponse>("/auth/login", {
      username,
      password,
    })
    const data = response.data
    localStorage.setItem("kanakkuflow_token", data.access_token)
    localStorage.setItem("kanakkuflow_user", JSON.stringify(data.user))
    return data
  },

  async getCurrentUser(): Promise<UserInfo> {
    const response = await api.get<UserInfo>("/auth/me")
    return response.data
  },

  logout(): void {
    localStorage.removeItem("kanakkuflow_token")
    localStorage.removeItem("kanakkuflow_user")
  },

  getStoredUser(): UserInfo | null {
    const raw = localStorage.getItem("kanakkuflow_user")
    if (!raw) return null
    try {
      return JSON.parse(raw) as UserInfo
    } catch {
      return null
    }
  },

  getToken(): string | null {
    return localStorage.getItem("kanakkuflow_token")
  },
}
