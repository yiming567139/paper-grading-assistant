export interface RegionConfig {
  capture: { x1: number; y1: number; x2: number; y2: number }
  capture_human?: { x1: number; y1: number; x2: number; y2: number }
  score_buttons: Array<{ score: number; x: number; y: number }>
  clear_score: { enabled: boolean; x: number; y: number }
  confirm_button: { x: number; y: number }
}

export interface LlmConfig {
  provider: string
  model: string
  api_key: string
  base_url: string
  timeout: number
  max_retries: number
  prompt_template: string
}

export interface LlmSecondaryConfig extends LlmConfig {
  enabled: boolean
}

export interface AppConfig {
  llm: LlmConfig
  llm_secondary?: LlmSecondaryConfig
  mysql: {
    host: string
    port: number
    database: string
    user: string
    password: string
    charset: string
  }
  paths: { logs: string; screenshots: string }
  region: RegionConfig
  http_server: { host: string; port: number }
  window: { auto_open_browser: boolean }
}
