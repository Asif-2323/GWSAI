export interface User {
  id: string
  full_name: string
  email: string
  created_at: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

export type Gender = 'male' | 'female' | 'other'
export type Category = 'general' | 'obc' | 'sc' | 'st' | 'ews' | 'other'

export interface Profile {
  full_name: string
  age: number
  gender: Gender
  state: string
  district: string
  occupation: string
  education: string
  annual_income: number
  category: Category
  disability_status: boolean
  minority_status: boolean
  student_status: boolean
  farmer_status: boolean
  widow_status: boolean
  senior_citizen_status: boolean
  bpl_status: boolean
}

export interface SchemeRecommendation {
  name: string
  why_eligible: string
  benefits: string
  required_documents: string[]
  application_process: string
  official_website?: string | null
}

export interface RecommendationResponse {
  recommendations: SchemeRecommendation[]
  sources: string[]
  message?: string | null
}

export interface RoadmapMilestone {
  stage: string
  schemes: string[]
  reasoning: string
}

export interface RoadmapResponse {
  milestones: RoadmapMilestone[]
  sources: string[]
  message?: string | null
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatResponse {
  answer: string
  sources: string[]
}

export interface SearchRecord {
  id: string
  kind: 'recommendation' | 'roadmap' | 'chat'
  summary: string
  created_at: string
}

export interface RagStatus {
  documents_indexed: number
  chunks_indexed: number
  embedding_model: string
  collection: string
  ready: boolean
  message: string
}
