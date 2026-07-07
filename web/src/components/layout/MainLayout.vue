<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  EditOutlined,
  SettingOutlined,
  HistoryOutlined,
  BarChartOutlined,
  CloudServerOutlined,
  ExperimentOutlined,
  FileSearchOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined
} from '@ant-design/icons-vue'

const route = useRoute()
const router = useRouter()

// 侧边栏折叠状态
const collapsed = ref(false)

// 当前选中的菜单项（根据路由路径自动匹配）
const selectedKeys = computed(() => [route.path])

// 菜单项配置
const menuItems = [
  { key: '/', label: '批改控制台', icon: EditOutlined },
  { key: '/settings', label: '系统设置', icon: SettingOutlined },
  { key: '/records', label: '历史记录', icon: HistoryOutlined },
  { key: '/statistics', label: '统计报表', icon: BarChartOutlined },
  { key: '/services', label: '服务状态', icon: CloudServerOutlined },
  { key: '/llm-test', label: '模型识别测试', icon: ExperimentOutlined },
  { key: '/vlm-logs', label: 'VLM日志', icon: FileSearchOutlined }
]

// 当前页标题
const currentTitle = computed(() => {
  const item = menuItems.find((m) => m.key === route.path)
  return item ? item.label : '试卷批改系统'
})

// 点击菜单项导航
function onMenuClick({ key }: { key: string }) {
  router.push(key)
}
</script>

<template>
  <a-layout class="main-layout">
    <a-layout-sider
      v-model:collapsed="collapsed"
      :width="224"
      :collapsed-width="72"
      class="app-sider"
    >
      <div class="logo">
        <div class="logo-badge">阅</div>
        <span v-if="!collapsed" class="logo-text">试卷批改系统</span>
      </div>
      <a-menu
        mode="inline"
        class="app-menu"
        :selected-keys="selectedKeys"
        @click="onMenuClick"
      >
        <a-menu-item v-for="item in menuItems" :key="item.key">
          <component :is="item.icon" />
          <span>{{ item.label }}</span>
        </a-menu-item>
      </a-menu>
    </a-layout-sider>

    <a-layout>
      <header class="app-header">
        <div class="header-left">
          <component
            :is="collapsed ? MenuUnfoldOutlined : MenuFoldOutlined"
            class="collapse-btn"
            @click="collapsed = !collapsed"
          />
          <span class="header-title">{{ currentTitle }}</span>
        </div>
        <div class="header-right">
          <span class="header-tag">AI 智能批改</span>
        </div>
      </header>

      <a-layout-content class="layout-content">
        <slot />
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<style scoped>
.main-layout {
  height: 100vh;
  overflow: hidden;
}

/* ===== 侧边栏 ===== */
.app-sider {
  height: 100vh;
  background: linear-gradient(180deg, #0b2942 0%, #0f172a 100%) !important;
  box-shadow: 2px 0 16px rgba(15, 23, 42, 0.12);
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.logo-badge {
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
  box-shadow: 0 4px 12px rgba(14, 165, 233, 0.45);
}

.logo-text {
  color: #f1f5f9;
  font-size: 16px;
  font-weight: 600;
  white-space: nowrap;
  letter-spacing: 0.5px;
}

/* 菜单：深色背景 + Ocean Blue 选中态 */
.app-menu {
  background: transparent !important;
  border-inline-end: none !important;
  padding: 12px 10px;
  overflow-y: auto;
  height: calc(100vh - 60px);
}

.app-menu :deep(.ant-menu-item) {
  color: #94a3b8;
  border-radius: 10px;
  margin: 4px 0;
  height: 44px;
  line-height: 44px;
  transition: all 0.2s ease;
}

.app-menu :deep(.ant-menu-item .anticon) {
  font-size: 17px;
}

.app-menu :deep(.ant-menu-item:hover) {
  color: #e2e8f0 !important;
  background: rgba(255, 255, 255, 0.06) !important;
}

.app-menu :deep(.ant-menu-item-selected) {
  color: #fff !important;
  background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%) !important;
  box-shadow: 0 6px 16px rgba(2, 132, 199, 0.4);
}

/* ===== 顶部 header ===== */
.app-header {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--color-border);
  position: sticky;
  top: 0;
  z-index: 20;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.collapse-btn {
  font-size: 18px;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: color 0.2s;
}
.collapse-btn:hover {
  color: var(--color-primary);
}

.header-title {
  font-size: 17px;
  font-weight: 600;
  color: var(--color-text);
}

.header-tag {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-primary);
  background: var(--color-primary-soft);
  padding: 5px 12px;
  border-radius: var(--radius-pill);
}

.layout-content {
  background-color: var(--color-bg);
  height: calc(100vh - 60px);
  overflow-y: auto;
}
</style>
