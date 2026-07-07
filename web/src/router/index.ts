import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'CorrectionControl',
      component: () => import('@/views/CorrectionControl.vue'),
      meta: { public: true }
    },
    {
      path: '/settings',
      name: 'Settings',
      component: () => import('@/views/SettingsView.vue'),
      meta: { public: false }
    },
    {
      path: '/records',
      name: 'Records',
      component: () => import('@/views/RecordsView.vue'),
      meta: { public: true }
    },
    {
      path: '/statistics',
      name: 'Statistics',
      component: () => import('@/views/StatisticsView.vue'),
      meta: { public: true }
    },
    {
      path: '/services',
      name: 'Services',
      component: () => import('@/views/ServicesView.vue'),
      meta: { public: true }
    },
    {
      path: '/llm-test',
      name: 'LlmTest',
      component: () => import('@/views/LlmTestView.vue'),
      meta: { public: true }
    },
    {
      path: '/vlm-logs',
      name: 'VlmLogs',
      component: () => import('@/views/VlmLogsView.vue'),
      meta: { public: true }
    }
  ]
})

// 路由守卫（当前项目无认证体系，仅作日志记录，为后续扩展预留）
router.beforeEach((to, _from, next) => {
  if (to.meta && !to.meta.public) {
    console.log('[路由守卫] 访问受保护页面:', to.path)
  }
  next()
})

export default router
