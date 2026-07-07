import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import axios from 'axios'

vi.mock('axios')
vi.mock('ant-design-vue', async () => {
  const actual = await vi.importActual('ant-design-vue')
  return {
    ...(actual as Record<string, unknown>),
    message: {
      info: vi.fn(),
      success: vi.fn(),
      error: vi.fn(),
      warning: vi.fn(),
    },
  }
})

describe('SettingsView workflow mock result', () => {
  const mockConfig = {
    llm: { provider: 'dashscope', model: 'mA', api_key: 'k', base_url: 'https://example.com', timeout: 60, max_retries: 2, prompt_template: '' },
    llm_secondary: { enabled: true, provider: 'deepseek', model: 'mB', api_key: 'k2', base_url: 'https://example2.com', timeout: 60, max_retries: 2, prompt_template: '' },
    mysql: { host: '', port: 3306, database: '', user: '', password: '', charset: 'utf8mb4' },
    paths: { logs: '', screenshots: '' },
    region: { capture: { x1: 0, y1: 0, x2: 0, y2: 0 }, capture_human: { x1: 0, y1: 0, x2: 0, y2: 0 }, score_buttons: [], clear_score: { enabled: true, x: 0, y: 0 }, confirm_button: { x: 0, y: 0 } },
    http_server: { host: '0.0.0.0', port: 8081 },
    window: { auto_open_browser: true },
  }

  const mockWorkflow = {
    workflow: {
      steps: [
        { id: 'evaluate', type: 'VLMEvalStep', enabled: true, delay: 0.5, params: { timeout: 30 } },
      ],
    },
  }

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(axios.get).mockImplementation((url: string) => {
      if (url === '/api/v1/config') return Promise.resolve({ data: mockConfig } as any)
      if (url === '/api/v1/workflow/config') return Promise.resolve({ data: mockWorkflow } as any)
      return Promise.reject(new Error('unknown'))
    })
    vi.mocked(axios.post).mockResolvedValue({ data: { status: 'saved' } } as any)
  })

  it('initializes mock_result and submits it on save', async () => {
    const SettingsView = (await import('@/views/SettingsView.vue')).default
    const wrapper = mount(SettingsView, {
      global: {
        stubs: {
          'a-tabs': { template: '<div><slot /></div>' },
          'a-tab-pane': { template: '<div><slot /></div>' },
          'a-list': { props: ['dataSource'], template: '<div><slot v-if="dataSource && dataSource.length" name="renderItem" v-bind="{ item: dataSource[0], index: 0 }" /></div>' },
          'a-list-item': { template: '<div><slot /></div>' },
          'a-switch': { template: '<input type="checkbox" :checked="checked" @change="$emit(\'update:checked\', $event.target.checked)" />', props: ['checked'] },
          'a-input-number': { template: '<input class="mock-input-number" :value="value" @input="$emit(\'update:value\', Number($event.target.value))" />', props: ['value'] },
          'a-textarea': { template: '<textarea class="mock-textarea" :value="value" @input="$emit(\'update:value\', $event.target.value)" />', props: ['value'] },
          'a-button': { template: '<button @click="$emit(\'click\')"><slot /></button>' },
          'a-card': { template: '<div><slot /></div>' },
          'a-form': { template: '<form><slot /></form>' },
          'a-form-item': { template: '<div><slot /></div>' },
        },
      },
    })
    await flushPromises()

    const buttons = wrapper.findAll('button')
    const saveBtn = buttons.find((b) => b.text() === '保存')!
    await saveBtn.trigger('click')
    await flushPromises()

    const workflowPost = vi.mocked(axios.post).mock.calls.find((call) => call[0] === '/api/v1/workflow/config')
    expect(workflowPost).toBeTruthy()
    const payload = workflowPost![1] as any
    const step = payload.workflow.steps[0]
    expect(step.params.mock_result).toEqual({
      enabled: false,
      primary: { score: 0, explanation: '' },
      secondary: { score: 0, explanation: '' },
    })
  })
})
