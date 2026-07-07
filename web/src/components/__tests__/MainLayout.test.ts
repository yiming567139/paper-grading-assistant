import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'

// Mock @ant-design/icons-vue
vi.mock('@ant-design/icons-vue', () => ({
  EditOutlined: { template: '<span>EditOutlined</span>' },
  SettingOutlined: { template: '<span>SettingOutlined</span>' },
  HistoryOutlined: { template: '<span>HistoryOutlined</span>' },
  BarChartOutlined: { template: '<span>BarChartOutlined</span>' },
  CloudServerOutlined: { template: '<span>CloudServerOutlined</span>' },
  ExperimentOutlined: { template: '<span>ExperimentOutlined</span>' },
  FileSearchOutlined: { template: '<span>FileSearchOutlined</span>' },
  MenuFoldOutlined: { template: '<span>MenuFoldOutlined</span>' },
  MenuUnfoldOutlined: { template: '<span>MenuUnfoldOutlined</span>' },
}))

describe('MainLayout', () => {
  let router: ReturnType<typeof createRouter>

  beforeEach(async () => {
    router = createRouter({
      history: createWebHistory(),
      routes: [
        {
          path: '/',
          name: 'home',
          component: { template: '<div>Home</div>' },
        },
      ],
    })
  })

  it('should render component', async () => {
    const MainLayout = (await import('@/components/layout/MainLayout.vue')).default
    const wrapper = mount(MainLayout, {
      global: {
        plugins: [router],
        stubs: {
          'a-layout': { template: '<div><slot /></div>' },
          'a-layout-sider': { template: '<div><slot /></div>' },
          'a-menu': { template: '<div><slot /></div>' },
          'a-menu-item': { template: '<div><slot /></div>' },
          'a-layout-content': { template: '<div><slot /></div>' },
          'router-view': { template: '<div>Content</div>' },
        },
      },
    })
    expect(wrapper.exists()).toBe(true)
  })

  it('should display logo text', async () => {
    const MainLayout = (await import('@/components/layout/MainLayout.vue')).default
    const wrapper = mount(MainLayout, {
      global: {
        plugins: [router],
        stubs: {
          'a-layout': { template: '<div><slot /></div>' },
          'a-layout-sider': { template: '<div><slot /></div>' },
          'a-menu': { template: '<div><slot /></div>' },
          'a-menu-item': { template: '<div><slot /></div>' },
          'a-layout-content': { template: '<div><slot /></div>' },
          'router-view': { template: '<div>Content</div>' },
        },
      },
    })
    expect(wrapper.text()).toContain('试卷批改系统')
  })

  it('should display AI tag in header', async () => {
    const MainLayout = (await import('@/components/layout/MainLayout.vue')).default
    const wrapper = mount(MainLayout, {
      global: {
        plugins: [router],
        stubs: {
          'a-layout': { template: '<div><slot /></div>' },
          'a-layout-sider': { template: '<div><slot /></div>' },
          'a-menu': { template: '<div><slot /></div>' },
          'a-menu-item': { template: '<div><slot /></div>' },
          'a-layout-content': { template: '<div><slot /></div>' },
          'router-view': { template: '<div>Content</div>' },
        },
      },
    })
    expect(wrapper.text()).toContain('AI 智能批改')
  })
})
