import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import VideoTaggingPanel from './VideoTaggingPanel'

const { apiServiceMock } = vi.hoisted(() => ({
  apiServiceMock: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))

vi.mock('../../services/api', () => ({
  default: apiServiceMock,
}))

describe('VideoTaggingPanel', () => {
  beforeEach(() => {
    apiServiceMock.get.mockReset()
    apiServiceMock.post.mockReset()
  })

  afterEach(() => {
    cleanup()
    vi.clearAllMocks()
  })

  it('同一标签展示唯一结果，来源仅用颜色区分并提供图例说明', async () => {
    apiServiceMock.get.mockImplementation(async (url: string) => {
      if (url === '/uploaded-files/1/tags') {
        return {
          code: 200,
          message: 'ok',
          data: [
            {
              id: 1,
              video_file_id: 1,
              tag_id: null,
              tag_name: '品牌曝光',
              tag_name_snapshot: '品牌曝光',
              source: 'ai_auto',
              sources: ['ai_auto', 'ai_assisted'],
              confidence: 0.9,
              auto_tag_task_id: null,
              revision_id: null,
              is_effective: true,
              created_by: 'ai',
              created_at: '2026-06-16T00:00:00.000Z',
              updated_at: '2026-06-16T00:00:00.000Z',
            },
          ],
        }
      }
      if (url === '/uploaded-files/1/tags/revisions') {
        return { code: 200, message: 'ok', data: [] }
      }
      if (url === '/video-auto-tags/video-files/1/tasks') {
        return { code: 200, message: 'ok', data: [] }
      }
      throw new Error(`unexpected url: ${url}`)
    })

    const showNotification = vi.fn()
    render(
      <VideoTaggingPanel
        video={{
          id: 1,
          original_filename: 'v.mp4',
          saved_filename: 'v.mp4',
          file_size: 1,
          created_at: '2026-06-16T00:00:00.000Z',
        }}
        aiConfigs={[
          {
            id: 1,
            name: 'cfg',
            provider: 'openai',
            model: 'm',
            is_active: true,
            created_at: '',
            updated_at: '',
          },
        ]}
        tagGroups={[]}
        selectedAIConfig={null}
        setSelectedAIConfig={vi.fn()}
        selectedTagGroups={[]}
        setSelectedTagGroups={vi.fn()}
        transmissionMethod="url"
        setTransmissionMethod={vi.fn()}
        showNotification={showNotification}
        onBack={vi.fn()}
      />,
    )

    await screen.findByText('品牌曝光')
    expect(await screen.findByText('颜色说明：蓝色=AI（自动打标/解析派生），绿色=人工修订，灰色=已排除')).toBeInTheDocument()
    expect(screen.queryByText('AI自动·解析派生')).toBeNull()
  })
})
