import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import VideoTagsSummary from './VideoTagsSummary'

const { apiServiceMock } = vi.hoisted(() => ({
  apiServiceMock: {
    get: vi.fn(),
  },
}))

vi.mock('../../services/api', () => ({
  default: apiServiceMock,
}))

describe('VideoTagsSummary', () => {
  beforeEach(() => {
    apiServiceMock.get.mockReset()
  })

  afterEach(() => {
    cleanup()
    vi.clearAllMocks()
  })

  it('展示 token 汇总与当前标签', async () => {
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
              tag_name_snapshot: '品牌曝光',
              tag_name: '品牌曝光',
              source: 'ai_auto',
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
      if (url === '/video-analysis/videos/1/token-summary') {
        return {
          code: 200,
          message: 'ok',
          data: {
            video_file_id: 1,
            analysis: { prompt_tokens: 100, completion_tokens: 200, total_tokens: 300 },
            auto_tag: { prompt_tokens: 7, completion_tokens: 8, total_tokens: 15 },
            analysis_derived_tagging: { prompt_tokens: 5, completion_tokens: 6, total_tokens: 11 },
            total: { prompt_tokens: 112, completion_tokens: 214, total_tokens: 326 },
          },
        }
      }
      throw new Error(`unexpected url: ${url}`)
    })

    render(<VideoTagsSummary videoFileId={1} />)

    await screen.findByText('Token 汇总')
    expect(screen.getByText('总计')).toBeInTheDocument()
    expect(screen.getByText('326 (112+214)')).toBeInTheDocument()

    await screen.findByText('当前标签')
    expect(screen.getByText('品牌曝光')).toBeInTheDocument()
  })
})

