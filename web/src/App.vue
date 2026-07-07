<script setup lang="ts">
import { theme } from 'ant-design-vue'
import MainLayout from './components/layout/MainLayout.vue'

// Ocean Blue 主题令牌（与 style.css 中的 CSS 变量保持一致）
const themeConfig = {
  token: {
    colorPrimary: '#0284c7',
    colorInfo: '#0284c7',
    colorSuccess: '#16a34a',
    colorWarning: '#d97706',
    colorError: '#dc2626',
    colorTextBase: '#0f172a',
    borderRadius: 10,
    fontFamily:
      "'Inter', 'Source Han Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Microsoft YaHei', sans-serif",
  },
  algorithm: theme.defaultAlgorithm,
}
</script>

<template>
  <a-config-provider :theme="themeConfig">
    <MainLayout>
      <router-view />
    </MainLayout>
  </a-config-provider>
</template>
