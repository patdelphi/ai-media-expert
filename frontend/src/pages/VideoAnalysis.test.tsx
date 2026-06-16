import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import VideoAnalysis from './VideoAnalysis'

const { apiServiceMock } = vi.hoisted(() => ({
  apiServiceMock: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))

vi.mock('../services/api', () => ({
  default: apiServiceMock,
}))

describe('VideoAnalysis', () => {
  it('解析历史显示视频原始标题', async () => {
    apiServiceMock.get.mockImplementation(async (url: string) => {
      if (url === '/video-analysis/videos') {
        return {
          code: 200,
          message: 'ok',
          data: { items: [], total: 0, page: 1, pages: 1 },
        }
      }
      if (url === '/video-analysis/templates') {
        return { code: 200, message: 'ok', data: [] }
      }
      if (url === '/video-analysis/tag-groups') {
        return { code: 200, message: 'ok', data: [] }
      }
      if (url === '/video-analysis/ai-configs') {
        return { code: 200, message: 'ok', data: [] }
      }
      if (url === '/video-analysis/') {
        return {
          code: 200,
          message: 'ok',
          data: {
            items: [
              {
                id: 1,
                video_file_id: 123,
                template_id: null,
                ai_config_id: 1,
                status: 'completed',
                progress: 100,
                result_summary: 'summary',
                processing_time: null,
                model_name: 'gpt-4o-mini',
                api_provider: 'openai',
                prompt_tokens: 10,
                completion_tokens: 20,
                total_tokens: 30,
                created_at: '2026-06-16T00:00:00.000Z',
                completed_at: '2026-06-16T00:00:01.000Z',
              },
            ],
            total: 1,
            page: 1,
            pages: 1,
          },
        }
      }
      if (url === '/video-analysis/videos/123') {
        return { code: 200, message: 'ok', data: { title: '原始标题' } }
      }

      throw new Error(`unexpected url: ${url}`)
    })

    render(
      <MemoryRouter>
        <VideoAnalysis />
      </MemoryRouter>,
    )

    await screen.findByText('解析历史')

    await waitFor(() => {
      expect(screen.getByText('视频: 原始标题')).toBeInTheDocument()
    })
  })
})
