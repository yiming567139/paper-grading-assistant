export interface CorrectionLog {
  time: string
  screenshot: string
  screenshot_human?: string
  score: number | null
  score_secondary?: number | null
  status: string
  detail: string
  vlm_response: string
  vlm_response_secondary?: string
  vlm_model?: string
  vlm_model_secondary?: string
  grading_mode?: 'single' | 'dual'
  score_consistent?: number | null
}

export interface CorrectionState {
  isRunning: boolean
  batchLimit: number
  logs: CorrectionLog[]
  loading: boolean
}
