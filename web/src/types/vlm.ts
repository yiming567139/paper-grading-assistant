export interface VlmLog {
  id: number
  record_id: number | null
  provider: string
  model: string
  base_url: string
  prompt: string
  image_path: string
  raw_response: string
  score: number
  duration_ms: number
  status: string
  error_message: string | null
  created_at: string
}
