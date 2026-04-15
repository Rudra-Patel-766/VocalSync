import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use((config) => {
  if (typeof window === 'undefined') {
    return config
  }

  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (typeof window !== 'undefined' && error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export interface User {
  id: number
  email: string
  firebase_uid: string
  created_at: string
}

export interface Session {
  id: number
  user_id: number
  goal: string
  context?: string
  start_time: string
  end_time?: string
  metrics?: SessionMetrics
}

export interface SessionMetrics {
  session_id: number
  wpm: number
  filler_count: number
  filler_ratio: number
  avg_pause: number
  pitch_variance: number
  confidence_score: number
  emotion_label: string
  goal_score: number
}

export interface SessionCreate {
  goal: string
  context?: string
}

export interface AnalyticsData {
  last_15_sessions: SessionTrend[]
  wpm_growth: number
  filler_reduction: number
  confidence_trend: string
  insights: string[]
}

export interface SessionRecommendationResponse {
  status: 'pending' | 'ready' | 'failed'
  recommendations: string | null
  source?: string | null
  error?: string | null
}

export interface SessionTrend {
  session_id: number
  date: string
  wpm: number
  filler_ratio: number
  confidence_score: number
}

export interface RealtimeMetrics {
  wpm?: number
  filler_count?: number
  filler_ratio?: number
  silence_detected?: boolean
  volume_level?: number
  pace_feedback?: string
  volume_feedback?: string
  silence_feedback?: string
  filler_feedback?: string
}

// Auth API
export const authAPI = {
  login: async (idToken: string) => {
    const response = await api.post('/api/v1/auth/login', { id_token: idToken })
    return response.data
  },

  getMe: async (): Promise<User> => {
    const response = await api.get('/api/v1/auth/me')
    return response.data
  },

  logout: async () => {
    await api.post('/api/v1/auth/logout')
  },
}

// Session API
export const sessionAPI = {
  startSession: async (sessionData: SessionCreate): Promise<Session> => {
    const response = await api.post('/api/v1/session/start', sessionData)
    return response.data
  },

  endSession: async (sessionId: number): Promise<Session> => {
    const response = await api.post(`/api/v1/session/${sessionId}/end`)
    return response.data
  },

  getSessions: async (limit: number = 50): Promise<Session[]> => {
    const response = await api.get(`/api/v1/session/?limit=${limit}`)
    return response.data
  },

  getSession: async (sessionId: number): Promise<Session> => {
    const response = await api.get(`/api/v1/session/${sessionId}`)
    return response.data
  },

  getRecommendations: async (sessionId: number): Promise<SessionRecommendationResponse> => {
    const response = await api.get(`/api/v1/session/${sessionId}/recommendations`)
    return response.data
  },
}

// Dashboard API
export const dashboardAPI = {
  getAnalytics: async (): Promise<AnalyticsData> => {
    const response = await api.get('/api/v1/dashboard/analytics')
    return response.data
  },

  getDashboard: async () => {
    const response = await api.get('/api/v1/dashboard/dashboard')
    return response.data
  },

  getInsights: async () => {
    const response = await api.get('/api/v1/dashboard/insights')
    return response.data
  },
}
