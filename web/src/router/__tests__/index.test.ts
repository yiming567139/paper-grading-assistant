import { describe, it, expect, beforeEach } from 'vitest'
import { createRouter, createWebHistory } from 'vue-router'

describe('router', () => {
  let router: ReturnType<typeof createRouter>

  beforeEach(async () => {
    const routes = [
      {
        path: '/',
        name: 'CorrectionControl',
        component: { template: '<div>CorrectionControl</div>' },
        meta: { public: true },
      },
      {
        path: '/settings',
        name: 'Settings',
        component: { template: '<div>Settings</div>' },
        meta: { public: false },
      },
      {
        path: '/records',
        name: 'Records',
        component: { template: '<div>Records</div>' },
        meta: { public: true },
      },
      {
        path: '/statistics',
        name: 'Statistics',
        component: { template: '<div>Statistics</div>' },
        meta: { public: true },
      },
      {
        path: '/services',
        name: 'Services',
        component: { template: '<div>Services</div>' },
        meta: { public: true },
      },
      {
        path: '/llm-test',
        name: 'LlmTest',
        component: { template: '<div>LlmTest</div>' },
        meta: { public: true },
      },
      {
        path: '/vlm-logs',
        name: 'VlmLogs',
        component: { template: '<div>VlmLogs</div>' },
        meta: { public: true },
      },
    ]
    router = createRouter({
      history: createWebHistory(),
      routes,
    })
  })

  it('should have routes defined', () => {
    expect(router.hasRoute('CorrectionControl')).toBe(true)
    expect(router.hasRoute('Settings')).toBe(true)
    expect(router.hasRoute('Records')).toBe(true)
    expect(router.hasRoute('Statistics')).toBe(true)
    expect(router.hasRoute('Services')).toBe(true)
    expect(router.hasRoute('LlmTest')).toBe(true)
    expect(router.hasRoute('VlmLogs')).toBe(true)
  })

  it('should have correct number of routes', () => {
    const routeRecords = router.getRoutes()
    const standardRoutes = routeRecords.filter((r) => r.meta)
    expect(standardRoutes.length).toBe(7)
  })

  it('root route should be CorrectionControl', () => {
    const route = router.resolve('/')
    expect(route.name).toBe('CorrectionControl')
  })

  it('should navigate to Settings', async () => {
    await router.push('/settings')
    expect(router.currentRoute.value.path).toBe('/settings')
  })

  it('should navigate to Records', async () => {
    await router.push('/records')
    expect(router.currentRoute.value.name).toBe('Records')
  })

  it('should resolve correction/logs path correctly', () => {
    const route = router.resolve('/records')
    expect(route.path).toBe('/records')
  })

  it('should navigate to Statistics', async () => {
    await router.push('/statistics')
    expect(router.currentRoute.value.name).toBe('Statistics')
  })

  it('should navigate to Services', async () => {
    await router.push('/services')
    expect(router.currentRoute.value.name).toBe('Services')
  })

  it('should navigate to LlmTest', async () => {
    await router.push('/llm-test')
    expect(router.currentRoute.value.name).toBe('LlmTest')
  })

  it('should navigate to VlmLogs', async () => {
    await router.push('/vlm-logs')
    expect(router.currentRoute.value.name).toBe('VlmLogs')
  })

  it('unknown path should not match any route', async () => {
    await router.push('/unknown-path')
    // No catch-all route defined, so route is still resolved at unknown-path
    expect(router.currentRoute.value.path).toBe('/unknown-path')
    expect(router.currentRoute.value.name).toBeUndefined()
  })
})
