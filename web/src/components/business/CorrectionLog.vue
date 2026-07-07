<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useCorrectionStore } from '@/stores/correction'
import { getCorrectionLogs } from '@/api/correction'

const store = useCorrectionStore()

// 一致性筛选：all=全部 / 1=一致 / 0=不一致
const consistentFilter = ref<'all' | '0' | '1'>('all')

// 关键字筛选
const keywordFilter = ref('')
watch(keywordFilter, () => {
  pagination.value.current = 1
})

// 工作流停止后再拉一次，避免最后一条记录在运行态与完成态之间出现数据缺失
watch(() => store.isRunning, (running, wasRunning) => {
  if (wasRunning && !running && pagination.value.current === 1) {
    fetchLogs()
  }
})

// 序号列
const seqColumn = { title: '序号', dataIndex: 'seq', width: 80 }

// 查看弹窗
const detailVisible = ref(false)
const currentDetail = ref<any>(null)
const currentIndex = ref(0)

// 切换上一条
const prevDetail = () => {
  if (currentIndex.value > 0) {
    currentIndex.value--
    currentDetail.value = logsWithSeq.value[currentIndex.value]
  }
}

// 切换下一条
const nextDetail = () => {
  if (currentIndex.value < logsWithSeq.value.length - 1) {
    currentIndex.value++
    currentDetail.value = logsWithSeq.value[currentIndex.value]
  }
}

// 分页配置
const pagination = ref({
  current: 1,
  pageSize: 50,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  pageSizeOptions: [10, 20, 50, 100, 200, 500],
  showTotal: (total: number) => `共 ${total} 条`
})

// 获取截图完整URL
const getScreenshotUrl = (path: string) => {
  if (!path) return ''
  const filename = path.split(/[/\\]/).pop() || ''
  return `/api/v1/screenshots/${filename}`
}

// 最终评分颜色：单评或双评一致=绿，双评不一致/失败=红
const isFinalGreen = (record: any) =>
  record.grading_mode !== 'dual' || record.score_consistent === 1

const modeText = (record: any) => (record.grading_mode === 'dual' ? '双评' : '单评')

const columns = [
  seqColumn,
  { title: '截图', dataIndex: 'screenshot', width: 160 },
  { title: '时间', dataIndex: 'time', width: 170 },
  { title: '模式', dataIndex: 'mode', width: 70 },
  { title: '主模型评分', dataIndex: 'score', width: 100 },
  { title: '副模型评分', dataIndex: 'score_secondary', width: 100 },
  { title: '最终评分', dataIndex: 'final', width: 90 },
  { title: '状态', dataIndex: 'status', width: 90 },
  { title: '操作', dataIndex: 'action', width: 70 }
]

// 按关键字过滤后的日志
const filteredLogs = computed(() => {
  const keyword = keywordFilter.value.trim().toLowerCase()
  if (!keyword) return store.logs
  return store.logs.filter((log: any) => {
    const fields = [
      String(log.screenshot || ''),
      String(log.screenshot_human || ''),
      String(log.vlm_model || ''),
      String(log.vlm_model_secondary || ''),
      String(log.status || ''),
      String(log.score ?? ''),
      String(log.score_secondary ?? ''),
      String(log.time || '')
    ]
    return fields.some(field => field.toLowerCase().includes(keyword))
  })
})

// 过滤后的总数
const filteredTotal = computed(() => filteredLogs.value.length)

// 是否处于关键字筛选模式
const isFiltering = computed(() => keywordFilter.value.trim().length > 0)

// 分页控件总数：无关键字时使用后端总数，筛选时使用本地过滤数
const paginationTotal = computed(() =>
  isFiltering.value ? filteredTotal.value : pagination.value.total
)

// 序号计算用总数：筛选时基于过滤结果，否则基于后端总数
const sequenceTotal = computed(() =>
  isFiltering.value ? filteredTotal.value : pagination.value.total
)

// 带序号的日志列表，序号从大到小排列
const logsWithSeq = computed(() => {
  const logs = filteredLogs.value
  // 计算全局序号（基于分页）
  const current = pagination.value.current
  const pageSize = pagination.value.pageSize
  const total = sequenceTotal.value
  const baseSeq = total - (current - 1) * pageSize
  return logs.map((log, index) => ({
    ...log,
    seq: baseSeq - index
  }))
})

// 提取截图文件名（优先显示尾部）
const getScreenshotName = (path: string) => {
  if (!path) return '-'
  const parts = path.split(/[/\\]/)
  const filename = parts[parts.length - 1]
  if (filename.length > 20) {
    return '...' + filename.slice(-20)
  }
  return filename
}

const fetchLogs = async () => {
  try {
    // 确保 pageSize 是数字类型
    const pageSize = Number(pagination.value.pageSize)
    const consistent = consistentFilter.value === 'all' ? undefined : consistentFilter.value
    const res: any = await getCorrectionLogs(pagination.value.current, pageSize, consistent)
    if (res.success && res.data) {
      store.setLogs(res.data)
      pagination.value.total = res.total ?? res.data.length
    }
  } catch (error) {
    console.error('获取日志失败:', error)
  }
}

// 一致性筛选变化时，回到第一页重新查询
const handleConsistentChange = () => {
  pagination.value.current = 1
  fetchLogs()
}

const showDetail = (record: any) => {
  // 找到当前记录在列表中的索引
  const index = logsWithSeq.value.findIndex((item: any) => item.seq === record.seq)
  currentIndex.value = index >= 0 ? index : 0
  currentDetail.value = record
  detailVisible.value = true
}

// 分页改变
const handlePageChange = (page: number, pageSize: number) => {
  pagination.value.current = page
  pagination.value.pageSize = Number(pageSize)
  fetchLogs()
}

onMounted(() => {
  fetchLogs()
})

onUnmounted(() => {
})
</script>

<template>
  <div class="correction-log-card">
    <div class="filter-bar">
      <span class="filter-label">一致性：</span>
      <a-radio-group v-model:value="consistentFilter" size="small" @change="handleConsistentChange">
        <a-radio-button value="all">全部</a-radio-button>
        <a-radio-button value="1">一致</a-radio-button>
        <a-radio-button value="0">不一致</a-radio-button>
      </a-radio-group>
      <span class="filter-label" style="margin-left: 16px;">关键字：</span>
      <a-input
        v-model:value="keywordFilter"
        placeholder="截图、模型、状态、分数..."
        size="small"
        style="width: 220px"
        allow-clear
      />
    </div>
    <div class="table-container">
      <a-table
        :columns="columns"
        :data-source="logsWithSeq"
        :pagination="false"
        :bordered="true"
        class="log-table"
        :size="'small'"
      >
        <template #emptyText>
          <div class="empty-state">
            <div class="empty-icon">&#xe5ef;</div>
            <div class="empty-title">暂无批改记录</div>
            <div class="empty-desc">点击"开始批改"按钮开始自动批改试卷</div>
          </div>
        </template>

        <template #bodyCell="{ column, record }">
          <template v-if="column.dataIndex === 'seq'">
            <span class="seq-cell">{{ record.seq }}</span>
          </template>
          <template v-if="column.dataIndex === 'screenshot'">
            <span class="screenshot-cell" :title="record.screenshot">{{ getScreenshotName(record.screenshot) }}</span>
          </template>
          <template v-if="column.dataIndex === 'score'">
            <span class="score-cell">{{ record.score ?? '-' }}</span>
          </template>
          <template v-if="column.dataIndex === 'mode'">
            <a-tag :color="record.grading_mode === 'dual' ? 'blue' : 'default'">{{ modeText(record) }}</a-tag>
          </template>
          <template v-if="column.dataIndex === 'score_secondary'">
            <span class="score-cell">{{ record.score_secondary ?? '-' }}</span>
          </template>
          <template v-if="column.dataIndex === 'final'">
            <span class="final-score" :class="isFinalGreen(record) ? 'final-green' : 'final-red'">
              {{ record.score ?? '-' }}
            </span>
          </template>
          <template v-if="column.dataIndex === 'status'">
            <a-tag :color="record.status === '成功' ? 'success' : record.status === '失败' ? 'error' : 'default'">
              {{ record.status || '待处理' }}
            </a-tag>
          </template>
          <template v-if="column.dataIndex === 'action'">
            <a-button type="link" size="small" @click="showDetail(record)">查看</a-button>
          </template>
        </template>
      </a-table>

      <!-- 自定义分页控件 -->
      <div class="pagination-container">
        <a-pagination
          v-model:current="pagination.current"
          v-model:pageSize="pagination.pageSize"
          :total="paginationTotal"
          :showSizeChanger="pagination.showSizeChanger"
          :showQuickJumper="pagination.showQuickJumper"
          :pageSizeOptions="pagination.pageSizeOptions"
          :showTotal="pagination.showTotal"
          @change="handlePageChange"
        />
        <span class="page-unit">页</span>
      </div>
    </div>

    <!-- 详情弹窗 -->
    <a-modal
      v-model:open="detailVisible"
      :title="`批改详情 (第 ${currentIndex + 1} / ${logsWithSeq.length} 条)`"
      :footer="null"
      width="800px"
      centered
    >
      <!-- 切换按钮 -->
      <div class="detail-navigator">
        <a-button
          type="primary"
          :disabled="currentIndex <= 0"
          @click="prevDetail"
          size="large"
        >
          &lt; 上一条
        </a-button>
        <span class="nav-info">
          序号: <strong>{{ currentDetail?.seq }}</strong>
        </span>
        <a-button
          type="primary"
          :disabled="currentIndex >= logsWithSeq.length - 1"
          @click="nextDetail"
          size="large"
        >
          下一条 &gt;
        </a-button>
      </div>

      <div v-if="currentDetail" class="detail-content">
        <div class="detail-row">
          <div class="detail-label">模型截图</div>
          <div class="detail-value">
            <img v-if="currentDetail.screenshot" :src="getScreenshotUrl(currentDetail.screenshot)" class="detail-image" alt="模型截图" />
            <span v-else>-</span>
          </div>
        </div>
        <div class="detail-row">
          <div class="detail-label">人看截图</div>
          <div class="detail-value">
            <img v-if="currentDetail.screenshot_human" :src="getScreenshotUrl(currentDetail.screenshot_human)" class="detail-image" alt="人看截图" />
            <span v-else>-</span>
          </div>
        </div>
        <div class="detail-row">
          <div class="detail-label">模式</div>
          <div class="detail-value">
            <a-tag :color="currentDetail.grading_mode === 'dual' ? 'blue' : 'default'">{{ modeText(currentDetail) }}</a-tag>
          </div>
        </div>
        <div class="detail-row">
          <div class="detail-label">主模型</div>
          <div class="detail-value">
            <div class="model-name">{{ currentDetail.vlm_model || '-' }}</div>
            <div class="vlm-text">{{ currentDetail.vlm_response || '-' }}</div>
            <div>分数：<strong>{{ currentDetail.score ?? '-' }}</strong></div>
          </div>
        </div>
        <div v-if="currentDetail.grading_mode === 'dual'" class="detail-row">
          <div class="detail-label">副模型</div>
          <div class="detail-value">
            <div class="model-name">{{ currentDetail.vlm_model_secondary || '-' }}</div>
            <div class="vlm-text">{{ currentDetail.vlm_response_secondary || '-' }}</div>
            <div>分数：<strong>{{ currentDetail.score_secondary ?? '-' }}</strong></div>
          </div>
        </div>
        <div class="detail-row">
          <div class="detail-label">最终评分</div>
          <div class="detail-value">
            <span class="final-score" :class="isFinalGreen(currentDetail) ? 'final-green' : 'final-red'">
              {{ currentDetail.score ?? '-' }}
            </span>
          </div>
        </div>
        <div v-if="currentDetail.detail" class="detail-row">
          <div class="detail-label">错误信息</div>
          <div class="detail-value error-text">{{ currentDetail.detail }}</div>
        </div>
        <div class="detail-row">
          <div class="detail-label">时间</div>
          <div class="detail-value">{{ currentDetail.time || '-' }}</div>
        </div>
      </div>
    </a-modal>

    <div class="info-tip">
      <span class="tip-icon">&#xe9d9;</span>
      <div class="tip-content">
        <div class="tip-title">数据展示示例</div>
        <div class="tip-desc">开始批改后，系统将自动记录每条批改记录，包含时间、截图预览、批改模式、主/副模型评分、最终评分和处理状态</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.correction-log-card {
  background: #ffffff;
  border: 0.9px solid #e2e8f0;
  border-radius: 12px;
  padding: 16px; /* 卡片内边距 */
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.filter-bar {
  display: flex;
  align-items: center;
  gap: 4px;
}

.filter-label {
  font-size: 13px;
  color: #64748b;
}

.table-container {
  margin-top: 12px; /* 表格上边距 */
  border: 0.9px solid #e2e8f0;
  border-radius: 8px;
  overflow: visible;
}

/* 表格样式 - 确保显示所有行 */
:deep(.ant-table) {
  max-height: none;
}

:deep(.ant-table-body) {
  max-height: none !important;
  overflow: visible !important;
}

/* 分页器样式 - 确保数字完整显示 */
:deep(.ant-pagination-options) {
  white-space: nowrap;
  flex-shrink: 0;
}

/* 下拉框宽度足够显示数字 */
:deep(.ant-pagination-options .ant-select) {
  min-width: 80px;
}

/* 选中项显示 */
:deep(.ant-pagination-options .ant-select-selection-item) {
  min-width: 50px;
  text-align: center;
}

/* 下拉选项数字完整显示 */
:deep(.ant-select-item) {
  min-width: 100% !important;
}

:deep(.ant-select-item-option-content) {
  white-space: nowrap;
  min-width: 60px;
}

/* 下拉面板 */
:deep(.ant-select-dropdown) {
  min-width: 100px !important;
}

:deep(.ant-select-dropdown .ant-select-item) {
  min-width: 100%;
}

/* 自定义分页容器 */
.pagination-container {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  margin-top: 16px;
  gap: 8px;
}

.page-unit {
  color: #666;
  font-size: 14px;
  flex-shrink: 0;
}

.log-table {
  font-size: 14px;
}

.seq-cell {
  font-weight: 600;
  color: #64748b;
  font-size: 13px;
}

.score-cell {
  font-weight: 600;
  color: #2563eb;
}

.vlm-cell {
  display: inline-block;
  max-width: 280px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #64748b;
  font-size: 13px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px 24px;
  gap: 12px;
}

.empty-icon {
  font-family: 'remixicon', sans-serif;
  font-size: 48px;
  color: #cbd5e1;
}

.empty-title {
  font-size: 14px;
  font-weight: 500;
  color: #94a3b8;
}

.empty-desc {
  font-size: 13px;
  color: #cbd5e1;
}

.info-tip {
  display: flex;
  gap: 8px;
  margin-top: 12px; /* 提示区域上边距 */
  padding: 12px; /* 提示区域内边距 */
  background-color: #eff6ff;
  border-radius: 8px;
}

.tip-icon {
  font-family: 'remixicon', sans-serif;
  font-size: 18px;
  color: #3b82f6;
}

.tip-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.tip-title {
  font-size: 13px;
  font-weight: 500;
  color: #1e40af;
}

.tip-desc {
  font-size: 12px;
  color: #3b82f6;
}

.screenshot-cell {
  font-size: 12px;
  color: #64748b;
  max-width: 160px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: inline-block;
}

.detail-content {
  padding: 8px 0;
}

/* 详情导航按钮 */
.detail-navigator {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e2e8f0;
}

.nav-info {
  font-size: 14px;
  color: #64748b;
}

.nav-info strong {
  color: #2563eb;
  font-size: 16px;
}

.detail-row {
  display: flex;
  margin-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
  padding-bottom: 12px;
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
  color: #64748b;
  font-size: 14px;
}

.detail-value {
  flex: 1;
  color: #1e293b;
  font-size: 14px;
}

.detail-image {
  max-width: 100%;
  max-height: 400px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.vlm-text {
  background-color: #f8fafc;
  padding: 12px;
  border-radius: 6px;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 200px;
  overflow-y: auto;
}

.error-text {
  background-color: #fef2f2;
  padding: 12px;
  border-radius: 6px;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 200px;
  overflow-y: auto;
  color: #991b1b;
}

.final-score { font-size: 18px; font-weight: 700; }
.final-green { color: #16a34a; }
.final-red { color: #dc2626; }
.model-name { font-weight: 600; color: #334155; margin-bottom: 4px; }
</style>
