<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { evaluateImage } from '@/api/correction'
import { message } from 'ant-design-vue'
import { UploadOutlined, SendOutlined } from '@ant-design/icons-vue'

const PROVIDER_DEFAULTS: Record<string, string> = {
  dashscope: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
  deepseek: 'https://api.deepseek.com',
  openai: 'https://api.openai.com/v1',
  other: ''
}

interface LLMConfig {
  provider: string
  api_key: string
  model: string
  base_url: string
  timeout: number
}

const llmConfig = reactive<LLMConfig>({
  provider: 'dashscope',
  api_key: '',
  model: 'qwen-vl-plus',
  base_url: '',
  timeout: 60
})

watch(
  () => llmConfig.provider,
  (newProvider) => {
    llmConfig.base_url = PROVIDER_DEFAULTS[newProvider] ?? ''
  },
  { immediate: true }
)

const prompt = ref('')
const fileList = ref<any[]>([])
const uploading = ref(false)
const result = ref('')
const resultImage = ref('')

const handleFileChange = (info: any) => {
  fileList.value = info.fileList.slice(-1)
  if (info.file && info.file.originFileObj) {
    const reader = new FileReader()
    reader.onload = (e) => {
      resultImage.value = e.target?.result as string
    }
    reader.readAsDataURL(info.file.originFileObj)
  }
}

const handleSubmit = async () => {
  if (!fileList.value.length) {
    message.warning('请先上传图片')
    return
  }
  if (!llmConfig.api_key) {
    message.warning('请输入 API Key')
    return
  }
  if (!llmConfig.base_url) {
    message.warning('请输入 Base URL')
    return
  }
  if (!prompt.value) {
    message.warning('请输入提示词')
    return
  }

  uploading.value = true
  result.value = ''

  try {
    const file = fileList.value[0].originFileObj
    const formData = new FormData()
    formData.append('image', file)
    formData.append('config', JSON.stringify(llmConfig))
    formData.append('prompt', prompt.value)

    const res: any = await evaluateImage(formData)
    if (res.success) {
      result.value = res.raw_response || ''
      message.success('识别成功')
    } else {
      result.value = ''
      message.error(res.error || '识别失败')
    }
  } catch (error) {
    message.error('请求失败: ' + String(error))
  } finally {
    uploading.value = false
  }
}
</script>

<template>
  <div class="page">
    <div class="page-header">
      <div>
        <div class="page-title"><span class="title-accent"></span>模型识别测试</div>
        <div class="page-subtitle">上传截图，测试大模型识别与评分</div>
      </div>
    </div>

    <div class="ui-card" style="padding: 16px;">
      <a-row :gutter="24">
        <!-- 左侧：配置 + 输入 -->
        <a-col :xs="24" :lg="10">
          <div class="left-section">
            <!-- LLM 临时配置 -->
            <div class="section-title">临时 LLM 配置</div>
            <a-form :model="llmConfig" layout="vertical" size="small">
              <a-form-item label="提供商">
                <a-select v-model:value="llmConfig.provider">
                <a-select-option value="dashscope">阿里百炼</a-select-option>
                <a-select-option value="deepseek">DeepSeek</a-select-option>
                <a-select-option value="openai">OpenAI</a-select-option>
                <a-select-option value="other">其他</a-select-option>
                </a-select>
              </a-form-item>
              <a-form-item label="API Key">
                <a-input-password v-model:value="llmConfig.api_key" placeholder="输入临时 API Key" />
              </a-form-item>
              <a-form-item label="模型">
                <a-input v-model:value="llmConfig.model" placeholder="如 qwen-vl-plus" />
              </a-form-item>
              <a-form-item label="Base URL（必填）">
                <a-input v-model:value="llmConfig.base_url" placeholder="请选择或输入 Base URL" />
              </a-form-item>
              <a-form-item label="超时时间（秒）">
                <a-input-number v-model:value="llmConfig.timeout" :min="5" :max="300" style="width: 100%" />
              </a-form-item>
            </a-form>

            <a-divider />

            <!-- 图片上传 -->
            <div class="section-title">上传图片</div>
            <a-upload
              v-model:file-list="fileList"
              :before-upload="() => false"
              :max-count="1"
              accept="image/*"
              list-type="picture-card"
              @change="handleFileChange"
            >
              <div v-if="fileList.length < 1">
                <UploadOutlined />
                <div style="margin-top: 8px">点击上传</div>
              </div>
            </a-upload>

            <!-- 提示词 -->
            <div class="section-title" style="margin-top: 16px">提示词</div>
            <a-textarea
              v-model:value="prompt"
              :rows="4"
              placeholder="输入提示词，例如：你是一个初中化学阅卷老师。请根据图片中的试卷答案，给出0-6分的整数评分。"
            />

            <!-- 执行按钮 -->
            <a-button
              type="primary"
              size="large"
              :loading="uploading"
              :disabled="!fileList.length || !llmConfig.api_key || !llmConfig.base_url || !prompt"
              style="margin-top: 16px; width: 100%"
              @click="handleSubmit"
            >
              <template #icon><SendOutlined /></template>
              执行识别
            </a-button>
          </div>
        </a-col>

        <!-- 右侧：结果展示 -->
        <a-col :xs="24" :lg="14">
          <div class="right-section">
            <div class="section-title">识别结果</div>

            <!-- 预览图 -->
            <div v-if="resultImage" class="preview-box">
              <img :src="resultImage" class="preview-image" alt="预览" />
            </div>

            <!-- 原始响应 -->
            <div class="result-box">
              <div v-if="!result && !uploading" class="result-placeholder">
                点击「执行识别」后，大模型返回的内容将展示在这里
              </div>
              <div v-else-if="uploading" class="result-loading">
                <a-spin /> 识别中...
              </div>
              <pre v-else class="result-text">{{ result }}</pre>
            </div>
          </div>
        </a-col>
      </a-row>
    </div>
  </div>
</template>

<style scoped>
.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-secondary);
  margin-bottom: 12px;
}

.left-section {
  padding-right: 8px;
}

.right-section {
  padding-left: 8px;
}

.preview-box {
  margin-bottom: 16px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  overflow: hidden;
  background: var(--color-surface);
}

.preview-image {
  width: 100%;
  max-height: 300px;
  object-fit: contain;
  display: block;
}

.result-box {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface-muted);
  min-height: 200px;
  padding: 16px;
}

.result-placeholder {
  color: var(--color-text-tertiary);
  font-size: 14px;
  text-align: center;
  padding: 40px 0;
}

.result-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: var(--color-text-secondary);
  font-size: 14px;
  padding: 40px 0;
}

.result-text {
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-text);
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 400px;
  overflow-y: auto;
}
</style>
