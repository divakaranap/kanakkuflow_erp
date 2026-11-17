export type UserRole = "OWNER" | "ADMIN" | "SALESMAN" | "PRODUCTION" | "AUDITOR"

export interface UserInfo {
  id: number
  username: string
  email: string
  full_name: string
  role: UserRole
  is_active: boolean
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in_minutes: number
  user: UserInfo
}

export interface AuthState {
  user: UserInfo | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
}
