import React from 'react'
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import SystemConfigPage from './SystemConfig'

const serviceMocks = vi.hoisted(() => ({
  systemConfigServiceMock: {
    getConfigs: vi.fn(),
    getCategories: vi.fn(),
  },
  aiConfigServiceMock: {
    getFullConfigs: vi.fn(),
    getSupportedProviders: vi.fn(() => [{ value: 'custom', label: '自定义', models: [] }]),
    createConfig: vi.fn(),
    updateConfig: vi.fn(),
  },
  promptTemplateServiceMock: {
    getTemplates: vi.fn(),
  },
  userManagementServiceMock: {
    getUsersList: vi.fn(),
  },
  tagGroupServiceMock: {
    getTagGroups: vi.fn(),
  },
}))

vi.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({ user: { role: 'admin' } }),
}))

vi.mock('../services/systemConfig', () => ({
  systemConfigService: serviceMocks.systemConfigServiceMock,
}))

vi.mock('../services/aiConfig', () => ({
  aiConfigService: serviceMocks.aiConfigServiceMock,
}))

vi.mock('../services/promptTemplate', () => ({
  promptTemplateService: serviceMocks.promptTemplateServiceMock,
}))

vi.mock('../services/userManagement', () => ({
  __esModule: true,
  default: serviceMocks.userManagementServiceMock,
}))

vi.mock('../services/tagGroup', () => ({
  __esModule: true,
  default: serviceMocks.tagGroupServiceMock,
}))

vi.mock('../utils/markdown', () => ({
  renderSafeMarkdown: (content: string) => content,
}))

vi.mock('react-hot-toast', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}))

describe('SystemConfigPage', () => {
  afterEach(() => {
    cleanup()
    vi.clearAllMocks()
  })

  it('AI API配置页签显示真实 AI 配置数量', async () => {
    serviceMocks.systemConfigServiceMock.getConfigs.mockResolvedValue({
      code: 200,
      message: 'ok',
      data: [],
    })
    serviceMocks.systemConfigServiceMock.getCategories.mockResolvedValue({
      code: 200,
      message: 'ok',
      data: [
        { category: 'ai', count: 2 },
        { category: 'system', count: 5 },
      ],
    })
    serviceMocks.aiConfigServiceMock.getFullConfigs.mockResolvedValue({
      code: 200,
      message: 'ok',
      data: [
        { id: 1, name: 'A', provider: 'custom', api_key: '***', model: 'm1', is_active: true, created_at: '', updated_at: '' },
        { id: 2, name: 'B', provider: 'custom', api_key: '***', model: 'm2', is_active: true, created_at: '', updated_at: '' },
        { id: 3, name: 'C', provider: 'custom', api_key: '***', model: 'm3', is_active: true, created_at: '', updated_at: '' },
      ],
    })
    serviceMocks.promptTemplateServiceMock.getTemplates.mockResolvedValue({
      code: 200,
      message: 'ok',
      data: [],
    })
    serviceMocks.userManagementServiceMock.getUsersList.mockResolvedValue({
      code: 200,
      message: 'ok',
      data: { items: [], total: 0, page: 1, size: 10, pages: 1 },
    })
    serviceMocks.tagGroupServiceMock.getTagGroups.mockResolvedValue({
      code: 200,
      message: 'ok',
      data: [],
    })

    render(<SystemConfigPage />)

    const aiTab = await screen.findByRole('button', { name: /AI API配置/ })

    await waitFor(() => {
      expect(within(aiTab).getByText('3')).toBeInTheDocument()
    })
  })

  it('AI 配置表单支持上传专用 API Key', async () => {
    serviceMocks.systemConfigServiceMock.getConfigs.mockResolvedValue({
      code: 200,
      message: 'ok',
      data: [],
    })
    serviceMocks.systemConfigServiceMock.getCategories.mockResolvedValue({
      code: 200,
      message: 'ok',
      data: [],
    })
    serviceMocks.aiConfigServiceMock.getFullConfigs.mockResolvedValue({
      code: 200,
      message: 'ok',
      data: [],
    })
    serviceMocks.aiConfigServiceMock.createConfig.mockResolvedValue({
      code: 200,
      message: 'ok',
      data: {
        id: 1,
        name: 'Qwen Upload',
        provider: 'custom',
        api_key: '***',
        upload_api_key: '***',
        api_base: 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions',
        model: 'qwen3.7-plus',
        max_tokens: 4000,
        temperature: 0.7,
        is_active: true,
        created_at: '',
        updated_at: '',
      },
    })
    serviceMocks.promptTemplateServiceMock.getTemplates.mockResolvedValue({
      code: 200,
      message: 'ok',
      data: [],
    })
    serviceMocks.userManagementServiceMock.getUsersList.mockResolvedValue({
      code: 200,
      message: 'ok',
      data: { items: [], total: 0, page: 1, size: 10, pages: 1 },
    })
    serviceMocks.tagGroupServiceMock.getTagGroups.mockResolvedValue({
      code: 200,
      message: 'ok',
      data: [],
    })

    render(<SystemConfigPage />)

    fireEvent.click(await screen.findByRole('button', { name: /AI API配置/ }))
    const uploadKeyInput = await screen.findByPlaceholderText('上传专用 API Key（仅Qwen文件上传）')
    expect(uploadKeyInput).toBeInTheDocument()

    fireEvent.change(screen.getByPlaceholderText('API名称 *'), { target: { value: 'Qwen Upload' } })
    fireEvent.change(screen.getByPlaceholderText('Provider *'), { target: { value: 'custom' } })
    fireEvent.change(screen.getByPlaceholderText('API Key *'), { target: { value: 'parse-key-1234567890' } })
    fireEvent.change(uploadKeyInput, { target: { value: 'upload-key-1234567890' } })
    fireEvent.change(screen.getByPlaceholderText('模型名称 *'), { target: { value: 'qwen3.7-plus' } })
    fireEvent.change(screen.getByPlaceholderText('Base URL *'), {
      target: { value: 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions' },
    })

    fireEvent.click(screen.getByRole('button', { name: /创建新配置/ }))

    await waitFor(() => {
      expect(serviceMocks.aiConfigServiceMock.createConfig).toHaveBeenCalledWith(
        expect.objectContaining({
          upload_api_key: 'upload-key-1234567890',
        }),
      )
    })
  })
})
