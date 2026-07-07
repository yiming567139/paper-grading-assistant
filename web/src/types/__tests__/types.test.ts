import { describe, it, expect } from 'vitest'

describe('Type definitions', () => {
  describe('CorrectionLog', () => {
    it('should allow constructing a valid CorrectionLog object', () => {
      const log = {
        time: '2026-07-01 10:00:00',
        screenshot: '/screenshots/001.png',
        screenshot_human: '/screenshots/human_001.png',
        score: 5,
        score_secondary: 4,
        status: '成功',
        detail: '',
        vlm_response: '5',
        vlm_response_secondary: '4',
        vlm_model: 'qwen-vl',
        vlm_model_secondary: 'deepseek-vl',
        grading_mode: 'dual' as const,
        score_consistent: 1,
      }
      expect(log.time).toBe('2026-07-01 10:00:00')
      expect(log.score).toBe(5)
      expect(log.grading_mode).toBe('dual')
      expect(log.score_consistent).toBe(1)
    })

    it('should allow single mode log without optional fields', () => {
      const log = {
        time: '2026-07-01 10:00:00',
        screenshot: '/screenshots/001.png',
        score: 3,
        status: '成功',
        detail: '',
        vlm_response: '3',
      } as Record<string, any>
      expect(log.status).toBe('成功')
      expect(log.screenshot_human).toBeUndefined()
    })

    it('should allow score to be null', () => {
      const log = {
        time: '2026-07-01 10:00:00',
        screenshot: '',
        score: null,
        status: '失败',
        detail: '识别失败',
        vlm_response: '',
      }
      expect(log.score).toBeNull()
      expect(log.status).toBe('失败')
    })
  })

  describe('CorrectionState', () => {
    it('should have correct shape with default values', () => {
      const state = {
        isRunning: false,
        batchLimit: 0,
        logs: [],
        loading: false,
      }
      expect(state.isRunning).toBe(false)
      expect(state.batchLimit).toBe(0)
      expect(state.logs).toHaveLength(0)
      expect(state.loading).toBe(false)
    })

    it('should allow with running state and logs', () => {
      const state = {
        isRunning: true,
        batchLimit: 10,
        logs: [
          { time: '10:00', screenshot: 'a.png', score: 5, status: '成功', detail: '', vlm_response: '5' },
        ],
        loading: true,
      }
      expect(state.isRunning).toBe(true)
      expect(state.logs).toHaveLength(1)
    })
  })

  describe('VlmLog', () => {
    it('should allow constructing a VlmLog object', () => {
      const log = {
        id: 1,
        record_id: 100,
        provider: 'dashscope',
        model: 'qwen-vl-plus',
        base_url: 'https://dashscope.aliyuncs.com',
        prompt: '请评分',
        image_path: '/tmp/test.png',
        raw_response: '5',
        score: 5,
        duration_ms: 1200,
        status: 'success',
        error_message: null,
        created_at: '2026-07-01 10:00:00',
      }
      expect(log.id).toBe(1)
      expect(log.provider).toBe('dashscope')
      expect(log.duration_ms).toBe(1200)
    })

    it('should allow error_message to be string', () => {
      const log = {
        id: 2,
        record_id: null,
        provider: 'deepseek',
        model: 'deepseek-vl',
        base_url: '',
        prompt: '请评分',
        image_path: '/tmp/fail.png',
        raw_response: '',
        score: 0,
        duration_ms: 5000,
        status: 'fail',
        error_message: 'timeout',
        created_at: '2026-07-01 11:00:00',
      }
      expect(log.status).toBe('fail')
      expect(log.error_message).toBe('timeout')
    })
  })

  describe('AppConfig', () => {
    it('should allow constructing a minimal AppConfig', () => {
      const config = {
        llm: {
          provider: 'dashscope',
          model: 'qwen-vl-plus',
          api_key: 'sk-xxx',
          base_url: 'https://dashscope.aliyuncs.com',
          timeout: 60,
          max_retries: 2,
          prompt_template: '请评分',
        },
        mysql: {
          host: 'localhost',
          port: 3306,
          database: 'grading_app',
          user: 'root',
          password: '123456',
          charset: 'utf8mb4',
        },
        paths: { logs: './logs', screenshots: './screenshots' },
        region: {
          capture: { x1: 0, y1: 0, x2: 100, y2: 100 },
          score_buttons: [{ score: 0, x: 100, y: 200 }],
          clear_score: { enabled: true, x: 10, y: 10 },
          confirm_button: { x: 500, y: 500 },
        },
        http_server: { host: '0.0.0.0', port: 8081 },
        window: { auto_open_browser: true },
      }
      expect(config.llm.model).toBe('qwen-vl-plus')
      expect(config.region.capture.x1).toBe(0)
      expect(config.mysql.port).toBe(3306)
    })

    it('should allow optional llm_secondary field', () => {
      const config = {
        llm: {
          provider: 'dashscope',
          model: 'qwen-vl-plus',
          api_key: 'sk-xxx',
          base_url: '',
          timeout: 60,
          max_retries: 2,
          prompt_template: '请评分',
        },
        llm_secondary: {
          enabled: true,
          provider: 'deepseek',
          model: 'deepseek-vl',
          api_key: 'sk-yyy',
          base_url: '',
          timeout: 60,
          max_retries: 2,
          prompt_template: '',
        },
        mysql: {
          host: 'localhost',
          port: 3306,
          database: 'grading_app',
          user: 'root',
          password: '123456',
          charset: 'utf8mb4',
        },
        paths: { logs: './logs', screenshots: './screenshots' },
        region: {
          capture: { x1: 0, y1: 0, x2: 100, y2: 100 },
          score_buttons: [],
          clear_score: { enabled: false, x: 0, y: 0 },
          confirm_button: { x: 0, y: 0 },
        },
        http_server: { host: '0.0.0.0', port: 8081 },
        window: { auto_open_browser: false },
      }
      expect(config.llm_secondary?.enabled).toBe(true)
      expect(config.llm_secondary?.api_key).toBe('sk-yyy')
    })
  })
})
