import type {
  AuthResponse,
  ChatMessage,
  ChatResponse,
  Profile,
  RagStatus,
  RecommendationResponse,
  RoadmapResponse,
  SearchRecord,
  User,
} from '@/types'

const TOKEN_KEY = 'yojanamitra_token'

export function getToken(): string | null {
  if (typeof window === 'undefined') return null
  return window.localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string): void {
  if (typeof window !== 'undefined') window.localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken(): void {
  if (typeof window !== 'undefined') window.localStorage.removeItem(TOKEN_KEY)
}

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> | undefined),
  }
  if (token) headers.Authorization = `Bearer ${token}`

  const res = await fetch(`/api${path}`, { ...options, headers })

  if (!res.ok) {
    let detail = `Request failed (${res.status})`
    try {
      const body = await res.json()
      if (body?.detail) detail = typeof body.detail === 'string' ? body.detail : detail
    } catch {
      /* ignore */
    }
    throw new ApiError(detail, res.status)
  }

  if (res.status === 204) return undefined as T
  return (await res.json()) as T
}

export const api = {
  // Auth
  register: (data: { full_name: string; email: string; password: string }) =>
    request<AuthResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  login: (data: { email: string; password: string }) =>
    request<AuthResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  me: () => request<User>('/auth/me'),

  // Profile
  getProfile: () => request<Profile | null>('/profile'),
  updateProfile: (profile: Profile) =>
    request<Profile>('/profile', { method: 'PUT', body: JSON.stringify(profile) }),
  recentSearches: () => request<SearchRecord[]>('/searches'),

  // AI
  recommendations: (profile: Profile) =>
    request<RecommendationResponse>('/recommendations', {
      method: 'POST',
      body: JSON.stringify(profile),
    }),
  roadmap: (profile: Profile) =>
    request<RoadmapResponse>('/roadmap', {
      method: 'POST',
      body: JSON.stringify(profile),
    }),
  chat: (message: string, history: ChatMessage[]) =>
    request<ChatResponse>('/chat', {
      method: 'POST',
      body: JSON.stringify({ message, history }),
    }),

  // RAG
  ragStatus: () => request<RagStatus>('/rag/status'),
  ragReindex: () => request<RagStatus>('/rag/reindex', { method: 'POST' }),
}
