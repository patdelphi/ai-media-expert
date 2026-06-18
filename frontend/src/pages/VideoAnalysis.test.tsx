import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import VideoAnalysis from './VideoAnalysis'
import VideoAnalysisHistoryDetail from './video-analysis/VideoAnalysisHistoryDetail'

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
    vi.stubGlobal('confirm', vi.fn(() => true))
  })

  afterEach(() => {
    cleanup()
    vi.useRealTimers()
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
      <MemoryRouter initialEntries={['/video/analysis']}>
        <Routes>
          <Route path="/video/analysis" element={<VideoAnalysis />} />
          <Route path="/video/analysis/history/:analysisId" element={<VideoAnalysisHistoryDetail />} />
        </Routes>
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
      <MemoryRouter initialEntries={['/video/analysis']}>
        <Routes>
          <Route path="/video/analysis" element={<VideoAnalysis />} />
          <Route path="/video/analysis/history/:analysisId" element={<VideoAnalysisHistoryDetail />} />
        </Routes>
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
      <MemoryRouter initialEntries={['/video/analysis']}>
        <Routes>
          <Route path="/video/analysis" element={<VideoAnalysis />} />
          <Route path="/video/analysis/history/:analysisId" element={<VideoAnalysisHistoryDetail />} />
        </Routes>
      </MemoryRouter>,
    )

    await screen.findByText('解析历史')
    const deleteButtons = await screen.findAllByRole('button', { name: /删除/ })
    fireEvent.click(deleteButtons[0])

    await waitFor(() => {
      expect(apiServiceMock.delete).toHaveBeenCalledWith('/video-analysis/9')
    })
  })

  it('步骤2展示自动打标结果与修订历史', async () => {
    apiServiceMock.get.mockImplementation(async (url: string) => {
      if (url === '/video-analysis/videos') {
        return {
          code: 200,
          message: 'ok',
          data: {
            items: [
              {
                id: 1,
                original_filename: 'video-1.mp4',
                saved_filename: 'saved-video-1.mp4',
                title: '视频1',
                file_size: 1024,
                duration: 10,
                width: 1080,
                height: 1920,
                format_name: 'mp4',
                created_at: '2026-06-16T00:00:00.000Z',
              },
            ],
            total: 1,
            page: 1,
            pages: 1,
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
        return {
          code: 200,
          message: 'ok',
          data: [
            {
              id: 7,
              name: 'Qwen AutoTag',
              provider: 'custom',
              model: 'qwen3.7-plus',
              max_tokens: 1200,
              temperature: 0.2,
              is_active: true,
              created_at: '2026-06-16T00:00:00.000Z',
              updated_at: '2026-06-16T00:00:00.000Z',
            },
          ],
        }
      }
      if (url === '/video-analysis/') {
        return { code: 200, message: 'ok', data: { items: [], total: 0, page: 1, pages: 1 } }
      }
      if (url === '/uploaded-files/1/tags') {
        return {
          code: 200,
          message: 'ok',
          data: [
            {
              id: 1,
              video_file_id: 1,
              tag_id: 10,
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
              tag_name_snapshot: '教程',
              source: 'manual_override',
              confidence: 1,
              auto_tag_task_id: null,
              revision_id: 5,
              is_effective: false,
              created_by: '1',
              created_at: '2026-06-16T00:00:00.000Z',
              updated_at: '2026-06-16T00:00:00.000Z',
            },
          ],
        }
      }
      if (url === '/video-auto-tags/video-files/1/tasks') {
        return {
          code: 200,
          message: 'ok',
          data: [
            {
              id: 99,
              video_file_id: 1,
              ai_config_id: 7,
              status: 'completed',
              progress: 100,
              transmission_method: 'url',
              structured_summary: { overview: '品牌信息突出' },
              created_at: '2026-06-16T00:00:00.000Z',
              updated_at: '2026-06-16T00:00:00.000Z',
              items: [
                {
                  id: 2,
                  tag_name: '品牌曝光',
                  tag_source: 'library',
                  match_type: 'ai_detected',
                  confidence: 0.93,
                  is_promoted: true,
                },
              ],
            },
          ],
        }
      }
      if (url === '/video-auto-tags/99') {
        return {
          code: 200,
          message: 'ok',
          data: {
            id: 99,
            video_file_id: 1,
            ai_config_id: 7,
            prompt_content: 'prompt',
            transmission_method: 'url',
            status: 'completed',
            progress: 100,
            structured_summary: { overview: '品牌信息突出' },
            result_metadata: {},
            token_usage: {},
            created_at: '2026-06-16T00:00:00.000Z',
            updated_at: '2026-06-16T00:00:00.000Z',
            items: [
              {
                id: 2,
                tag_name: '品牌曝光',
                tag_source: 'library',
                match_type: 'ai_detected',
                confidence: 0.93,
                is_promoted: true,
              },
            ],
          },
        }
      }
      if (url === '/uploaded-files/1/tags/revisions') {
        return {
          code: 200,
          message: 'ok',
          data: [
            {
              id: 5,
              video_file_id: 1,
              revision_number: 1,
              change_reason: '人工确认',
              created_by: '1',
              created_at: '2026-06-16T00:00:00.000Z',
              updated_at: '2026-06-16T00:00:00.000Z',
              items: [
                {
                  id: 8,
                  tag_id: 10,
                  tag_name: '品牌曝光',
                  action: 'add',
                  note: '人工确认',
                  created_at: '2026-06-16T00:00:00.000Z',
                },
              ],
            },
          ],
        }
      }

      throw new Error(`unexpected url: ${url}`)
    })

    render(
      <MemoryRouter initialEntries={['/video/analysis']}>
        <Routes>
          <Route path="/video/analysis" element={<VideoAnalysis />} />
          <Route path="/video/analysis/history/:analysisId" element={<VideoAnalysisHistoryDetail />} />
        </Routes>
      </MemoryRouter>,
    )

    await screen.findByText('选择要解析的视频')
    fireEvent.click(await screen.findByText('视频1'))
    fireEvent.click(screen.getByRole('button', { name: '上传视频打标' }))

    await screen.findByText('自动打标')
    const aiTag = screen.getByText('品牌曝光')
    const manualTag = screen.getByText('教程')
    expect(aiTag).toBeInTheDocument()
    expect(manualTag).toBeInTheDocument()
    const aiChipButton = screen.getByRole('button', { name: '排除标签 品牌曝光' })
    const manualChipButton = screen.getByRole('button', { name: '恢复标签 教程' })
    expect(aiChipButton.closest('span')?.className).toContain('bg-blue-50')
    expect(manualChipButton.closest('span')?.className).toContain('bg-green-50')
    expect(screen.getByText('已排除')).toBeInTheDocument()
    expect(screen.queryByText('当前生效')).not.toBeInTheDocument()
    expect(screen.getByText('自动打标历史')).toBeInTheDocument()
    expect(screen.getByText('任务 #99')).toBeInTheDocument()
    expect(screen.getByText('版本 #1')).toBeInTheDocument()
  })

  it('历史标签排序：先 AI 后手动，最后已排除；组内按拼音', async () => {
    apiServiceMock.get.mockImplementation(async (url: string) => {
      if (url === '/video-analysis/videos') {
        return {
          code: 200,
          message: 'ok',
          data: {
            items: [
              {
                id: 1,
                original_filename: 'video-1.mp4',
                saved_filename: 'saved-video-1.mp4',
                title: '视频1',
                file_size: 1024,
                duration: 10,
                width: 1080,
                height: 1920,
                format_name: 'mp4',
                created_at: '2026-06-16T00:00:00.000Z',
              },
            ],
            total: 1,
            page: 1,
            pages: 1,
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
        return {
          code: 200,
          message: 'ok',
          data: [
            {
              id: 7,
              name: 'Qwen AutoTag',
              provider: 'custom',
              model: 'qwen3.7-plus',
              max_tokens: 1200,
              temperature: 0.2,
              is_active: true,
              created_at: '2026-06-16T00:00:00.000Z',
              updated_at: '2026-06-16T00:00:00.000Z',
            },
          ],
        }
      }
      if (url === '/video-analysis/') {
        return { code: 200, message: 'ok', data: { items: [], total: 0, page: 1, pages: 1 } }
      }
      if (url === '/uploaded-files/1/tags') {
        return {
          code: 200,
          message: 'ok',
          data: [
            {
              id: 1,
              video_file_id: 1,
              tag_id: 10,
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
              tag_id: 12,
              tag_name_snapshot: '阿尔法',
              source: 'ai_auto',
              confidence: 0.8,
              auto_tag_task_id: 99,
              revision_id: null,
              is_effective: true,
              created_by: 'ai',
              created_at: '2026-06-16T00:00:00.000Z',
              updated_at: '2026-06-16T00:00:00.000Z',
            },
            {
              id: 3,
              video_file_id: 1,
              tag_id: 11,
              tag_name_snapshot: '教程',
              source: 'manual_override',
              confidence: 1,
              auto_tag_task_id: null,
              revision_id: 5,
              is_effective: true,
              created_by: '1',
              created_at: '2026-06-16T00:00:00.000Z',
              updated_at: '2026-06-16T00:00:00.000Z',
            },
            {
              id: 4,
              video_file_id: 1,
              tag_id: 13,
              tag_name_snapshot: '测试',
              source: 'ai_auto',
              confidence: 0.5,
              auto_tag_task_id: 99,
              revision_id: null,
              is_effective: false,
              created_by: 'ai',
              created_at: '2026-06-16T00:00:00.000Z',
              updated_at: '2026-06-16T00:00:00.000Z',
            },
          ],
        }
      }
      if (url === '/video-auto-tags/video-files/1/tasks') {
        return { code: 200, message: 'ok', data: [] }
      }
      if (url === '/uploaded-files/1/tags/revisions') {
        return { code: 200, message: 'ok', data: [] }
      }

      throw new Error(`unexpected url: ${url}`)
    })

    render(
      <MemoryRouter initialEntries={['/video/analysis']}>
        <Routes>
          <Route path="/video/analysis" element={<VideoAnalysis />} />
          <Route path="/video/analysis/history/:analysisId" element={<VideoAnalysisHistoryDetail />} />
        </Routes>
      </MemoryRouter>,
    )

    await screen.findByText('选择要解析的视频')
    fireEvent.click(await screen.findByText('视频1'))
    fireEvent.click(screen.getByRole('button', { name: '上传视频打标' }))
    await screen.findByText('自动打标')

    const actionButtons = screen.getAllByRole('button', { name: /^(排除标签|恢复标签) / })
    const labels = actionButtons.map((btn) => btn.getAttribute('aria-label'))
    expect(labels).toEqual(['排除标签 阿尔法', '排除标签 品牌曝光', '排除标签 教程', '恢复标签 测试'])
  })

  it('支持启动自动打标并展示任务摘要', async () => {
    let taskDetailCalls = 0
    apiServiceMock.get.mockImplementation(async (url: string) => {
      if (url === '/video-analysis/videos') {
        return {
          code: 200,
          message: 'ok',
          data: {
            items: [
              {
                id: 1,
                original_filename: 'video-1.mp4',
                saved_filename: 'saved-video-1.mp4',
                title: '视频1',
                file_size: 1024,
                duration: 10,
                width: 1080,
                height: 1920,
                format_name: 'mp4',
                created_at: '2026-06-16T00:00:00.000Z',
              },
            ],
            total: 1,
            page: 1,
            pages: 1,
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
        return {
          code: 200,
          message: 'ok',
          data: [
            {
              id: 7,
              name: 'Qwen AutoTag',
              provider: 'custom',
              model: 'qwen3.7-plus',
              max_tokens: 1200,
              temperature: 0.2,
              is_active: true,
              created_at: '2026-06-16T00:00:00.000Z',
              updated_at: '2026-06-16T00:00:00.000Z',
            },
          ],
        }
      }
      if (url === '/video-analysis/') {
        return { code: 200, message: 'ok', data: { items: [], total: 0, page: 1, pages: 1 } }
      }
      if (url === '/uploaded-files/1/tags') {
        return {
          code: 200,
          message: 'ok',
          data: taskDetailCalls >= 2
            ? [
                {
                  id: 1,
                  video_file_id: 1,
                  tag_id: 10,
                  tag_name: '品牌曝光',
                  source: 'ai_auto',
                  confidence: 0.91,
                  auto_tag_task_id: 99,
                  revision_id: null,
                  is_effective: true,
                  created_by: 'ai',
                  created_at: '2026-06-16T00:00:00.000Z',
                  updated_at: '2026-06-16T00:00:00.000Z',
                },
              ]
            : [],
        }
      }
      if (url === '/video-auto-tags/video-files/1/tasks') {
        return {
          code: 200,
          message: 'ok',
          data: taskDetailCalls >= 2
            ? [
                {
                  id: 99,
                  video_file_id: 1,
                  ai_config_id: 7,
                  status: 'completed',
                  progress: 100,
                  transmission_method: 'url',
                  structured_summary: { overview: '品牌信息突出' },
                  created_at: '2026-06-16T00:00:00.000Z',
                  updated_at: '2026-06-16T00:00:00.000Z',
                  items: [
                    {
                      id: 2,
                      tag_name: '品牌曝光',
                      tag_source: 'library',
                      match_type: 'ai_detected',
                      confidence: 0.91,
                      is_promoted: true,
                    },
                  ],
                },
              ]
            : [],
        }
      }
      if (url === '/uploaded-files/1/tags/revisions') {
        return { code: 200, message: 'ok', data: [] }
      }
      if (url === '/video-auto-tags/99') {
        taskDetailCalls += 1
        return {
          code: 200,
          message: 'ok',
          data: {
            id: 99,
            video_file_id: 1,
            ai_config_id: 7,
            prompt_content: 'prompt',
            transmission_method: 'url',
            status: taskDetailCalls >= 2 ? 'completed' : 'processing',
            progress: taskDetailCalls >= 2 ? 100 : 30,
            structured_summary: { overview: '品牌信息突出' },
            result_metadata: {},
            token_usage: {},
            created_at: '2026-06-16T00:00:00.000Z',
            updated_at: '2026-06-16T00:00:00.000Z',
            items: [
              {
                id: 2,
                tag_name: '品牌曝光',
                tag_source: 'library',
                match_type: 'ai_detected',
                confidence: 0.91,
                is_promoted: true,
              },
            ],
          },
        }
      }

      throw new Error(`unexpected url: ${url}`)
    })
    apiServiceMock.post.mockImplementation(async (url: string) => {
      if (url === '/video-auto-tags/start') {
        return { code: 200, message: 'ok', data: { task_id: 99, status: 'pending', message: 'ok' } }
      }
      throw new Error(`unexpected post url: ${url}`)
    })

    render(
      <MemoryRouter>
        <VideoAnalysis />
      </MemoryRouter>,
    )

    await screen.findByText('选择要解析的视频')
    fireEvent.click(await screen.findByText('视频1'))
    fireEvent.click(screen.getByRole('button', { name: '上传视频打标' }))
    await screen.findByText('自动打标')
    vi.useFakeTimers()
    fireEvent.click(screen.getByText('Qwen AutoTag'))
    fireEvent.click(screen.getByRole('button', { name: '开始自动打标' }))

    await act(async () => {
      await vi.advanceTimersByTimeAsync(3000)
    })

    expect(apiServiceMock.post).toHaveBeenCalledWith('/video-auto-tags/start', expect.any(Object))
    expect(screen.getByText(/最近自动打标任务 #99/)).toBeInTheDocument()
    expect(screen.getAllByText(/品牌信息突出/).length).toBeGreaterThan(0)
    expect(screen.getByText('自动打标历史')).toBeInTheDocument()
    expect(screen.getAllByText('品牌曝光').length).toBeGreaterThan(0)
  })

  it('支持人工添加标签修订', async () => {
    const revisionState = {
      tags: [] as Array<Record<string, unknown>>,
      revisions: [] as Array<Record<string, unknown>>,
    }

    apiServiceMock.get.mockImplementation(async (url: string) => {
      if (url === '/video-analysis/videos') {
        return {
          code: 200,
          message: 'ok',
          data: {
            items: [
              {
                id: 1,
                original_filename: 'video-1.mp4',
                saved_filename: 'saved-video-1.mp4',
                title: '视频1',
                file_size: 1024,
                duration: 10,
                width: 1080,
                height: 1920,
                format_name: 'mp4',
                created_at: '2026-06-16T00:00:00.000Z',
              },
            ],
            total: 1,
            page: 1,
            pages: 1,
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
        return {
          code: 200,
          message: 'ok',
          data: [
            {
              id: 7,
              name: 'Qwen AutoTag',
              provider: 'custom',
              model: 'qwen3.7-plus',
              max_tokens: 1200,
              temperature: 0.2,
              is_active: true,
              created_at: '2026-06-16T00:00:00.000Z',
              updated_at: '2026-06-16T00:00:00.000Z',
            },
          ],
        }
      }
      if (url === '/video-analysis/') {
        return { code: 200, message: 'ok', data: { items: [], total: 0, page: 1, pages: 1 } }
      }
      if (url === '/uploaded-files/1/tags') {
        return { code: 200, message: 'ok', data: revisionState.tags }
      }
      if (url === '/uploaded-files/1/tags/revisions') {
        return { code: 200, message: 'ok', data: revisionState.revisions }
      }
      if (url === '/video-auto-tags/video-files/1/tasks') {
        return { code: 200, message: 'ok', data: [] }
      }

      throw new Error(`unexpected url: ${url}`)
    })
    apiServiceMock.post.mockImplementation(async (url: string, data?: any) => {
      if (url === '/uploaded-files/1/tags/revisions') {
        revisionState.tags = [
          {
            id: 11,
            video_file_id: 1,
            tag_id: 21,
            tag_name: data.operations[0].tag_name,
            source: 'manual_override',
            confidence: 1,
            auto_tag_task_id: null,
            revision_id: 1,
            is_effective: true,
            created_by: '1',
            created_at: '2026-06-16T00:00:00.000Z',
            updated_at: '2026-06-16T00:00:00.000Z',
          },
        ]
        revisionState.revisions = [
          {
            id: 1,
            video_file_id: 1,
            revision_number: 1,
            change_reason: data.change_reason,
            created_by: '1',
            created_at: '2026-06-16T00:00:00.000Z',
            updated_at: '2026-06-16T00:00:00.000Z',
            items: [
              {
                id: 3,
                tag_name: data.operations[0].tag_name,
                action: 'add',
                created_at: '2026-06-16T00:00:00.000Z',
              },
            ],
          },
        ]
        return { code: 200, message: 'ok', data: revisionState.revisions[0] }
      }
      throw new Error(`unexpected post url: ${url}`)
    })

    render(
      <MemoryRouter>
        <VideoAnalysis />
      </MemoryRouter>,
    )

    await screen.findByText('选择要解析的视频')
    fireEvent.click(screen.getByText('视频1'))
    fireEvent.click(screen.getByRole('button', { name: '上传视频打标' }))
    await screen.findByText('自动打标')

    fireEvent.change(screen.getByPlaceholderText('输入要添加的标签'), {
      target: { value: '教程' },
    })
    fireEvent.change(screen.getByPlaceholderText('修订原因（可选）'), {
      target: { value: '补充人工标签' },
    })
    fireEvent.click(screen.getByRole('button', { name: '添加标签' }))

    await waitFor(() => {
      expect(apiServiceMock.post).toHaveBeenCalledWith('/uploaded-files/1/tags/revisions', {
        change_reason: '补充人工标签',
        operations: [
          {
            action: 'add',
            tag_name: '教程',
            confidence: 1,
            note: '补充人工标签',
          },
        ],
      })
    })
    expect(await screen.findByText('教程')).toBeInTheDocument()
    expect(screen.getByText('版本 #1')).toBeInTheDocument()
  })

  it('移除标签前弹出确认框', async () => {
    apiServiceMock.get.mockImplementation(async (url: string) => {
      if (url === '/video-analysis/videos') {
        return {
          code: 200,
          message: 'ok',
          data: {
            items: [
              {
                id: 1,
                original_filename: 'video-1.mp4',
                saved_filename: 'saved-video-1.mp4',
                title: '视频1',
                file_size: 1024,
                duration: 10,
                width: 1080,
                height: 1920,
                format_name: 'mp4',
                created_at: '2026-06-16T00:00:00.000Z',
              },
            ],
            total: 1,
            page: 1,
            pages: 1,
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
        return {
          code: 200,
          message: 'ok',
          data: [
            {
              id: 7,
              name: 'Qwen AutoTag',
              provider: 'custom',
              model: 'qwen3.7-plus',
              max_tokens: 1200,
              temperature: 0.2,
              is_active: true,
              created_at: '2026-06-16T00:00:00.000Z',
              updated_at: '2026-06-16T00:00:00.000Z',
            },
          ],
        }
      }
      if (url === '/video-analysis/') {
        return { code: 200, message: 'ok', data: { items: [], total: 0, page: 1, pages: 1 } }
      }
      if (url === '/uploaded-files/1/tags') {
        return {
          code: 200,
          message: 'ok',
          data: [
            {
              id: 1,
              video_file_id: 1,
              tag_id: 10,
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

    render(
      <MemoryRouter>
        <VideoAnalysis />
      </MemoryRouter>,
    )

    await screen.findByText('选择要解析的视频')
    fireEvent.click(await screen.findByText('视频1'))
    fireEvent.click(screen.getByRole('button', { name: '上传视频打标' }))
    await screen.findByText('历史标签集合')

    fireEvent.click(screen.getByRole('button', { name: '排除标签 品牌曝光' }))

    expect(window.confirm).toHaveBeenCalled()
    expect(apiServiceMock.post).toHaveBeenCalledWith('/uploaded-files/1/tags/revisions', {
      change_reason: undefined,
      operations: [
        {
          action: 'remove',
          tag_name: '品牌曝光',
          note: '前端人工移除标签',
        },
      ],
    })
  })

  it('选择视频后展示双入口', async () => {
    apiServiceMock.get.mockImplementation(async (url: string) => {
      if (url === '/video-analysis/videos') {
        return {
          code: 200,
          message: 'ok',
          data: {
            items: [
              {
                id: 1,
                original_filename: 'video-1.mp4',
                saved_filename: 'saved-video-1.mp4',
                title: '视频1',
                file_size: 1024,
                duration: 10,
                width: 1080,
                height: 1920,
                format_name: 'mp4',
                created_at: '2026-06-16T00:00:00.000Z',
              },
            ],
            total: 1,
            page: 1,
            pages: 1,
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
    fireEvent.click(await screen.findByText('视频1'))

    expect(screen.getByRole('button', { name: '视频解析' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '上传视频打标' })).toBeInTheDocument()
  })

  it('解析历史列表点击“查看 / 打标”只打开详情，不自动生成候选', async () => {
    apiServiceMock.get.mockImplementation(async (url: string) => {
      if (url === '/video-analysis/videos') {
        return {
          code: 200,
          message: 'ok',
          data: {
            items: [
              {
                id: 1,
                original_filename: 'video-1.mp4',
                saved_filename: 'saved-video-1.mp4',
                title: '视频1',
                file_size: 1024,
                duration: 10,
                width: 1080,
                height: 1920,
                format_name: 'mp4',
                created_at: '2026-06-16T00:00:00.000Z',
              },
            ],
            total: 1,
            page: 1,
            pages: 1,
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
        return {
          code: 200,
          message: 'ok',
          data: {
            items: [
              {
                id: 10,
                video_file_id: 1,
                template_id: 1,
                ai_config_id: 7,
                status: 'completed',
                progress: 100,
                result_summary: 'summary',
                processing_time: 1,
                model_name: 'm1',
                api_provider: 'custom',
                total_tokens: 10,
                prompt_tokens: 4,
                completion_tokens: 6,
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
      if (url === '/video-analysis/videos/1') {
        return { code: 200, message: 'ok', data: { id: 1, title: '视频1', original_filename: 'video-1.mp4' } }
      }
      if (url === '/video-analysis/10') {
        return {
          code: 200,
          message: 'ok',
          data: {
            id: 10,
            video_file_id: 1,
            template_id: 1,
            ai_config_id: 7,
            prompt_content: 'prompt',
            status: 'completed',
            progress: 100,
            analysis_result: 'result',
            result_metadata: { tag_candidates: [{ tag_name: '新标签', confidence: 0.7, reason: 'r' }] },
            created_at: '2026-06-16T00:00:00.000Z',
            updated_at: '2026-06-16T00:00:00.000Z',
          },
        }
      }
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

      throw new Error(`unexpected url: ${url}`)
    })

    apiServiceMock.post.mockImplementation(async (url: string) => {
      throw new Error(`unexpected post url: ${url}`)
    })

    render(
      <MemoryRouter initialEntries={['/video/analysis']}>
        <Routes>
          <Route path="/video/analysis" element={<VideoAnalysis />} />
          <Route path="/video/analysis/history/:analysisId" element={<VideoAnalysisHistoryDetail />} />
        </Routes>
      </MemoryRouter>,
    )

    await screen.findByText('选择要解析的视频')

    fireEvent.click(await screen.findByRole('button', { name: '查看详情/根据解析结果打标' }))

    await screen.findByText(/解析结果详情 #10/)
    await screen.findByText('当前标签')
    await screen.findByText('品牌曝光')
  })

  it('解析历史列表显示模板名称，无模板时显示未使用模板', async () => {
    apiServiceMock.get.mockImplementation(async (url: string) => {
      if (url === '/video-analysis/videos') {
        return {
          code: 200,
          message: 'ok',
          data: {
            items: [
              {
                id: 1,
                original_filename: 'video-1.mp4',
                saved_filename: 'saved-video-1.mp4',
                title: '视频1',
                file_size: 1024,
                created_at: '2026-06-16T00:00:00.000Z',
              },
            ],
            total: 1,
            page: 1,
            pages: 1,
          },
        }
      }
      if (url === '/video-analysis/templates') {
        return {
          code: 200,
          message: 'ok',
          data: [
            {
              id: 1,
              title: '商品讲解模板',
              content: 'tmpl',
              is_active: true,
              usage_count: 1,
              created_at: '2026-06-16T00:00:00.000Z',
              updated_at: '2026-06-16T00:00:00.000Z',
            },
          ],
        }
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
                id: 10,
                video_file_id: 1,
                template_id: 1,
                ai_config_id: 7,
                status: 'completed',
                progress: 100,
                result_summary: 'summary-a',
                created_at: '2026-06-16T00:00:00.000Z',
                completed_at: '2026-06-16T00:00:01.000Z',
              },
              {
                id: 11,
                video_file_id: 1,
                template_id: null,
                ai_config_id: 7,
                status: 'completed',
                progress: 100,
                result_summary: 'summary-b',
                created_at: '2026-06-16T00:00:02.000Z',
                completed_at: '2026-06-16T00:00:03.000Z',
              },
            ],
            total: 2,
            page: 1,
            pages: 1,
          },
        }
      }
      if (url === '/video-analysis/videos/1') {
        return { code: 200, message: 'ok', data: { id: 1, title: '视频1', original_filename: 'video-1.mp4' } }
      }
      throw new Error(`unexpected url: ${url}`)
    })

    render(
      <MemoryRouter>
        <VideoAnalysis />
      </MemoryRouter>,
    )

    await screen.findByText('模板：商品讲解模板')
    await screen.findByText('模板：未使用模板')
  })

  it('解析历史列表兼容旧完成态，status 为 success 时点击“查看 / 打标”也只打开详情', async () => {
    apiServiceMock.get.mockImplementation(async (url: string) => {
      if (url === '/video-analysis/videos') {
        return {
          code: 200,
          message: 'ok',
          data: {
            items: [
              {
                id: 1,
                original_filename: 'video-1.mp4',
                saved_filename: 'saved-video-1.mp4',
                title: '视频1',
                file_size: 1024,
                duration: 10,
                width: 1080,
                height: 1920,
                format_name: 'mp4',
                created_at: '2026-06-16T00:00:00.000Z',
              },
            ],
            total: 1,
            page: 1,
            pages: 1,
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
        return {
          code: 200,
          message: 'ok',
          data: {
            items: [
              {
                id: 11,
                video_file_id: 1,
                template_id: 1,
                ai_config_id: 7,
                status: 'success',
                progress: 100,
                result_summary: 'summary',
                processing_time: 1,
                model_name: 'm1',
                api_provider: 'custom',
                total_tokens: 10,
                prompt_tokens: 4,
                completion_tokens: 6,
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
      if (url === '/video-analysis/videos/1') {
        return { code: 200, message: 'ok', data: { id: 1, title: '视频1', original_filename: 'video-1.mp4' } }
      }
      if (url === '/video-analysis/11') {
        return {
          code: 200,
          message: 'ok',
          data: {
            id: 11,
            video_file_id: 1,
            template_id: 1,
            ai_config_id: 7,
            prompt_content: 'prompt',
            status: 'success',
            progress: 100,
            analysis_result: 'result',
            result_metadata: { tag_candidates: [{ tag_name: '新标签', confidence: 0.7, reason: 'r' }] },
            created_at: '2026-06-16T00:00:00.000Z',
            updated_at: '2026-06-16T00:00:00.000Z',
            completed_at: '2026-06-16T00:00:01.000Z',
          },
        }
      }
      if (url === '/uploaded-files/1/tags') {
        return { code: 200, message: 'ok', data: [] }
      }

      throw new Error(`unexpected url: ${url}`)
    })

    apiServiceMock.post.mockImplementation(async (url: string) => {
      throw new Error(`unexpected post url: ${url}`)
    })

    render(
      <MemoryRouter initialEntries={['/video/analysis']}>
        <Routes>
          <Route path="/video/analysis" element={<VideoAnalysis />} />
          <Route path="/video/analysis/history/:analysisId" element={<VideoAnalysisHistoryDetail />} />
        </Routes>
      </MemoryRouter>,
    )

    const tagButton = await screen.findByRole('button', { name: '查看详情/根据解析结果打标' })

    fireEvent.click(tagButton)

    await screen.findByText(/解析结果详情 #11/)
    await screen.findByText('解析结果打标')
    await screen.findByText('当前标签')
  })
})
