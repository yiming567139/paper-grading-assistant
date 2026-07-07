<template>
  <div class="page">
    <div class="page-header">
      <div>
        <div class="page-title"><span class="title-accent"></span>服务状态</div>
        <div class="page-subtitle">查看后端服务与依赖运行状况</div>
      </div>
    </div>

    <div class="ui-card" style="padding: 16px;">
      <a-descriptions bordered :column="1">
        <a-descriptions-item label="后端状态">
          <a-tag color="green">运行中</a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="API 版本">2.0.0</a-descriptions-item>
        <a-descriptions-item label="LLM 提供商">
          <span v-if="loading">加载中...</span>
          <span v-else>{{ config.llm?.provider || '未配置' }}</span>
        </a-descriptions-item>
        <a-descriptions-item label="LLM 模型">
          <span v-if="loading">加载中...</span>
          <span v-else>{{ config.llm?.model || '未配置' }}</span>
        </a-descriptions-item>
        <a-descriptions-item label="工作流状态">
          <span v-if="loading">加载中...</span>
          <a-tag v-else :color="workflowStatusColor">{{ workflowStatusText }}</a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="当前批次">
          <span v-if="loading">加载中...</span>
          <span v-else>{{ workflowStatus.batch_id ?? '无' }}</span>
        </a-descriptions-item>
      </a-descriptions>

      <div style="margin-top: 16px; display: flex; gap: 12px;">
        <a-button @click="refreshStatus" :loading="loading">刷新状态</a-button>
        <a-button type="primary" @click="testLlm" :loading="testingLlm">测试 LLM 连接</a-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { message } from 'ant-design-vue'

const config = ref<any>({})
const workflowStatus = ref<any>({})
const loading = ref(false)
const testingLlm = ref(false)

const workflowStatusText = computed(() => {
  if (workflowStatus.value.is_running && workflowStatus.value.is_paused) {
    return '已暂停'
  }
  if (workflowStatus.value.is_running) {
    return '运行中'
  }
  return '已停止'
})

const workflowStatusColor = computed(() => {
  if (workflowStatus.value.is_running && workflowStatus.value.is_paused) {
    return 'orange'
  }
  if (workflowStatus.value.is_running) {
    return 'green'
  }
  return 'default'
})

async function refreshStatus() {
  loading.value = true
  try {
    const [configRes, statusRes] = await Promise.all([
      axios.get('/api/v1/config'),
      axios.get('/api/v1/workflow/status')
    ])
    config.value = configRes.data
    workflowStatus.value = statusRes.data
  } catch (e) {
    message.error('加载状态失败')
  } finally {
    loading.value = false
  }
}

async function testLlm() {
  testingLlm.value = true
  try {
    const res = await axios.post('/api/v1/llm/test', {
      provider: config.value.llm?.provider || '',
      api_key: config.value.llm?.api_key || '',
      model: config.value.llm?.model || ''
    })
    if (res.data.success) {
      message.success(res.data.message || 'LLM 连接测试成功')
    } else {
      message.error(res.data.message || 'LLM 连接测试失败')
    }
  } catch (e) {
    message.error('LLM 连接测试请求失败')
  } finally {
    testingLlm.value = false
  }
}

onMounted(() => {
  refreshStatus()
})
</script>
