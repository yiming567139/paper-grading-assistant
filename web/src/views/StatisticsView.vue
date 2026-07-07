<template>
  <div class="page">
    <div class="page-header">
      <div>
        <div class="page-title"><span class="title-accent"></span>统计报表</div>
        <div class="page-subtitle">批改数据与评分分布概览</div>
      </div>
    </div>

    <div class="ui-card" style="padding: 16px;">
      <!-- 查询区域 -->
      <div style="margin-bottom: 24px; display: flex; align-items: center; gap: 12px;">
        <a-range-picker
          v-model:value="dateRange"
          format="YYYY-MM-DD"
          :placeholder="['开始日期', '结束日期']"
        />
        <a-button type="primary" :loading="loading" @click="fetchStatistics">查询</a-button>
      </div>

      <!-- 统计卡片 -->
      <div v-if="hasData" style="display: flex; gap: 16px; margin-bottom: 24px;">
        <a-card style="flex: 1;">
          <a-statistic title="总批改数" :value="summary.total" />
        </a-card>
        <a-card style="flex: 1;">
          <a-statistic title="成功数" :value="summary.success" />
        </a-card>
        <a-card style="flex: 1;">
          <a-statistic title="成功率" :value="summary.rate" suffix="%" />
        </a-card>
      </div>

      <!-- 数据表格 -->
      <a-table
        v-if="hasData"
        :dataSource="tableData"
        :columns="columns"
        :pagination="false"
        row-key="date"
      />

      <!-- 无数据提示 -->
      <a-empty v-if="!hasData && !loading" description="暂无数据，请选择日期范围后查询" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Dayjs } from 'dayjs'
import request from '@/utils/request'

// 日期范围
const dateRange = ref<[Dayjs, Dayjs] | null>(null)

// 加载状态
const loading = ref(false)

// 按日统计数据
const dailyList = ref<Array<{ date: string; total: number; success: number }>>([])

// 是否有数据
const hasData = computed(() => dailyList.value.length > 0)

// 汇总统计
const summary = computed(() => {
  const total = dailyList.value.reduce((sum, item) => sum + item.total, 0)
  const success = dailyList.value.reduce((sum, item) => sum + item.success, 0)
  const rate = total > 0 ? Number(((success / total) * 100).toFixed(1)) : 0
  return { total, success, rate }
})

// 表格数据：为每行计算成功率
const tableData = computed(() =>
  dailyList.value.map((item) => ({
    ...item,
    rate: item.total > 0 ? `${((item.success / item.total) * 100).toFixed(1)}%` : '0.0%'
  }))
)

// 表格列定义
const columns = [
  { title: '日期', dataIndex: 'date', key: 'date' },
  { title: '总批改数', dataIndex: 'total', key: 'total' },
  { title: '成功数', dataIndex: 'success', key: 'success' },
  { title: '成功率', dataIndex: 'rate', key: 'rate' }
]

// 查询统计接口
const fetchStatistics = async () => {
  if (!dateRange.value) return

  const [start, end] = dateRange.value
  loading.value = true
  try {
    const res: any = await request.get('/statistics', {
      params: {
        start_date: start.format('YYYY-MM-DD'),
        end_date: end.format('YYYY-MM-DD')
      }
    })
    dailyList.value = res.data || []
  } catch {
    dailyList.value = []
  } finally {
    loading.value = false
  }
}
</script>
