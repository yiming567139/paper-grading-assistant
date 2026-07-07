import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockGet = vi.fn()
const mockPost = vi.fn()

vi.mock('@/utils/request', () => ({
  default: {
    get: mockGet,
    post: mockPost,
  },
}))

describe('correction API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('getCorrectionLogs should call GET /correction/logs with page params', async () => {
    const { getCorrectionLogs } = await import('@/api/correction')
    mockGet.mockResolvedValueOnce({ data: [], total: 0 })

    const result = await getCorrectionLogs(1, 50)
    expect(mockGet).toHaveBeenCalledWith('/correction/logs', {
      params: { page: 1, page_size: 50 },
    })
    expect(result).toEqual({ data: [], total: 0 })
  })

  it('getCorrectionLogs should pass consistent param when 0 or 1', async () => {
    const { getCorrectionLogs } = await import('@/api/correction')
    mockGet.mockResolvedValueOnce({ data: [], total: 0 })

    await getCorrectionLogs(1, 50, '1')
    expect(mockGet).toHaveBeenCalledWith('/correction/logs', {
      params: { page: 1, page_size: 50, consistent: '1' },
    })
  })

  it('getCorrectionLogs should skip consistent param when not 0 or 1', async () => {
    const { getCorrectionLogs } = await import('@/api/correction')
    mockGet.mockResolvedValueOnce({ data: [], total: 0 })

    await getCorrectionLogs(1, 50, undefined)
    expect(mockGet).toHaveBeenCalledWith('/correction/logs', {
      params: { page: 1, page_size: 50 },
    })
  })

  it('startCorrection should call POST /correction/start with batch_limit', async () => {
    const { startCorrection } = await import('@/api/correction')
    mockPost.mockResolvedValueOnce({ status: 'started' })

    const result = await startCorrection(5)
    expect(mockPost).toHaveBeenCalledWith('/correction/start', { batch_limit: 5 })
    expect(result).toEqual({ status: 'started' })
  })

  it('startCorrection should default batch_limit to 0', async () => {
    const { startCorrection } = await import('@/api/correction')
    mockPost.mockResolvedValueOnce({ status: 'started' })

    await startCorrection()
    expect(mockPost).toHaveBeenCalledWith('/correction/start', { batch_limit: 0 })
  })

  it('stopCorrection should call POST /correction/stop', async () => {
    const { stopCorrection } = await import('@/api/correction')
    mockPost.mockResolvedValueOnce({ status: 'stopped' })

    const result = await stopCorrection()
    expect(mockPost).toHaveBeenCalledWith('/correction/stop')
    expect(result).toEqual({ status: 'stopped' })
  })

  it('getCorrectionStatus should call GET /correction/status', async () => {
    const { getCorrectionStatus } = await import('@/api/correction')
    mockGet.mockResolvedValueOnce({ is_running: false })

    const result = await getCorrectionStatus()
    expect(mockGet).toHaveBeenCalledWith('/correction/status')
    expect(result).toEqual({ is_running: false })
  })

  it('evaluateImage should call POST /llm/evaluate with FormData', async () => {
    const { evaluateImage } = await import('@/api/correction')
    const formData = new FormData()
    formData.append('image', new Blob(['test']), 'test.png')

    mockPost.mockResolvedValueOnce({ success: true, score: 5 })
    const result = await evaluateImage(formData)
    expect(mockPost).toHaveBeenCalledWith('/llm/evaluate', formData)
    expect(result).toEqual({ success: true, score: 5 })
  })
})
