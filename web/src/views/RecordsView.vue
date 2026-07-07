<template>
  <div class="page">
    <div class="page-header">
      <div>
        <div class="page-title"><span class="title-accent"></span>历史记录</div>
        <div class="page-subtitle">查看全部批改记录与主副模型评分一致性</div>
      </div>
    </div>
    <div class="ui-card" style="padding: 16px;">
      <a-alert v-if="dbError" :message="dbError" type="warning" show-icon style="margin-bottom: 16px;" />
      <div style="margin-bottom: 16px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
        <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
          <span style="color: var(--color-text-secondary); font-size: 0.875rem;">一致性：</span>
          <a-radio-group v-model:value="consistentFilter" @change="fetchRecords">
            <a-radio-button value="all">全部</a-radio-button>
            <a-radio-button value="1">一致</a-radio-button>
            <a-radio-button value="0">不一致</a-radio-button>
          </a-radio-group>
        </div>
        <span style="color: var(--color-text-secondary); font-size: 0.875rem;">共 {{ records.length }} 条</span>
      </div>
      <a-table :dataSource="records" :columns="columns" :pagination="{ pageSize: 50 }" rowKey="id">
        <template #bodyCell="{ column, record }">
          <template v-if="column.dataIndex === 'grading_mode'">
            <a-tag :color="record.grading_mode === 'dual' ? 'blue' : 'default'">
              {{ record.grading_mode === 'dual' ? '双评' : '单评' }}
            </a-tag>
          </template>
          <template v-if="column.dataIndex === 'final'">
            <span :class="isFinalGreen(record) ? 'final-green' : 'final-red'" style="font-weight:700;">
              {{ record.score ?? '-' }}
            </span>
          </template>
        </template>
      </a-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import request from '@/utils/request'
import type { CorrectionLog } from '@/types/correction'
import type { ApiResponse } from '@/utils/request'

const records = ref<any[]>([])
const dbError = ref('')
const consistentFilter = ref<'all' | '0' | '1'>('all')

const columns = [
  { title: 'ID', dataIndex: 'id' },
  { title: '批次ID', dataIndex: 'batch_id' },
  { title: '模式', dataIndex: 'grading_mode' },
  { title: '主模型分', dataIndex: 'score' },
  { title: '副模型分', dataIndex: 'score_secondary' },
  { title: '最终评分', dataIndex: 'final' },
  { title: '状态', dataIndex: 'status' },
  { title: '模型', dataIndex: 'vlm_model' },
  { title: '耗时(ms)', dataIndex: 'duration_ms' },
  { title: '时间', dataIndex: 'created_at' },
]

const isFinalGreen = (record: any) =>
  record.grading_mode !== 'dual' || record.score_consistent === 1

const fetchRecords = async () => {
  try {
    const params: Record<string, any> = {}
    if (consistentFilter.value !== 'all') params.consistent = consistentFilter.value
    const res: ApiResponse<CorrectionLog[]> = await request.get('/records', { params })
    records.value = (res.data as any[]) || []
    dbError.value = ''
  } catch (error) {
    const err = error as { response?: { status: number }; message?: string }
    if (err?.response?.status === 503) {
      dbError.value = '数据库未连接，请先在系统设置中配置 MySQL 连接信息'
    } else {
      dbError.value = '加载记录失败: ' + (err?.message || '未知错误')
    }
  }
}

onMounted(fetchRecords)
</script>

<style scoped>
.final-green { color: var(--color-success); font-weight: bold; }
.final-red { color: var(--color-danger); font-weight: bold; }
</style>
