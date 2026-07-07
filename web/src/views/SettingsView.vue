<template>
  <div class="page">
    <div class="page-header">
      <div>
        <div class="page-title"><span class="title-accent"></span>系统设置</div>
        <div class="page-subtitle">配置阅卷模式、数据库与工作流</div>
      </div>
    </div>
    <div class="ui-card" style="padding:16px;">
      <a-tabs>
        <a-tab-pane key="llm" tab="阅卷模式配置">
          <a-card title="主模型（最终以主模型分为准）" size="small" style="margin-bottom: 16px;">
            <a-form :model="config.llm" layout="vertical">
              <a-form-item label="提供商">
                <a-select v-model:value="config.llm.provider">
                  <a-select-option value="dashscope">阿里百炼</a-select-option>
                  <a-select-option value="deepseek">DeepSeek</a-select-option>
                  <a-select-option value="openai">OpenAI</a-select-option>
                  <a-select-option value="other">其他</a-select-option>
                </a-select>
              </a-form-item>
              <a-form-item label="API Key">
                <a-input-password v-model:value="config.llm.api_key" />
              </a-form-item>
              <a-form-item label="模型">
                <a-input v-model:value="config.llm.model" placeholder="如 qwen-vl-plus" />
              </a-form-item>
              <a-form-item label="Base URL（必填）">
                <a-input v-model:value="config.llm.base_url" placeholder="请选择或输入 Base URL" />
              </a-form-item>
              <a-form-item label="提示词模板">
                <a-textarea v-model:value="config.llm.prompt_template" :rows="4" />
              </a-form-item>
            </a-form>
          </a-card>

          <a-card title="副模型（双评）" size="small" style="margin-bottom: 16px;">
            <a-alert
              type="info"
              show-icon
              style="margin-bottom: 16px;"
              message="双评模式：开启后，同一张截图会同时发送给主模型和副模型评分。最终以主模型分为准，两者一致性会在列表中用颜色标注。"
            />
            <a-form v-if="config.llm_secondary" :model="config.llm_secondary" layout="vertical">
              <a-form-item label="启用双评">
                <a-switch v-model:checked="config.llm_secondary.enabled" />
                <span style="margin-left: 12px; color: var(--color-text-secondary);">
                  {{ config.llm_secondary.enabled ? '已启用（需填写下方副模型信息）' : '未启用（保持单评）' }}
                </span>
              </a-form-item>
              <a-form-item label="副模型提供商">
                <a-select v-model:value="config.llm_secondary.provider">
                  <a-select-option value="dashscope">阿里百炼</a-select-option>
                  <a-select-option value="deepseek">DeepSeek</a-select-option>
                  <a-select-option value="openai">OpenAI</a-select-option>
                  <a-select-option value="other">其他</a-select-option>
                </a-select>
              </a-form-item>
              <a-form-item label="副模型 API Key">
                <a-input-password v-model:value="config.llm_secondary.api_key" />
              </a-form-item>
              <a-form-item label="副模型">
                <a-input v-model:value="config.llm_secondary.model" placeholder="如 qwen-vl-plus" />
              </a-form-item>
              <a-form-item label="副模型 Base URL（必填）">
                <a-input v-model:value="config.llm_secondary.base_url" placeholder="请选择或输入 Base URL" />
              </a-form-item>
              <a-form-item label="副模型提示词模板">
                <a-textarea v-model:value="config.llm_secondary.prompt_template" :rows="4" placeholder="留空则复用主模型提示词" />
              </a-form-item>
            </a-form>
          </a-card>
        </a-tab-pane>

        <a-tab-pane key="region" tab="区域坐标">
          <a-form layout="vertical">
            <!-- 截图区域校准 -->
            <a-card title="截图区域" size="small" style="margin-bottom: 16px;">
              <a-row :gutter="8" align="middle">
                <a-col :span="5">
                  <a-form-item label="左上角 X" style="margin-bottom: 0;">
                    <a-input-number v-model:value="config.region.capture.x1" style="width: 100%;" />
                  </a-form-item>
                </a-col>
                <a-col :span="5">
                  <a-form-item label="左上角 Y" style="margin-bottom: 0;">
                    <a-input-number v-model:value="config.region.capture.y1" style="width: 100%;" />
                  </a-form-item>
                </a-col>
                <a-col :span="3" style="display: flex; align-items: flex-end; padding-bottom: 4px;">
                  <a-button size="small" @click="simulateClick(config.region.capture.x1, config.region.capture.y1)">模拟点击</a-button>
                </a-col>
                <a-col :span="5">
                  <a-form-item label="右下角 X" style="margin-bottom: 0;">
                    <a-input-number v-model:value="config.region.capture.x2" style="width: 100%;" />
                  </a-form-item>
                </a-col>
                <a-col :span="5">
                  <a-form-item label="右下角 Y" style="margin-bottom: 0;">
                    <a-input-number v-model:value="config.region.capture.y2" style="width: 100%;" />
                  </a-form-item>
                </a-col>
                <a-col :span="1"></a-col>
              </a-row>
              <div style="margin-top: 12px;">
                <a-button type="primary" @click="startCalibration('capture')" :loading="calibrationLoading">
                  校准截图区域
                </a-button>
              </div>
            </a-card>

            <!-- 人看截图区域校准（可选） -->
            <a-card title="人看截图区域（可选，仅展示不送模型）" size="small" style="margin-bottom: 16px;" v-if="config.region.capture_human">
              <a-row :gutter="8" align="middle">
                <a-col :span="5">
                  <a-form-item label="左上角 X" style="margin-bottom: 0;">
                    <a-input-number v-model:value="config.region.capture_human.x1" style="width: 100%;" />
                  </a-form-item>
                </a-col>
                <a-col :span="5">
                  <a-form-item label="左上角 Y" style="margin-bottom: 0;">
                    <a-input-number v-model:value="config.region.capture_human.y1" style="width: 100%;" />
                  </a-form-item>
                </a-col>
                <a-col :span="3" style="display: flex; align-items: flex-end; padding-bottom: 4px;">
                  <a-button size="small" @click="simulateClick(config.region.capture_human.x1, config.region.capture_human.y1)">模拟点击</a-button>
                </a-col>
                <a-col :span="5">
                  <a-form-item label="右下角 X" style="margin-bottom: 0;">
                    <a-input-number v-model:value="config.region.capture_human.x2" style="width: 100%;" />
                  </a-form-item>
                </a-col>
                <a-col :span="5">
                  <a-form-item label="右下角 Y" style="margin-bottom: 0;">
                    <a-input-number v-model:value="config.region.capture_human.y2" style="width: 100%;" />
                  </a-form-item>
                </a-col>
                <a-col :span="1"></a-col>
              </a-row>
              <div style="margin-top: 12px;">
                <a-button type="primary" @click="startCalibration('capture_human')" :loading="calibrationLoading">
                  校准人看截图区域
                </a-button>
              </div>
            </a-card>

            <!-- 分数按钮校准 -->
            <a-card title="分数按钮" size="small" style="margin-bottom: 16px;">
              <a-row :gutter="[8, 8]">
                <a-col :span="12" v-for="(btn, index) in config.region.score_buttons" :key="index">
                  <a-card size="small">
                    <template #title>
                      <span>分数 {{ btn.score }}</span>
                    </template>
                    <a-row :gutter="8" align="middle">
                      <a-col :span="7">
                        <a-form-item label="X" style="margin-bottom: 0;">
                          <a-input-number v-model:value="btn.x" style="width: 100%;" />
                        </a-form-item>
                      </a-col>
                      <a-col :span="7">
                        <a-form-item label="Y" style="margin-bottom: 0;">
                          <a-input-number v-model:value="btn.y" style="width: 100%;" />
                        </a-form-item>
                      </a-col>
                      <a-col :span="10" style="display: flex; align-items: flex-end; gap: 4px; padding-bottom: 4px;">
                        <a-button size="small" @click="simulateClick(btn.x, btn.y)">模拟点击</a-button>
                        <a-button size="small" @click="startCalibration('score', Number(index))" :loading="calibrationLoading">校准</a-button>
                      </a-col>
                    </a-row>
                  </a-card>
                </a-col>
              </a-row>
            </a-card>

            <!-- 清分按钮校准 -->
            <a-card title="清分按钮" size="small" style="margin-bottom: 16px;">
              <a-row :gutter="8" align="middle">
                <a-col :span="6">
                  <a-form-item label="X" style="margin-bottom: 0;">
                    <a-input-number v-model:value="config.region.clear_score.x" style="width: 100%;" />
                  </a-form-item>
                </a-col>
                <a-col :span="6">
                  <a-form-item label="Y" style="margin-bottom: 0;">
                    <a-input-number v-model:value="config.region.clear_score.y" style="width: 100%;" />
                  </a-form-item>
                </a-col>
                <a-col :span="12" style="display: flex; align-items: flex-end; gap: 8px; padding-bottom: 4px;">
                  <a-button size="small" @click="simulateClick(config.region.clear_score.x, config.region.clear_score.y)">模拟点击</a-button>
                  <a-button size="small" @click="startCalibration('clear_score')" :loading="calibrationLoading">校准</a-button>
                </a-col>
              </a-row>
            </a-card>

            <!-- 确认按钮校准 -->
            <a-card title="确认按钮" size="small" style="margin-bottom: 16px;">
              <a-row :gutter="8" align="middle">
                <a-col :span="6">
                  <a-form-item label="X" style="margin-bottom: 0;">
                    <a-input-number v-model:value="config.region.confirm_button.x" style="width: 100%;" />
                  </a-form-item>
                </a-col>
                <a-col :span="6">
                  <a-form-item label="Y" style="margin-bottom: 0;">
                    <a-input-number v-model:value="config.region.confirm_button.y" style="width: 100%;" />
                  </a-form-item>
                </a-col>
                <a-col :span="12" style="display: flex; align-items: flex-end; gap: 8px; padding-bottom: 4px;">
                  <a-button size="small" @click="simulateClick(config.region.confirm_button.x, config.region.confirm_button.y)">模拟点击</a-button>
                  <a-button size="small" @click="startCalibration('confirm')" :loading="calibrationLoading">校准</a-button>
                </a-col>
              </a-row>
            </a-card>
          </a-form>
        </a-tab-pane>

        <a-tab-pane key="mysql" tab="MySQL">
          <a-form :model="config.mysql" layout="vertical">
            <a-form-item label="Host"><a-input v-model:value="config.mysql.host" /></a-form-item>
            <a-form-item label="Port"><a-input-number v-model:value="config.mysql.port" /></a-form-item>
            <a-form-item label="数据库"><a-input v-model:value="config.mysql.database" /></a-form-item>
            <a-form-item label="用户名"><a-input v-model:value="config.mysql.user" /></a-form-item>
            <a-form-item label="密码"><a-input-password v-model:value="config.mysql.password" /></a-form-item>
          </a-form>
        </a-tab-pane>

        <a-tab-pane key="screenshots" tab="截图设置">
          <a-form layout="vertical">
            <a-form-item label="存储路径">
              <a-input v-model:value="config.paths.screenshots" />
            </a-form-item>
          </a-form>
        </a-tab-pane>

        <a-tab-pane key="workflow" tab="工作流">
          <a-list :data-source="workflowSteps" bordered>
            <template #renderItem="{ item, index }">
              <a-list-item>
                <div class="step-row">
                  <span class="step-seq">{{ index + 1 }}</span>
                  <span class="step-id">{{ getStepName(item.id) }}</span>
                  <span class="step-type">{{ getStepType(item.type) }}</span>
                  <div class="step-delay">
                    <span class="delay-label">等待</span>
                    <a-input-number
                      v-model:value="item.delay"
                      :min="0"
                      :max="60"
                      :step="0.5"
                      size="small"
                      style="width: 72px;"
                    />
                    <span class="delay-unit">秒</span>
                  </div>
                  <a-switch v-model:checked="item.enabled" />
                  <a-button size="small" @click="moveStepUp(index)" :disabled="index === 0">上移</a-button>
                  <a-button size="small" @click="moveStepDown(index)" :disabled="index === workflowSteps.length - 1">下移</a-button>
                  <a-button
                    v-if="item.type === 'VLMEvalStep'"
                    size="small"
                    :type="expandedMockIndex === index ? 'primary' : 'default'"
                    @click="toggleMock(index)"
                  >
                    {{ expandedMockIndex === index ? '收起模拟' : '模拟配置' }}
                  </a-button>
                </div>
                <div v-if="expandedMockIndex === index && item.type === 'VLMEvalStep'" class="mock-panel">
                  <div class="mock-header">
                    <a-switch v-model:checked="mockResultOf(item).enabled" />
                    <span class="mock-label">启用模拟返回结果</span>
                  </div>
                  <div v-if="mockResultOf(item).enabled" class="mock-body">
                    <a-card title="主模型" size="small" class="mock-card">
                      <a-form layout="vertical">
                        <a-form-item label="模拟分数">
                          <a-input-number
                            v-model:value="mockResultOf(item).primary.score"
                            :min="0"
                            :max="6"
                            style="width: 100%;"
                          />
                        </a-form-item>
                        <a-form-item label="模拟返回文本">
                          <a-textarea
                            v-model:value="mockResultOf(item).primary.explanation"
                            :rows="2"
                            placeholder="模拟大模型返回的文本内容"
                          />
                        </a-form-item>
                      </a-form>
                    </a-card>
                    <a-card title="副模型" size="small" class="mock-card">
                      <a-form layout="vertical">
                        <a-form-item label="模拟分数">
                          <a-input-number
                            v-model:value="mockResultOf(item).secondary.score"
                            :min="0"
                            :max="6"
                            style="width: 100%;"
                          />
                        </a-form-item>
                        <a-form-item label="模拟返回文本">
                          <a-textarea
                            v-model:value="mockResultOf(item).secondary.explanation"
                            :rows="2"
                            placeholder="模拟大模型返回的文本内容"
                          />
                        </a-form-item>
                      </a-form>
                    </a-card>
                  </div>
                </div>
              </a-list-item>
            </template>
          </a-list>
        </a-tab-pane>
      </a-tabs>

      <a-button type="primary" @click="saveAll" style="margin-top: 16px;">保存</a-button>
    </div>

    <!-- 校准覆盖层 -->
    <div v-if="calibrationOverlay.visible" class="calibration-overlay" @click="onOverlayClick">
      <!-- 顶部提示栏 -->
      <div class="calibration-header">
        <span class="calibration-hint">{{ calibrationOverlay.hint }}</span>
        <a-button @click.stop="cancelCalibration" danger>取消校准</a-button>
      </div>

      <!-- 图片容器：标记点和选区框相对于此定位 -->
      <div class="calibration-img-container" ref="calibrationContainerRef">
        <!-- 截图图片 -->
        <img
          v-if="calibrationOverlay.imageUrl"
          :src="calibrationOverlay.imageUrl"
          class="calibration-image"
          @load="onImageLoad"
          ref="calibrationImageRef"
        />

        <!-- 已标记的校准点 -->
        <div
          v-for="(point, idx) in calibrationOverlay.points"
          :key="idx"
          class="calibration-point"
          :style="{
            left: point.x * calibrationOverlay.imageScale + 'px',
            top: point.y * calibrationOverlay.imageScale + 'px',
          }"
        >
          <div class="calibration-point-inner">
            {{ point.label }}
          </div>
        </div>

        <!-- 截图区域框（capture 校准时已有两点后显示） -->
        <div
          v-if="(calibrationOverlay.mode === 'capture' || calibrationOverlay.mode === 'capture_human') && calibrationOverlay.points.length === 2"
          class="calibration-rect"
          :style="{
            left: Math.min(calibrationOverlay.points[0].x, calibrationOverlay.points[1].x) * calibrationOverlay.imageScale + 'px',
            top: Math.min(calibrationOverlay.points[0].y, calibrationOverlay.points[1].y) * calibrationOverlay.imageScale + 'px',
            width: Math.abs(calibrationOverlay.points[1].x - calibrationOverlay.points[0].x) * calibrationOverlay.imageScale + 'px',
            height: Math.abs(calibrationOverlay.points[1].y - calibrationOverlay.points[0].y) * calibrationOverlay.imageScale + 'px',
          }"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import axios from 'axios'
import { message } from 'ant-design-vue'

import type { AppConfig } from '@/types/config'

const PROVIDER_DEFAULTS: Record<string, string> = {
  dashscope: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
  deepseek: 'https://api.deepseek.com',
  openai: 'https://api.openai.com/v1',
  other: ''
}

const config = ref<AppConfig>({
  llm: { provider: '', model: '', api_key: '', base_url: '', timeout: 60, max_retries: 2, prompt_template: '' },
  llm_secondary: { enabled: false, provider: '', model: '', api_key: '', base_url: '', timeout: 60, max_retries: 2, prompt_template: '' },
  mysql: { host: '', port: 3306, database: '', user: '', password: '', charset: 'utf8mb4' },
  paths: { logs: '', screenshots: '' },
  region: {
    capture: { x1: 0, y1: 0, x2: 0, y2: 0 },
    capture_human: { x1: 0, y1: 0, x2: 0, y2: 0 },
    score_buttons: [],
    clear_score: { enabled: true, x: 0, y: 0 },
    confirm_button: { x: 0, y: 0 },
  },
  http_server: { host: '0.0.0.0', port: 8081 },
  window: { auto_open_browser: true },
})

const isLoadingConfig = ref(true)

watch(
  () => config.value.llm.provider,
  (newProvider) => {
    if (isLoadingConfig.value) return
    config.value.llm.base_url = PROVIDER_DEFAULTS[newProvider] ?? ''
  }
)

watch(
  () => config.value.llm_secondary?.provider,
  (newProvider) => {
    if (isLoadingConfig.value) return
    if (config.value.llm_secondary) {
      config.value.llm_secondary.base_url = PROVIDER_DEFAULTS[newProvider ?? ''] ?? ''
    }
  }
)

const calibrationLoading = ref(false)
const calibrationImageRef = ref<HTMLImageElement | null>(null)
const calibrationContainerRef = ref<HTMLElement | null>(null)

// 校准覆盖层状态
const calibrationOverlay = reactive({
  visible: false,
  imageUrl: '',
  mode: '' as 'capture' | 'capture_human' | 'score' | 'clear_score' | 'confirm',
  scoreIndex: -1,
  hint: '',
  imageScale: 1,
  imageNaturalWidth: 0,
  imageNaturalHeight: 0,
  points: [] as Array<{ x: number; y: number; label: string }>,
})

onMounted(async () => {
  try {
    const res = await axios.get('/api/v1/config')
    config.value = res.data
    // 兼容旧配置：缺失双评/人看截图配置时补默认值，避免表单绑定 undefined
    if (!config.value.llm_secondary) {
      config.value.llm_secondary = { enabled: false, provider: '', model: '', api_key: '', base_url: '', timeout: 60, max_retries: 2, prompt_template: '' }
    }
    if (!config.value.region.capture_human) {
      config.value.region.capture_human = { x1: 0, y1: 0, x2: 0, y2: 0 }
    }
    // 若后端未保存 base_url，按当前所选提供商填入默认值；保留已保存的自定义 base_url
    if (!config.value.llm.base_url) {
      config.value.llm.base_url = PROVIDER_DEFAULTS[config.value.llm.provider] ?? ''
    }
    if (config.value.llm_secondary && !config.value.llm_secondary.base_url) {
      config.value.llm_secondary.base_url = PROVIDER_DEFAULTS[config.value.llm_secondary.provider] ?? ''
    }
  } catch (e) {
    message.error('加载配置失败')
  }
  isLoadingConfig.value = false
  try {
    const res = await axios.get('/api/v1/workflow/config')
    workflowSteps.value = res.data.workflow?.steps || []
    workflowSteps.value.forEach(ensureMockResult)
  } catch (e) {
    message.error('加载工作流配置失败')
  }
})

async function saveAll() {
  if (!config.value.llm.base_url) {
    message.warning('请输入主模型 Base URL')
    return
  }
  if (config.value.llm_secondary?.enabled && !config.value.llm_secondary.base_url) {
    message.warning('请输入副模型 Base URL')
    return
  }
  try {
    await Promise.all([
      axios.post('/api/v1/config', config.value),
      axios.post('/api/v1/workflow/config', { workflow: { steps: workflowSteps.value } }),
    ])
    message.success('保存成功')
  } catch (e) {
    message.error('保存失败')
  }
}

// ===== 工作流配置 =====
interface WorkflowStep {
  id: string
  type: string
  enabled: boolean
  delay: number
  params?: Record<string, unknown>
}

interface MockModelResult {
  score: number
  explanation: string
}

interface MockResultConfig {
  enabled: boolean
  primary: MockModelResult
  secondary: MockModelResult
}

interface VLMStepParams {
  mock_result?: MockResultConfig
}

const workflowSteps = ref<WorkflowStep[]>([])
const expandedMockIndex = ref<number | null>(null)

function mockResultOf(step: WorkflowStep): MockResultConfig {
  if (!step.params) step.params = {}
  const params = step.params as unknown as VLMStepParams
  if (!params.mock_result) {
    params.mock_result = {
      enabled: false,
      primary: { score: 0, explanation: '' },
      secondary: { score: 0, explanation: '' },
    }
  }
  return params.mock_result
}

function ensureMockResult(step: WorkflowStep): void {
  if (step.type !== 'VLMEvalStep') return
  mockResultOf(step)
}

function toggleMock(index: number): void {
  expandedMockIndex.value = expandedMockIndex.value === index ? null : index
}

const stepNameMap: Record<string, string> = {
  screenshot: '截图',
  evaluate: 'VLM评分',
  clear: '清分',
  click_score: '打分',
  confirm: '确认',
  wait: '等待',
}

const stepTypeMap: Record<string, string> = {
  ScreenshotStep: '截图步骤',
  VLMEvalStep: 'VLM评分步骤',
  ClearScoreStep: '清分步骤',
  ClickScoreStep: '打分步骤',
  ConfirmStep: '确认步骤',
  WaitStep: '等待步骤',
  ConditionStep: '条件判断',
}

function getStepName(id: string) {
  return stepNameMap[id] || id
}

function getStepType(type: string) {
  return stepTypeMap[type] || type
}

function moveStepUp(index: number) {
  if (index === 0) return
  const temp = [...workflowSteps.value]
  ;[temp[index - 1], temp[index]] = [temp[index], temp[index - 1]]
  workflowSteps.value = temp
}

function moveStepDown(index: number) {
  if (index === workflowSteps.value.length - 1) return
  const temp = [...workflowSteps.value]
  ;[temp[index], temp[index + 1]] = [temp[index + 1], temp[index]]
  workflowSteps.value = temp
}

async function simulateClick(x: number | undefined, y: number | undefined) {
  if (x == null || y == null) {
    message.warning('请先设置坐标')
    return
  }
  try {
    await axios.post('/api/v1/calibration/move-mouse', { x, y })
    message.success(`鼠标已移动到 (${x}, ${y})`)
  } catch (e) {
    message.error('移动鼠标失败')
  }
}

async function startCalibration(mode: 'capture' | 'capture_human' | 'score' | 'clear_score' | 'confirm', scoreIndex?: number) {
  calibrationLoading.value = true
  try {
    const res = await axios.post('/api/v1/calibration/screenshot')
    const { url } = res.data

    calibrationOverlay.mode = mode
    calibrationOverlay.scoreIndex = scoreIndex ?? -1
    calibrationOverlay.points = []
    calibrationOverlay.imageScale = 1

    if (mode === 'capture') {
      calibrationOverlay.hint = '请点击截图区域的左上角（第 1/2 点）'
    } else if (mode === 'capture_human') {
      calibrationOverlay.hint = '请点击【人看截图】区域的左上角（第 1/2 点）'
    } else if (mode === 'score') {
      calibrationOverlay.hint = `请点击分数 ${config.value.region.score_buttons[scoreIndex!].score} 按钮的位置`
    } else if (mode === 'clear_score') {
      calibrationOverlay.hint = '请点击清分按钮的位置'
    } else if (mode === 'confirm') {
      calibrationOverlay.hint = '请点击确认按钮的位置'
    }

    calibrationOverlay.imageUrl = url
    calibrationOverlay.visible = true
  } catch (e) {
    message.error('校准截图失败，请检查后端服务')
  } finally {
    calibrationLoading.value = false
  }
}

function onImageLoad() {
  const img = calibrationImageRef.value
  if (!img) return
  calibrationOverlay.imageNaturalWidth = img.naturalWidth
  calibrationOverlay.imageNaturalHeight = img.naturalHeight
  // 用图片实际渲染尺寸计算 scale，而不是假设占满全屏宽度
  calibrationOverlay.imageScale = img.clientWidth / img.naturalWidth
}

function onOverlayClick(e: MouseEvent) {
  if ((e.target as HTMLElement).closest('.calibration-header')) return

  const img = calibrationImageRef.value
  if (!img) return

  // 用 img 的 getBoundingClientRect 直接换算，不需要容器偏移
  const rect = img.getBoundingClientRect()
  const clickX = Math.round((e.clientX - rect.left) / calibrationOverlay.imageScale)
  const clickY = Math.round((e.clientY - rect.top) / calibrationOverlay.imageScale)

  if (calibrationOverlay.mode === 'capture') {
    handleCaptureClick(clickX, clickY)
  } else if (calibrationOverlay.mode === 'capture_human') {
    handleCaptureClick(clickX, clickY)
  } else if (calibrationOverlay.mode === 'score') {
    handleSinglePointClick(clickX, clickY, 'score')
  } else if (calibrationOverlay.mode === 'clear_score') {
    handleSinglePointClick(clickX, clickY, 'clear_score')
  } else if (calibrationOverlay.mode === 'confirm') {
    handleSinglePointClick(clickX, clickY, 'confirm')
  }
}

function handleCaptureClick(x: number, y: number) {
  const isHuman = calibrationOverlay.mode === 'capture_human'
  const areaLabel = isHuman ? '人看截图' : '截图'
  const pointCount = calibrationOverlay.points.length
  if (pointCount === 0) {
    calibrationOverlay.points.push({ x, y, label: '左上' })
    calibrationOverlay.hint = `请点击${areaLabel}区域的右下角（第 2/2 点）`
  } else if (pointCount === 1) {
    calibrationOverlay.points.push({ x, y, label: '右下' })

    const p1 = calibrationOverlay.points[0]
    const p2 = calibrationOverlay.points[1]
    const w = Math.abs(p2.x - p1.x)
    const h = Math.abs(p2.y - p1.y)

    if (w < 10 || h < 10) {
      message.warning('区域太小，请重新校准')
      calibrationOverlay.points = []
      calibrationOverlay.hint = `请点击${areaLabel}区域的左上角（第 1/2 点）`
      return
    }

    const rect = {
      x1: Math.min(p1.x, p2.x),
      y1: Math.min(p1.y, p2.y),
      x2: Math.max(p1.x, p2.x),
      y2: Math.max(p1.y, p2.y),
    }
    if (isHuman) {
      config.value.region.capture_human = rect
    } else {
      config.value.region.capture = rect
    }

    message.success(
      `${areaLabel}区域已设定: (${rect.x1}, ${rect.y1}) → (${rect.x2}, ${rect.y2})`
    )

    setTimeout(() => {
      finishCalibration()
    }, 800)
  }
}

function handleSinglePointClick(x: number, y: number, target: string) {
  calibrationOverlay.points.push({ x, y, label: '已选' })

  if (target === 'score') {
    const idx = calibrationOverlay.scoreIndex
    config.value.region.score_buttons[idx].x = x
    config.value.region.score_buttons[idx].y = y
    message.success(`分数 ${config.value.region.score_buttons[idx].score} 按钮坐标已设定: (${x}, ${y})`)
  } else if (target === 'clear_score') {
    config.value.region.clear_score.x = x
    config.value.region.clear_score.y = y
    message.success(`清分按钮坐标已设定: (${x}, ${y})`)
  } else if (target === 'confirm') {
    config.value.region.confirm_button.x = x
    config.value.region.confirm_button.y = y
    message.success(`确认按钮坐标已设定: (${x}, ${y})`)
  }

  setTimeout(() => {
    finishCalibration()
  }, 600)
}

function cancelCalibration() {
  finishCalibration()
  message.info('校准已取消')
}

function finishCalibration() {
  calibrationOverlay.visible = false
  calibrationOverlay.imageUrl = ''
  calibrationOverlay.points = []
  calibrationOverlay.hint = ''
}
</script>

<style scoped>
.calibration-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 9999;
  background: rgba(0, 0, 0, 0.85);
  cursor: crosshair;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
}

.calibration-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 12px 24px;
  background: rgba(0, 0, 0, 0.75);
}

.calibration-hint {
  color: #fff;
  font-size: 16px;
  font-weight: 500;
}

.calibration-image {
  max-width: 100vw;
  max-height: 100vh;
  object-fit: contain;
  user-select: none;
  -webkit-user-drag: none;
  display: block;
}

.calibration-img-container {
  position: relative;
  display: inline-block;
  line-height: 0;
}

.calibration-point {
  position: absolute;
  z-index: 10001;
  pointer-events: none;
  transform: translate(-50%, -50%);
}

.calibration-point-inner {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: rgba(255, 50, 50, 0.85);
  border: 2px solid #fff;
  box-shadow: 0 0 8px rgba(255, 50, 50, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  color: #fff;
  font-weight: bold;
}

.calibration-rect {
  position: absolute;
  z-index: 10000;
  pointer-events: none;
  border: 2px solid rgba(0, 255, 100, 0.8);
  background: rgba(0, 255, 100, 0.1);
}

.step-row {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
}

.step-seq {
  width: 30px;
  text-align: center;
  color: var(--color-text-secondary);
  font-weight: 600;
}

.step-id {
  width: 120px;
  font-weight: bold;
}

.step-type {
  width: 140px;
  color: var(--color-text-tertiary);
}

.step-delay {
  display: flex;
  align-items: center;
  gap: 6px;
}

.delay-label {
  font-size: 13px;
  color: var(--color-text-secondary);
}

.delay-unit {
  font-size: 13px;
  color: var(--color-text-secondary);
}

.mock-panel {
  margin-top: 12px;
  padding: 12px;
  background: #fafafa;
  border: 1px solid #f0f0f0;
  border-radius: 6px;
  width: 100%;
}

.mock-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.mock-label {
  font-size: 14px;
  color: var(--color-text-primary);
}

.mock-body {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.mock-card {
  flex: 1;
  min-width: 240px;
}
</style>
