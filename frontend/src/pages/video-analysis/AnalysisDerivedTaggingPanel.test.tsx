import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import AnalysisDerivedTaggingPanel from './AnalysisDerivedTaggingPanel'

const { apiServiceMock } = vi.hoisted(() => ({
  apiServiceMock: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))

vi.mock('../../services/api', () => ({
  default: apiServiceMock,
}))

describe('AnalysisDerivedTaggingPanel', () => {
  beforeEach(() => {
    apiServiceMock.get.mockReset()
    apiServiceMock.post.mockReset()
  })

  afterEach(() => {
    cleanup()
    vi.clearAllMocks()
  })

  it('生成候选标签后可勾选采纳，并写入source=ai_assisted', async () => {
    apiServiceMock.get.mockResolvedValue({
      code: 200,
      message: 'ok',
      data: [
        {
          id: 1,
          video_file_id: 1,
          tag_id: 10,
          tag_name: '品牌曝光',
          tag_name_snapshot: '品牌曝光',
          source: 'ai_auto',
          confidence: 0.93,
          auto_tag_task_id: 99,
          revision_id: null,
          is_effective: true,
          created_by: 'ai',
          created_at: '2026-06-16T00:00:00.000Z',
          updated_at: '2026-06-16T00:00:00.000Z',
        },
        {
          id: 2,
          video_file_id: 1,
          tag_id: 11,
          tag_name: '教程',
          tag_name_snapshot: '教程',
          source: 'ai_auto',
          confidence: 0.8,
          auto_tag_task_id: 99,
          revision_id: null,
          is_effective: false,
          created_by: 'ai',
          created_at: '2026-06-16T00:00:00.000Z',
          updated_at: '2026-06-16T00:00:00.000Z',
        },
      ],
    })

    apiServiceMock.post.mockImplementation(async (url: string, payload?: any) => {
      if (url.startsWith('/video-analysis/99/tag-candidates') && url.includes('force=true')) {
        return {
          code: 200,
          message: 'ok',
          data: {
            analysis_id: 99,
            video_file_id: 1,
            tag_candidates: [
              { tag_name: '品牌曝光', confidence: 0.91, reason: '理由1' },
              { tag_name: '教程', confidence: 0.66, reason: '理由2' },
              { tag_name: '新标签', confidence: 0.7, reason: '理由3' },
            ],
          },
        }
      }
      if (url === '/uploaded-files/1/tags/revisions') {
        expect(payload.change_reason).toBe('采纳解析候选标签')
        expect(payload.operations).toEqual([
          {
            action: 'add',
            tag_name: '教程',
            confidence: 0.66,
            note: 'analysis_id=99',
            source: 'ai_assisted',
          },
          {
            action: 'add',
            tag_name: '新标签',
            confidence: 0.7,
            note: 'analysis_id=99',
            source: 'ai_assisted',
          },
        ])
        return { code: 200, message: 'ok', data: {} }
      }

      throw new Error(`unexpected post url: ${url}`)
    })

    const showNotification = vi.fn()
    render(<AnalysisDerivedTaggingPanel analysisId={99} videoFileId={1} showNotification={showNotification} />)

    fireEvent.click(await screen.findByRole('button', { name: '生成候选标签' }))

    await screen.findByText('新标签')
    const brandCheckbox = screen.getByLabelText('选择候选标签 品牌曝光') as HTMLInputElement
    const tutorialCheckbox = screen.getByLabelText('选择候选标签 教程') as HTMLInputElement
    const newCheckbox = screen.getByLabelText('选择候选标签 新标签') as HTMLInputElement

    expect(brandCheckbox.disabled).toBe(true)
    expect(tutorialCheckbox.disabled).toBe(false)
    expect(newCheckbox.disabled).toBe(false)

    await waitFor(() => {
      expect(tutorialCheckbox.checked).toBe(true)
      expect(newCheckbox.checked).toBe(true)
    })

    fireEvent.click(screen.getByRole('button', { name: '采纳所选为标签(2)' }))

    await waitFor(() => {
      expect(apiServiceMock.post).toHaveBeenCalledWith(
        '/uploaded-files/1/tags/revisions',
        expect.anything(),
      )
    })
  })

  it('允许在面板中手动切换AI配置与标签组，并将其带到生成候选接口参数中', async () => {
    apiServiceMock.get.mockResolvedValue({ code: 200, message: 'ok', data: [] })

    apiServiceMock.post.mockImplementation(async (url: string) => {
      if (
        url.startsWith('/video-analysis/99/tag-candidates') &&
        url.includes('force=true') &&
        url.includes('ai_config_id=2') &&
        url.includes('tag_group_ids=10')
      ) {
        return {
          code: 200,
          message: 'ok',
          data: { analysis_id: 99, video_file_id: 1, tag_candidates: [{ tag_name: '新标签', confidence: 0.7 }] },
        }
      }
      throw new Error(`unexpected post url: ${url}`)
    })

    const showNotification = vi.fn()
    render(
      <AnalysisDerivedTaggingPanel
        analysisId={99}
        videoFileId={1}
        aiConfigs={[
          { id: 1, name: 'A', provider: 'openai', model: 'm1', is_active: true, created_at: '', updated_at: '' },
          { id: 2, name: 'B', provider: 'openai', model: 'm2', is_active: true, created_at: '', updated_at: '' },
        ]}
        tagGroups={[
          { id: 10, name: '组1', is_active: true, tags: [], created_at: '', updated_at: '' },
        ]}
        showNotification={showNotification}
      />,
    )

    fireEvent.change(await screen.findByRole('combobox'), { target: { value: '2' } })
    fireEvent.click(screen.getByLabelText('选择标签组 组1'))

    fireEvent.click(await screen.findByRole('button', { name: '生成候选标签' }))
    await screen.findByText('新标签')
  })

  it('生成候选失败时显示后端返回的具体错误原因', async () => {
    apiServiceMock.get.mockResolvedValue({ code: 200, message: 'ok', data: [] })
    apiServiceMock.post.mockRejectedValue({
      response: {
        status: 400,
        data: {
          detail: '解析结果打标 API 调用失败: 401 - invalid api key',
        },
      },
    })

    const showNotification = vi.fn()
    render(<AnalysisDerivedTaggingPanel analysisId={109} videoFileId={25} showNotification={showNotification} />)

    fireEvent.click(await screen.findByRole('button', { name: '生成候选标签' }))

    await screen.findByText('解析结果打标 API 调用失败: 401 - invalid api key')
    expect(showNotification).toHaveBeenCalledWith('error', '解析结果打标 API 调用失败: 401 - invalid api key')
  })
})
