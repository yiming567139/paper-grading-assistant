import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'

// Mock API modules with resolved values
vi.mock('@/api/correction', () => ({
  startCorrection: vi.fn().mockResolvedValue({ status: 'started' }),
  stopCorrection: vi.fn().mockResolvedValue({ status: 'stopped' }),
  getCorrectionLogs: vi.fn().mockResolvedValue({ success: true, data: [], total: 0 }),
  getCorrectionStatus: vi.fn().mockResolvedValue({
    is_running: false,
    batch_limit: 0,
    completed_count: 0,
    dual_grading: false,
    primary_model: '',
    secondary_model: '',
    current_step: '',
  }),
}))

// Mock ant-design-vue message
vi.mock('ant-design-vue', () => ({
  message: {
    info: vi.fn(),
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
  },
}))

describe('ProcessControl', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('should render component with default status', async () => {
    const ProcessControl = (await import('@/components/business/ProcessControl.vue')).default
    const wrapper = mount(ProcessControl, {
      global: {
        stubs: {
          'a-button': { template: '<button><slot /></button>' },
          'a-input-number': { template: '<input class="mock-input-number" />' },
        },
      },
    })
    // Wait for onMounted effects to settle
    await new Promise((r) => setTimeout(r, 50))
    expect(wrapper.exists()).toBe(true)
    expect(wrapper.text()).toContain('开始')
  })

  it('should show step progress labels', async () => {
    const ProcessControl = (await import('@/components/business/ProcessControl.vue')).default
    const wrapper = mount(ProcessControl, {
      global: {
        stubs: {
          'a-button': { template: '<button><slot /></button>' },
          'a-input-number': { template: '<input class="mock-input-number" />' },
        },
      },
    })
    await new Promise((r) => setTimeout(r, 50))
    const text = wrapper.text()
    expect(text).toContain('截图')
    expect(text).toContain('VLM评分')
    expect(text).toContain('清分')
    expect(text).toContain('打分')
    expect(text).toContain('确认')
  })

  it('should have status text indicating idle', async () => {
    const ProcessControl = (await import('@/components/business/ProcessControl.vue')).default
    const wrapper = mount(ProcessControl, {
      global: {
        stubs: {
          'a-button': { template: '<button><slot /></button>' },
          'a-input-number': { template: '<input class="mock-input-number" />' },
        },
      },
    })
    await new Promise((r) => setTimeout(r, 50))
    expect(wrapper.text()).toContain('未执行')
  })

  it('should have batch input field', async () => {
    const ProcessControl = (await import('@/components/business/ProcessControl.vue')).default
    const wrapper = mount(ProcessControl, {
      global: {
        stubs: {
          'a-button': { template: '<button><slot /></button>' },
          'a-input-number': { template: '<input class="mock-input-number" />' },
        },
      },
    })
    await new Promise((r) => setTimeout(r, 50))
    expect(wrapper.find('.mock-input-number').exists()).toBe(true)
  })
})
