import request from '@/utils/request'

export const getCorrectionLogs = (page = 1, pageSize = 50, consistent?: '0' | '1') => {
  const params: Record<string, any> = { page, page_size: pageSize }
  if (consistent === '0' || consistent === '1') params.consistent = consistent
  return request.get('/correction/logs', { params })
}

export const startCorrection = (batchLimit: number = 0) => {
  return request.post('/correction/start', { batch_limit: batchLimit })
}

export const stopCorrection = () => {
  return request.post('/correction/stop')
}

export const getCorrectionStatus = () => {
  return request.get('/correction/status')
}

export const evaluateImage = (data: FormData) => {
  return request.post('/llm/evaluate', data)
}
