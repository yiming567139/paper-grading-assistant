<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { message } from 'ant-design-vue'
import type { VlmLog } from '@/types/vlm'

const logs = ref<VlmLog[]>([])
const loading = ref(false)
const detailVisible = ref(false)
const currentDetail = ref<VlmLog | null>(null)

const pagination = ref({
  current: 1,
  pageSize: 50,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  pageSizeOptions: [10, 20, 50, 100],
  showTotal: (total: number) => `共 ${total} 条`
})

const logsWithSeq = computed(() => {
  const current = pagination.value.current
  const pageSize = pagination.value.pageSize
  const total = pagination.value.total
  const baseSeq = total - (current - 1) * pageSize
  return logs.value.map((log, index) => ({
    ...log,
    seq: baseSeq - index
  }))
})

const columns = [
  { title: '序号', dataIndex: 'seq', width: 70 },
  { title: '调用时间', dataIndex: 'created_at', width: 180 },
  { title: '模型', dataIndex: 'model', width: 180 },
  { title: '提供商', dataIndex: 'provider', width: 100 },
  { title: '评分', dataIndex: 'score', width: 70 },
  { title: '耗时', dataIndex: 'duration_ms', width: 90 },
  { title: '状态', dataIndex: 'status', width: 80 },
  { title: '操作', dataIndex: 'action', width: 80 }
]

async function fetchLogs() {
  loading.value = true
  try {
    const res = await axios.get('/api/v1/vlm-logs', {
      params: { page: pagination.value.current, page_size: pagination.value.pageSize }
    })
    logs.value = res.data.data || []
    pagination.value.total = res.data.total || 0
  } catch (e) {
    message.error('加载 VLM 日志失败')
  } finally {
    loading.value = false
  }
}

function showDetail(record: VlmLog) {
  currentDetail.value = record
  detailVisible.value = true
}

function handlePageChange(page: number, pageSize: number) {
  pagination.value.current = page
  pagination.value.pageSize = pageSize
  fetchLogs()
}

function formatDuration(ms: number) {
  if (!ms) return '-'
  return ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${ms}ms`
}

function formatDateTime(value: string | undefined): string {
  if (!value) return '-'
  const date = new Date(value)
  if (isNaN(date.getTime())) return value
  const pad = (n: number) => n.toString().padStart(2, '0')
  const yyyy = date.getFullYear()
  const MM = pad(date.getMonth() + 1)
  const dd = pad(date.getDate())
  const HH = pad(date.getHours())
  const mm = pad(date.getMinutes())
  const ss = pad(date.getSeconds())
  return `${yyyy}-${MM}-${dd} ${HH}:${mm}:${ss}`
}

onMounted(() => {
  fetchLogs()
})
</script>

<template>
  <div class="page">
    <div class="page-header">
      <div>
        <div class="page-title"><span class="title-accent"></span>VLM 日志</div>
        <div class="page-subtitle">查看每次模型调用的请求与响应</div>
      </div>
    </div>

    <div class="ui-card" style="padding: 16px;">
      <a-table
        :columns="columns"
        :data-source="logsWithSeq"
        :loading="loading"
        :pagination="false"
        :bordered="true"
        size="small"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.dataIndex === 'seq'">
            <span style="font-weight: 600; color: var(--color-text-secondary);">{{ record.seq }}</span>
          </template>
          <template v-if="column.dataIndex === 'created_at'">
            {{ formatDateTime(record.created_at) }}
          </template>
          <template v-if="column.dataIndex === 'score'">
            <span style="font-weight: 700; color: var(--color-primary);">{{ record.score ?? '-' }}</span>
          </template>
          <template v-if="column.dataIndex === 'duration_ms'">
            {{ formatDuration(record.duration_ms) }}
          </template>
          <template v-if="column.dataIndex === 'status'">
            <a-tag :color="record.status === 'success' ? 'success' : 'error'">
              {{ record.status === 'success' ? '成功' : '失败' }}
            </a-tag>
          </template>
          <template v-if="column.dataIndex === 'action'">
            <a-button type="link" size="small" @click="showDetail(record)">查看</a-button>
          </template>
        </template>
      </a-table>

      <div style="display: flex; align-items: center; justify-content: flex-end; margin-top: 16px; gap: 8px;">
        <a-pagination
          v-model:current="pagination.current"
          v-model:pageSize="pagination.pageSize"
          :total="pagination.total"
          :showSizeChanger="pagination.showSizeChanger"
          :showQuickJumper="pagination.showQuickJumper"
          :pageSizeOptions="pagination.pageSizeOptions"
          :showTotal="pagination.showTotal"
          @change="handlePageChange"
        />
        <span style="color: var(--color-text-secondary); font-size: 14px;">页</span>
      </div>
    </div>

    <!-- 详情弹窗 -->
    <a-modal
      v-model:open="detailVisible"
      title="VLM 调用详情"
      :footer="null"
      width="800px"
      centered
    >
      <div v-if="currentDetail" style="padding: 8px 0;">
        <div class="detail-row">
          <div class="detail-label">模型</div>
          <div class="detail-value">{{ currentDetail.model || '-' }}</div>
        </div>
        <div class="detail-row">
          <div class="detail-label">提供商</div>
          <div class="detail-value">{{ currentDetail.provider || '-' }}</div>
        </div>
        <div class="detail-row">
          <div class="detail-label">Base URL</div>
          <div class="detail-value" style="word-break: break-all;">{{ currentDetail.base_url || '-' }}</div>
        </div>
        <div class="detail-row">
          <div class="detail-label">评分</div>
          <div class="detail-value" style="font-size: 24px; font-weight: 700; color: var(--color-primary);">{{ currentDetail.score ?? '-' }}</div>
        </div>
        <div class="detail-row">
          <div class="detail-label">耗时</div>
          <div class="detail-value">{{ formatDuration(currentDetail.duration_ms) }}</div>
        </div>
        <div class="detail-row">
          <div class="detail-label">截图路径</div>
          <div class="detail-value" style="word-break: break-all;">{{ currentDetail.image_path || '-' }}</div>
        </div>
        <div class="detail-row">
          <div class="detail-label">提示词</div>
          <div class="detail-value prompt-text">{{ currentDetail.prompt || '-' }}</div>
        </div>
        <div class="detail-row">
          <div class="detail-label">模型原文</div>
          <div class="detail-value response-text">{{ currentDetail.raw_response || '-' }}</div>
        </div>
        <div v-if="currentDetail.error_message" class="detail-row">
          <div class="detail-label">错误信息</div>
          <div class="detail-value error-text">{{ currentDetail.error_message }}</div>
        </div>
        <div class="detail-row">
          <div class="detail-label">调用时间</div>
          <div class="detail-value">{{ formatDateTime(currentDetail.created_at) }}</div>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<style scoped>
.detail-row {
  display: flex;
  margin-bottom: 14px;
  border-bottom: 1px solid var(--color-border);
  padding-bottom: 10px;
}

.detail-row:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.detail-label {
  width: 80px;
  flex-shrink: 0;
  font-weight: 600;
  color: var(--color-text-secondary);
  font-size: 14px;
}

.detail-value {
  flex: 1;
  color: var(--color-text);
  font-size: 14px;
}

.prompt-text,
.response-text {
  background-color: var(--color-surface-muted);
  padding: 12px;
  border-radius: var(--radius-sm);
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 200px;
  overflow-y: auto;
}

.error-text {
  background-color: var(--color-danger-soft);
  padding: 12px;
  border-radius: var(--radius-sm);
  color: var(--color-danger);
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
