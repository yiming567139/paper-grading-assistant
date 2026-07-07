import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import { useCorrectionStore } from '@/stores/correction'

vi.mock('@/api/correction', () => ({
  getCorrectionLogs: vi.fn().mockResolvedValue({ success: true, data: [], total: 0 }),
}))

const paginationStub = {
  template: '<div class="mock-pagination">total={{ total }}</div>',
  props: ['total']
}

describe('CorrectionLog', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('should render component', async () => {
    const CorrectionLog = (await import('@/components/business/CorrectionLog.vue')).default
    const wrapper = mount(CorrectionLog, {
      global: {
        stubs: {
          'a-table': { template: '<div class="mock-table"><slot name="emptyText" /></div>' },
          'a-radio-group': { template: '<div class="mock-radio-group"><slot /></div>' },
          'a-radio-button': { template: '<span class="mock-radio-button"><slot /></span>' },
          'a-pagination': true,
          'a-modal': { template: '<div class="mock-modal" />' },
          'a-button': { template: '<button><slot /></button>' },
          'a-tag': { template: '<span><slot /></span>' },
        },
      },
    })
    await new Promise((r) => setTimeout(r, 50))
    expect(wrapper.exists()).toBe(true)
  })

  it('should render filter labels', async () => {
    const CorrectionLog = (await import('@/components/business/CorrectionLog.vue')).default
    const wrapper = mount(CorrectionLog, {
      global: {
        stubs: {
          'a-table': { template: '<div class="mock-table"><slot name="emptyText" /></div>' },
          'a-radio-group': { template: '<div class="mock-radio-group"><slot /></div>' },
          'a-radio-button': { template: '<span class="mock-radio-button"><slot /></span>' },
          'a-pagination': true,
          'a-modal': { template: '<div class="mock-modal" />' },
          'a-button': { template: '<button><slot /></button>' },
          'a-tag': { template: '<span><slot /></span>' },
        },
      },
    })
    await new Promise((r) => setTimeout(r, 50))
    expect(wrapper.text()).toContain('一致性')
  })

  it('should render tip section', async () => {
    const CorrectionLog = (await import('@/components/business/CorrectionLog.vue')).default
    const wrapper = mount(CorrectionLog, {
      global: {
        stubs: {
          'a-table': { template: '<div class="mock-table"><slot name="emptyText" /></div>' },
          'a-radio-group': { template: '<div class="mock-radio-group"><slot /></div>' },
          'a-radio-button': { template: '<span class="mock-radio-button"><slot /></span>' },
          'a-pagination': true,
          'a-modal': { template: '<div class="mock-modal" />' },
          'a-button': { template: '<button><slot /></button>' },
          'a-tag': { template: '<span><slot /></span>' },
        },
      },
    })
    await new Promise((r) => setTimeout(r, 50))
    expect(wrapper.text()).toContain('数据展示示例')
  })

  it('should use backend total for pagination when no keyword filter', async () => {
    const { getCorrectionLogs } = await import('@/api/correction')
    vi.mocked(getCorrectionLogs).mockResolvedValueOnce({
      success: true,
      data: [
        { id: 1, screenshot: 'a.png', status: '成功', score: 5 },
        { id: 2, screenshot: 'b.png', status: '成功', score: 4 },
      ],
      total: 100,
    })

    const CorrectionLog = (await import('@/components/business/CorrectionLog.vue')).default
    const wrapper = mount(CorrectionLog, {
      global: {
        stubs: {
          'a-table': { template: '<div class="mock-table" />' },
          'a-radio-group': { template: '<div class="mock-radio-group"><slot /></div>' },
          'a-radio-button': { template: '<span class="mock-radio-button"><slot /></span>' },
          'a-pagination': paginationStub,
          'a-modal': { template: '<div class="mock-modal" />' },
          'a-button': { template: '<button><slot /></button>' },
          'a-tag': { template: '<span><slot /></span>' },
        },
      },
    })
    await new Promise((r) => setTimeout(r, 50))
    expect(wrapper.find('.mock-pagination').text()).toBe('total=100')
  })

  it('should refetch logs when workflow stops', async () => {
    const { getCorrectionLogs } = await import('@/api/correction')
    vi.mocked(getCorrectionLogs).mockResolvedValue({
      success: true,
      data: [],
      total: 0,
    })

    const CorrectionLog = (await import('@/components/business/CorrectionLog.vue')).default
    mount(CorrectionLog, {
      global: {
        stubs: {
          'a-table': { template: '<div class="mock-table" />' },
          'a-radio-group': { template: '<div class="mock-radio-group"><slot /></div>' },
          'a-radio-button': { template: '<span class="mock-radio-button"><slot /></span>' },
          'a-pagination': paginationStub,
          'a-modal': { template: '<div class="mock-modal" />' },
          'a-button': { template: '<button><slot /></button>' },
          'a-tag': { template: '<span><slot /></span>' },
        },
      },
    })
    await flushPromises()

    const store = useCorrectionStore()
    vi.mocked(getCorrectionLogs).mockClear()

    store.setRunning(true)
    await flushPromises()
    store.setRunning(false)
    await flushPromises()

    expect(getCorrectionLogs).toHaveBeenCalled()
  })
})
