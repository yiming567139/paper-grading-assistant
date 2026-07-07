import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useCorrectionStore } from '@/stores/correction'

describe('correction store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should have initial state', () => {
    const store = useCorrectionStore()
    expect(store.isRunning).toBe(false)
    expect(store.batchLimit).toBe(0)
    expect(store.completedCount).toBe(0)
    expect(store.logs).toEqual([])
    expect(store.loading).toBe(false)
    expect(store.currentStep).toBe(0)
    expect(store.dualGrading).toBe(false)
    expect(store.primaryModel).toBe('')
    expect(store.secondaryModel).toBe('')
  })

  it('setRunning should update isRunning', () => {
    const store = useCorrectionStore()
    expect(store.isRunning).toBe(false)
    store.setRunning(true)
    expect(store.isRunning).toBe(true)
    store.setRunning(false)
    expect(store.isRunning).toBe(false)
  })

  it('setBatchLimit should update batchLimit', () => {
    const store = useCorrectionStore()
    expect(store.batchLimit).toBe(0)
    store.setBatchLimit(10)
    expect(store.batchLimit).toBe(10)
  })

  it('setCompletedCount should update completedCount', () => {
    const store = useCorrectionStore()
    expect(store.completedCount).toBe(0)
    store.setCompletedCount(5)
    expect(store.completedCount).toBe(5)
  })

  it('setLogs should replace logs', () => {
    const store = useCorrectionStore()
    const logs = [
      { time: '10:00', screenshot: 'a.png', score: 5, status: '成功', detail: '', vlm_response: '5' },
      { time: '10:01', screenshot: 'b.png', score: 3, status: '成功', detail: '', vlm_response: '3' },
    ]
    store.setLogs(logs as any)
    expect(store.logs).toHaveLength(2)
    expect(store.logs[0].score).toBe(5)
  })

  it('addLog should prepend log', () => {
    const store = useCorrectionStore()
    store.addLog({ time: '10:00', screenshot: 'a.png', score: 5, status: '成功', detail: '', vlm_response: '5' } as any)
    expect(store.logs).toHaveLength(1)
    store.addLog({ time: '10:01', screenshot: 'b.png', score: 3, status: '成功', detail: '', vlm_response: '3' } as any)
    expect(store.logs).toHaveLength(2)
    expect(store.logs[0].score).toBe(3) // prepended
  })

  it('setLoading should update loading', () => {
    const store = useCorrectionStore()
    expect(store.loading).toBe(false)
    store.setLoading(true)
    expect(store.loading).toBe(true)
    store.setLoading(false)
    expect(store.loading).toBe(false)
  })

  it('setCurrentStep should update currentStep', () => {
    const store = useCorrectionStore()
    expect(store.currentStep).toBe(0)
    store.setCurrentStep(3)
    expect(store.currentStep).toBe(3)
    store.setCurrentStep(0)
    expect(store.currentStep).toBe(0)
  })

  it('setDualGrading should update dual grading state', () => {
    const store = useCorrectionStore()
    store.setDualGrading(true, 'qwen-vl', 'deepseek-vl')
    expect(store.dualGrading).toBe(true)
    expect(store.primaryModel).toBe('qwen-vl')
    expect(store.secondaryModel).toBe('deepseek-vl')
  })

  it('setDualGrading should reset models when dual=false', () => {
    const store = useCorrectionStore()
    store.setDualGrading(true, 'mA', 'mB')
    store.setDualGrading(false)
    expect(store.dualGrading).toBe(false)
    expect(store.primaryModel).toBe('')
    expect(store.secondaryModel).toBe('')
  })

  it('state changes should be reflected immediately after setter calls', () => {
    const store = useCorrectionStore()
    store.setRunning(true)
    expect(store.isRunning).toBe(true)
    store.setRunning(false)
    expect(store.isRunning).toBe(false)
    store.setBatchLimit(100)
    expect(store.batchLimit).toBe(100)
    store.setCurrentStep(4)
    expect(store.currentStep).toBe(4)
  })
})
