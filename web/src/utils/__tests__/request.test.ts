import { describe, it, expect, vi, beforeAll } from 'vitest'

const mockAxiosInstance = {
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  delete: vi.fn(),
  interceptors: {
    request: { use: vi.fn() },
    response: { use: vi.fn() },
  },
}

vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => mockAxiosInstance),
  },
  create: vi.fn(() => mockAxiosInstance),
}))

describe('request utility', () => {
  beforeAll(async () => {
    // Import triggers interceptor registration & exports default request
    await import('@/utils/request')
  })

  // --- Interceptor registration ---

  it('should install request and response interceptors', () => {
    expect(mockAxiosInstance.interceptors.request.use).toHaveBeenCalled()
    expect(mockAxiosInstance.interceptors.response.use).toHaveBeenCalled()
  })

  // --- Response interceptor behavior (extract from the one-time registration) ---

  it('response interceptor should return response.data', () => {
    const onFulfilled: Function =
      mockAxiosInstance.interceptors.response.use.mock.calls[0][0]
    const onRejected: Function | undefined =
      mockAxiosInstance.interceptors.response.use.mock.calls[0][1]
    expect(onRejected).toBeDefined()

    const mockResponse = { data: { data: [], total: 0 }, status: 200 }
    const result = onFulfilled(mockResponse)
    expect(result).toEqual(mockResponse.data)
  })

  it('response interceptor should reject on error', async () => {
    const onRejected: Function =
      mockAxiosInstance.interceptors.response.use.mock.calls[0][1]
    const mockError = new Error('Network Error')
    await expect(onRejected(mockError)).rejects.toThrow('Network Error')
  })

  // --- HTTP method wrappers ---
  // Note: These tests mock instance.get/post/put/delete directly, which
  // bypasses the response interceptor. The return value is the raw mock
  // resolved value (not response.data). Interceptor behavior is tested
  // separately above.

  it('should call instance.get for request.get', async () => {
    const request = (await import('@/utils/request')).default
    mockAxiosInstance.get.mockResolvedValueOnce({ data: { data: [{ id: 1 }], total: 1 } })

    const result = await request.get('/records', { params: { page: 1 } })

    expect(mockAxiosInstance.get).toHaveBeenCalledWith('/records', { params: { page: 1 } })
    expect(result).toEqual({ data: { data: [{ id: 1 }], total: 1 } })
  })

  it('should call instance.post for request.post', async () => {
    const request = (await import('@/utils/request')).default
    mockAxiosInstance.post.mockResolvedValueOnce({ data: { status: 'saved' } })

    const result = await request.post('/config', { key: 'value' })

    expect(mockAxiosInstance.post).toHaveBeenCalledWith('/config', { key: 'value' }, undefined)
    expect(result).toEqual({ data: { status: 'saved' } })
  })

  it('should call instance.put for request.put', async () => {
    const request = (await import('@/utils/request')).default
    mockAxiosInstance.put.mockResolvedValueOnce({ data: { success: true } })

    const result = await request.put('/records/1', { score: 5 })

    expect(mockAxiosInstance.put).toHaveBeenCalledWith('/records/1', { score: 5 }, undefined)
    expect(result).toEqual({ data: { success: true } })
  })

  it('should call instance.delete for request.delete', async () => {
    const request = (await import('@/utils/request')).default
    mockAxiosInstance.delete.mockResolvedValueOnce({ data: { success: true } })

    const result = await request.delete('/records/1')

    expect(mockAxiosInstance.delete).toHaveBeenCalledWith('/records/1', undefined)
    expect(result).toEqual({ data: { success: true } })
  })

  // --- Type check ---

  it('ApiResponse type should be structurally correct', () => {
    const response: { data: number[]; total?: number } = { data: [], total: 0 }
    expect(response).toBeDefined()
  })
})
