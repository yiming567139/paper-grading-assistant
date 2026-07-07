<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useCorrectionStore } from '@/stores/correction'
import { startCorrection, stopCorrection, getCorrectionLogs, getCorrectionStatus } from '@/api/correction'
import { message } from 'ant-design-vue'

const store = useCorrectionStore()
const batchLimitInput = ref(0)
let statusTimer: number | null = null
let startDelayTimer: number | null = null
const isStarting = ref(false)
const startCountdown = ref(0)

const isStopDisabled = computed(() => !store.isRunning)

const statusText = computed(() => store.isRunning ? '执行中' : '未执行')

const handleStart = async () => {
  if (isStarting.value) return
  isStarting.value = true
  startCountdown.value = 2
  message.info(`${startCountdown.value}秒后开始批改...`)

  const countdownInterval = window.setInterval(() => {
    startCountdown.value--
    if (startCountdown.value > 0) {
      message.info(`${startCountdown.value}秒后开始批改...`)
    }
  }, 1000)

  startDelayTimer = window.setTimeout(async () => {
    clearInterval(countdownInterval)
    store.setBatchLimit(batchLimitInput.value)
    store.setCompletedCount(0)
    try {
      const res: any = await startCorrection(batchLimitInput.value)
      if (res.status === 'started' || res.success) {
        store.setRunning(true)
        store.setBatchLimit(batchLimitInput.value)
        message.success('开始批改')
        fetchLogs()
      } else {
        message.error(res.error || '启动失败')
      }
    } catch (error) {
      message.error('启动失败: ' + String(error))
    } finally {
      isStarting.value = false
      startCountdown.value = 0
    }
  }, 2000)
}

const handleStop = async () => {
  // 如果正在倒计时，先取消延迟启动
  if (isStarting.value && startDelayTimer) {
    clearTimeout(startDelayTimer)
    startDelayTimer = null
    isStarting.value = false
    startCountdown.value = 0
    message.info('已取消启动')
    return
  }
  try {
    const res: any = await stopCorrection()
    if (res.status === 'stopped' || res.success) {
      store.setRunning(false)
      store.setCurrentStep(0)
      message.warning('已停止批改')
    } else {
      message.error(res.error || '停止失败')
    }
  } catch (error) {
    message.error('停止失败: ' + String(error))
  }
}

const handleInputChange = (e: Event) => {
  const target = e.target as HTMLInputElement
  batchLimitInput.value = parseInt(target.value) || 0
}

const fetchLogs = async () => {
  try {
    const res = await getCorrectionLogs()
    if (res.success && res.data) {
      store.setLogs(res.data as any[])
    }
  } catch (error) {
    console.error('获取日志失败:', error)
  }
}

const fetchStatus = async () => {
  try {
    const res: any = await getCorrectionStatus()
    // 兼容新旧格式：新API直接返回状态，旧API包裹在 {success, data} 中
    const data = res.data || res
    if (data) {
      store.setRunning(data.is_running)
      store.setBatchLimit(data.batch_limit || 0)
      store.setCompletedCount(data.completed_count || 0)
      store.setDualGrading(!!data.dual_grading, data.primary_model || '', data.secondary_model || '')
      // 新引擎返回步骤名字符串，映射为数字以兼容旧 UI
      const stepMap: Record<string, number> = {
        'screenshot': 1, 'evaluate': 2, 'clear': 3,
        'click_score': 4, 'confirm': 5, 'wait': 5, '': 0
      }
      const step = data.current_step
      store.setCurrentStep(typeof step === 'number' ? step : (stepMap[step] || 0))
    }
  } catch (error) {
    console.error('获取状态失败:', error)
  }
}

const handleRefresh = () => {
  fetchLogs()
  fetchStatus()
  message.success('已刷新')
}

const handleKeyDown = (e: KeyboardEvent) => {
  if (e.key === 'Escape' && store.isRunning) {
    handleStop()
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeyDown)
  fetchStatus()
  // 启动定时器持续同步状态（2秒间隔）
  statusTimer = window.setInterval(() => {
    fetchStatus()
  }, 2000)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeyDown)
  if (statusTimer) {
    clearInterval(statusTimer)
  }
  if (startDelayTimer) {
    clearTimeout(startDelayTimer)
  }
})
</script>

<template>
  <div class="process-control-card">
    <div class="toolbar">
      <!-- 左组：开始/停止 + 状态 -->
      <div class="toolbar-left">
        <div class="control-buttons">
          <a-button
            html-type="button"
            type="primary"
            class="start-btn"
            :disabled="isStarting || store.isRunning"
            @click="handleStart"
          >
            {{ isStarting ? `${startCountdown}秒后启动...` : '开始' }}
          </a-button>

          <a-button
            html-type="button"
            class="stop-btn"
            :disabled="isStopDisabled && !isStarting"
            @click="handleStop"
          >
            {{ isStarting ? '取消' : '停止' }}
          </a-button>
        </div>

        <div :class="['status-indicator', store.isRunning ? 'running' : 'idle']">
          <span :class="['status-dot', store.isRunning ? 'running' : 'idle']"></span>
          <span class="status-text">{{ statusText }}</span>
        </div>
      </div>

      <!-- 右组：执行进度 + 批量设置 -->
      <div class="toolbar-right">
        <div class="step-progress">
          <div class="step-item" :class="{ active: store.currentStep >= 1, current: store.currentStep === 1 }">
            <span class="step-number">1</span>
            <span class="step-label">截图</span>
          </div>
          <div class="step-arrow">→</div>
          <div class="step-item" :class="{ active: store.currentStep >= 2, current: store.currentStep === 2 }">
            <span class="step-number">2</span>
            <template v-if="store.dualGrading">
              <span class="step-label dual-label">
                <span class="dual-line">主: {{ store.primaryModel || '主模型' }}</span>
                <span class="dual-line">副: {{ store.secondaryModel || '副模型' }}</span>
              </span>
            </template>
            <span v-else class="step-label">VLM评分</span>
          </div>
          <div class="step-arrow">→</div>
          <div class="step-item" :class="{ active: store.currentStep >= 3, current: store.currentStep === 3 }">
            <span class="step-number">3</span>
            <span class="step-label">清分</span>
          </div>
          <div class="step-arrow">→</div>
          <div class="step-item" :class="{ active: store.currentStep >= 4, current: store.currentStep === 4 }">
            <span class="step-number">4</span>
            <span class="step-label">打分</span>
          </div>
          <div class="step-arrow">→</div>
          <div class="step-item" :class="{ active: store.currentStep >= 5, current: store.currentStep === 5 }">
            <span class="step-number">5</span>
            <span class="step-label">确认</span>
          </div>
        </div>

        <div class="toolbar-divider"></div>

        <div class="batch-setting">
          <span class="label">批次</span>
          <a-input-number
            v-model:value="batchLimitInput"
            :min="0"
            class="batch-input"
            @change="handleInputChange"
          />
          <span v-if="store.batchLimit > 0" class="batch-remaining">
            剩余 {{ Math.max(0, store.batchLimit - store.completedCount) }} / {{ store.batchLimit }}
          </span>
          <a-button html-type="button" class="refresh-btn" @click.prevent="handleRefresh">
            <template #icon>
              <span class="refresh-icon">&#xe4e4;</span>
            </template>
            刷新
          </a-button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.process-control-card {
  background: #ffffff;
  border: 0.9px solid #e2e8f0;
  border-radius: 12px;
  padding: 12px 20px; /* 紧凑内边距 */
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.status-indicator.idle {
  background-color: #f1f5f9;
}

.status-indicator.running {
  background-color: #dcfce7;
  border: 1px solid #86efac;
}

.status-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-dot.running {
  background-color: #22c55e;
  box-shadow: 0 0 10px #22c55e;
  animation: pulse 1.5s infinite;
}

.status-dot.idle {
  background-color: #94a3b8;
  box-shadow: none;
}

.status-text {
  font-size: 14px;
  font-weight: 600;
}

.status-indicator.idle .status-text {
  color: #64748b;
}

.status-indicator.running .status-text {
  color: #166534;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px 24px;
  flex-wrap: wrap;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.toolbar-divider {
  width: 1px;
  height: 28px;
  background: var(--color-border, #e2e8f0);
}

.control-buttons {
  display: flex;
  gap: 12px;
}

.start-btn {
  background-color: var(--color-primary) !important;
  border-color: var(--color-primary) !important;
  padding: 8px 24px !important;
  height: auto !important;
  font-size: 15px !important;
  font-weight: 600 !important;
  border-radius: 8px !important;
}

.stop-btn {
  background-color: #e2e8f0 !important;
  border-color: #e2e8f0 !important;
  color: #64748b !important;
  padding: 8px 24px !important;
  height: auto !important;
  font-size: 15px !important;
  font-weight: 600 !important;
  border-radius: 8px !important;
}

.batch-setting {
  display: flex;
  align-items: center;
  gap: 12px;
}

.label {
  font-size: 14px;
  font-weight: 500;
  color: #334155;
}

.batch-input {
  width: 96px;
  border-radius: 8px !important;
}

.hint {
  font-size: 13px;
  color: #64748b;
}

.refresh-btn {
  display: flex !important;
  align-items: center !important;
  gap: 4px !important;
  padding: 8px 16px !important;
  height: auto !important;
  background-color: #f1f5f9 !important;
  border: none !important;
  border-radius: 8px !important;
  color: #334155 !important;
  font-size: 14px !important;
  font-weight: 500 !important;
  margin-left: 12px;
}

.refresh-icon {
  font-family: 'remixicon', sans-serif;
  font-size: 16px;
}

.step-progress {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background-color: #f1f5f9;
  border-radius: 8px;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 6px;
  background-color: #f8fafc;
  border: 2px dashed #e2e8f0;
  transition: all 0.3s ease;
}

.step-item.active {
  background-color: var(--color-primary-soft);
  border: 2px solid #7dd3fc;
}

.step-item.current {
  background: var(--gradient-brand);
  border-color: var(--color-primary-active);
  box-shadow: 0 0 0 3px rgba(2, 132, 199, 0.3);
}

.step-item.current .step-number {
  background-color: #ffffff;
  color: var(--color-primary-active);
  font-weight: 700;
}

.step-item.current .step-label {
  color: #ffffff !important;
  font-weight: 600;
}

.step-number {
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #cbd5e1;
  color: #ffffff;
  border-radius: 50%;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.step-item.active .step-number {
  background-color: var(--color-primary-hover);
}

.step-label {
  font-size: 13px;
  font-weight: 500;
  color: #cbd5e1;
}

.step-item.active .step-label {
  color: var(--color-primary-active);
  font-weight: 600;
}

.step-arrow {
  color: #94a3b8;
  font-size: 14px;
}

.batch-remaining {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-primary);
  margin-left: 8px;
}

.dual-label {
  display: inline-flex;
  flex-direction: column;
  line-height: 1.2;
}
.dual-line {
  font-size: 12px;
  white-space: nowrap;
}
</style>
