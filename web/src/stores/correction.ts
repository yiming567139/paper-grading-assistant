import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { CorrectionLog } from '@/types/correction'

export const useCorrectionStore = defineStore('correction', () => {
  const isRunning = ref(false)
  const batchLimit = ref(0)
  const logs = ref<CorrectionLog[]>([])
  const loading = ref(false)
  const currentStep = ref(0) // 当前步骤: 0=空闲, 1=截图, 2=VLM评分, 3=清分, 4=打分, 5=确认
  const completedCount = ref(0)
  const dualGrading = ref(false)
  const primaryModel = ref('')
  const secondaryModel = ref('')

  const setRunning = (running: boolean) => {
    isRunning.value = running
  }

  const setBatchLimit = (limit: number) => {
    batchLimit.value = limit
  }

  const setCompletedCount = (count: number) => {
    completedCount.value = count
  }

  const setLogs = (newLogs: CorrectionLog[]) => {
    logs.value = newLogs
  }

  const addLog = (log: CorrectionLog) => {
    logs.value.unshift(log)
  }

  const setLoading = (l: boolean) => {
    loading.value = l
  }

  const setCurrentStep = (step: number) => {
    currentStep.value = step
  }

  const setDualGrading = (dual: boolean, primary = '', secondary = '') => {
    dualGrading.value = dual
    primaryModel.value = primary
    secondaryModel.value = secondary
  }

  return {
    isRunning,
    batchLimit,
    completedCount,
    logs,
    loading,
    currentStep,
    dualGrading,
    primaryModel,
    secondaryModel,
    setRunning,
    setBatchLimit,
    setCompletedCount,
    setLogs,
    addLog,
    setLoading,
    setCurrentStep,
    setDualGrading
  }
})
