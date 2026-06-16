import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import VideoAnalysis from './VideoAnalysis'

const { apiServiceMock } = vi.hoisted(() => ({
  apiServiceMock: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}))

vi.mock('../services/api', () => ({
  default: apiServiceMock,
}))

describe('VideoAnalysis', () => {
  beforeEach(() => {
    apiServiceMock.get.mockReset()
    apiServiceMock.post.mockReset()
    apiServiceMock.delete.mockReset()
    localStorage.clear()
  })

  afterEach(() => {
    cleanup()
    vi.unstubAllGlobals()
    vi.clearAllMocks()
  })

  it('视频列表请求固定每页9条', async () => {
    apiServiceMock.get.mockImplementation(async (url: string) => {
      if (url === '/video-analysis/videos') {
        return {
          code: 200,
          message: 'ok',
          data: {
            items: Array.from({ length: 9 }, (_, index) => ({
              id: index + 1,
              original_filename: `video-${index + 1}.mp4`,
              saved_filename: `saved-video-${index + 1}.mp4`,
              title: `视频${index + 1}`,
              file_size: 1024,
              duration: 10,
              width: 1080,
              height: 1920,
              format_name: 'mp4',
              created_at: '2026-06-16T00:00:00.000Z',
            })),
            total: 12,
            page: 1,
            pages: 2,
          },
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
        return { code: 200, message: 'ok', data: { items: [], total: 0, page: 1, pages: 1 } }
      }

      throw new Error(`unexpected url: ${url}`)
    })

    render(
      <MemoryRouter>
        <VideoAnalysis />
      </MemoryRouter>,
    )

    await screen.findByText('选择要解析的视频')

    expect(apiServiceMock.get).toHaveBeenCalledWith('/video-analysis/videos', { page: 1, size: 9 })
    expect(screen.getByText('共 12 条，第 1/2 页')).toBeInTheDocument()
    expect(screen.getAllByText(/文件: saved-video-/)).toHaveLength(9)
  })

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

  it('解析历史支持逻辑删除', async () => {
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
                id: 9,
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
    apiServiceMock.delete.mockResolvedValue({ code: 200, message: 'ok', data: null })
    vi.stubGlobal('confirm', vi.fn(() => true))

    render(
      <MemoryRouter>
        <VideoAnalysis />
      </MemoryRouter>,
    )

    await screen.findByText('解析历史')
    const deleteButtons = await screen.findAllByRole('button', { name: /删除/ })
    fireEvent.click(deleteButtons[0])

    await waitFor(() => {
      expect(apiServiceMock.delete).toHaveBeenCalledWith('/video-analysis/9')
    })
  })
})
