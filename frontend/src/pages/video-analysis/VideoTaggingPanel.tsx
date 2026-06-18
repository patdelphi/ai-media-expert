import React, { useEffect, useMemo, useRef, useState } from 'react'
import type {
  AIConfig,
  AutoTagTask,
  AutoTagTaskHistoryItem,
  EffectiveTag,
  TagGroup,
  TagRevision,
  VideoFile,
} from './types'
import apiService from '../../services/api'

type TagFilter = 'all' | 'effective' | 'excluded'

export interface VideoTaggingPanelProps {
  video: VideoFile
  aiConfigs: AIConfig[]
  tagGroups: TagGroup[]
  selectedAIConfig: AIConfig | null
  setSelectedAIConfig: (value: AIConfig | null) => void
  selectedTagGroups: number[]
  setSelectedTagGroups: (value: number[]) => void
  transmissionMethod: 'url' | 'base64' | 'upload'
  setTransmissionMethod: (value: 'url' | 'base64' | 'upload') => void
  showNotification: (type: 'success' | 'error' | 'info', message: string) => void
  onBackPrev?: () => void
  onBack: () => void
}

const VideoTaggingPanel: React.FC<VideoTaggingPanelProps> = ({
  video,
  aiConfigs,
  tagGroups,
  selectedAIConfig,
  setSelectedAIConfig,
  selectedTagGroups,
  setSelectedTagGroups,
  transmissionMethod,
  setTransmissionMethod,
  showNotification,
  onBackPrev,
  onBack,
}) => {
  const autoTagPollingRef = useRef<number | null>(null)
  const [currentAutoTagTask, setCurrentAutoTagTask] = useState<AutoTagTask | null>(null)
  const [autoTagHistory, setAutoTagHistory] = useState<AutoTagTaskHistoryItem[]>([])
  const [tags, setTags] = useState<EffectiveTag[]>([])
  const [tagRevisions, setTagRevisions] = useState<TagRevision[]>([])
  const [autoTagLoading, setAutoTagLoading] = useState(false)
  const [autoTagRefreshing, setAutoTagRefreshing] = useState(false)
  const [autoTagError, setAutoTagError] = useState<string | null>(null)
  const [newManualTag, setNewManualTag] = useState('')
  const [revisionReason, setRevisionReason] = useState('')
  const [tagFilter, setTagFilter] = useState<TagFilter>('all')

  const clearAutoTagPolling = () => {
    if (autoTagPollingRef.current) {
      clearInterval(autoTagPollingRef.current)
      autoTagPollingRef.current = null
    }
  }

  useEffect(() => {
    return () => {
      clearAutoTagPolling()
    }
  }, [])

  const getTagName = (tag: EffectiveTag) => {
    return (tag.tag_name || tag.tag_name_snapshot || '').trim()
  }

  const refresh = async (options?: { silent?: boolean }) => {
    const silent = options?.silent ?? false
    if (!silent) {
      setAutoTagRefreshing(true)
    }
    setAutoTagError(null)
    try {
      const [tagsResult, revisionsResult, historyResult] = await Promise.all([
        apiService.get<EffectiveTag[]>(`/uploaded-files/${video.id}/tags`),
        apiService.get<TagRevision[]>(`/uploaded-files/${video.id}/tags/revisions`),
        apiService.get<AutoTagTaskHistoryItem[]>(`/video-auto-tags/video-files/${video.id}/tasks`),
      ])

      const nextTags = (tagsResult.data || []).map((item) => ({
        ...item,
        tag_name: getTagName(item),
      }))
      const nextHistory = historyResult.data || []

      setTags(nextTags)
      setTagRevisions(revisionsResult.data || [])
      setAutoTagHistory(nextHistory)

      if (nextHistory.length > 0) {
        const latestTaskId = nextHistory[0].id
        if (!currentAutoTagTask || currentAutoTagTask.id !== latestTaskId) {
          await loadAutoTagTaskDetail(latestTaskId)
        }
      } else {
        setCurrentAutoTagTask(null)
      }
    } catch (err) {
      console.error('Failed to load tagging data:', err)
      setAutoTagError('加载打标数据失败')
      setTags([])
      setTagRevisions([])
      setAutoTagHistory([])
    } finally {
      if (!silent) {
        setAutoTagRefreshing(false)
      }
    }
  }

  useEffect(() => {
    refresh()
  }, [video.id])

  const loadAutoTagTaskDetail = async (taskId: number) => {
    try {
      const result = await apiService.get<AutoTagTask>(`/video-auto-tags/${taskId}`)
      setCurrentAutoTagTask(result.data)
      return result.data
    } catch (err) {
      console.error('Failed to load auto tag task detail:', err)
      setAutoTagError('加载自动打标任务详情失败')
      return null
    }
  }

  const startAutoTagging = async () => {
    if (!selectedAIConfig) {
      showNotification('error', '请先选择 AI 配置')
      return
    }

    setAutoTagLoading(true)
    setAutoTagError(null)
    clearAutoTagPolling()

    try {
      const result = await apiService.post<{ task_id: number; status: string; message: string }>(
        '/video-auto-tags/start',
        {
          video_file_id: video.id,
          ai_config_id: selectedAIConfig.id,
          tag_group_ids: selectedTagGroups,
          transmission_method: transmissionMethod,
        },
      )

      const taskId = result.data.task_id
      const initialTask = await loadAutoTagTaskDetail(taskId)
      if (initialTask) {
        setCurrentAutoTagTask(initialTask)
      }
      showNotification('success', '自动打标任务已启动')

      autoTagPollingRef.current = window.setInterval(async () => {
        const latestTask = await loadAutoTagTaskDetail(taskId)
        if (!latestTask) {
          clearAutoTagPolling()
          return
        }
        if (latestTask.status === 'completed') {
          clearAutoTagPolling()
          await refresh({ silent: true })
          showNotification('success', '自动打标已完成')
        } else if (latestTask.status === 'failed') {
          clearAutoTagPolling()
          showNotification('error', latestTask.error_message || '自动打标失败')
        }
      }, 3000)
    } catch (err) {
      console.error('Failed to start auto tagging:', err)
      setAutoTagError('启动自动打标失败')
      showNotification('error', '启动自动打标失败')
    } finally {
      setAutoTagLoading(false)
    }
  }

  const submitTagRevision = async (operations: Array<Record<string, unknown>>, successMessage: string) => {
    try {
      await apiService.post(`/uploaded-files/${video.id}/tags/revisions`, {
        change_reason: revisionReason.trim() || undefined,
        operations,
      })
      await refresh({ silent: true })
      setRevisionReason('')
      showNotification('success', successMessage)
    } catch (err) {
      console.error('Failed to create tag revision:', err)
      showNotification('error', '标签修订失败')
    }
  }

  const addManualTag = async () => {
    const tagName = newManualTag.trim()
    if (!tagName) {
      showNotification('error', '请输入要添加的标签')
      return
    }

    await submitTagRevision(
      [
        {
          action: 'add',
          tag_name: tagName,
          confidence: 1,
          note: revisionReason.trim() || '前端人工新增标签',
        },
      ],
      '标签已添加',
    )
    setNewManualTag('')
  }

  const toggleTagGroup = (tagGroupId: number) => {
    if (selectedTagGroups.includes(tagGroupId)) {
      setSelectedTagGroups(selectedTagGroups.filter((id) => id !== tagGroupId))
      return
    }
    setSelectedTagGroups([...selectedTagGroups, tagGroupId])
  }

  const handleTagAction = async (tag: EffectiveTag) => {
    const tagName = getTagName(tag)
    if (!tagName) {
      showNotification('error', '标签名称不能为空')
      return
    }

    if (tag.is_effective) {
      const confirmed = window.confirm(
        `确认将标签“${tagName}”标记为当前不生效吗？\n\n说明：标签会保留在历史集合中，但不会参与当前生效标签。`,
      )
      if (!confirmed) {
        return
      }
      await submitTagRevision(
        [
          {
            action: 'remove',
            tag_name: tagName,
            note: revisionReason.trim() || '前端人工移除标签',
          },
        ],
        '标签已排除',
      )
      return
    }

    const confirmed = window.confirm(`是否恢复标签“${tagName}”？`)
    if (!confirmed) {
      return
    }
    await submitTagRevision(
      [
        {
          action: 'add',
          tag_name: tagName,
          confidence: 1,
          note: revisionReason.trim() || '前端恢复已排除标签',
        },
      ],
      '标签已恢复',
    )
  }

  const filteredTags = useMemo(() => {
    const collator =
      typeof Intl !== 'undefined' && typeof Intl.Collator !== 'undefined'
        ? new Intl.Collator('zh-Hans-u-co-pinyin', { sensitivity: 'base' })
        : null

    const compareNames = (left: string, right: string) => {
      if (collator) {
        return collator.compare(left, right)
      }
      return left.localeCompare(right, 'zh-Hans-CN')
    }

    const getGroupOrder = (tag: EffectiveTag) => {
      if (!tag.is_effective) {
        return 2
      }
      if (tag.source === 'ai_auto' || tag.source === 'ai_assisted') {
        return 0
      }
      return 1
    }

    const sortTags = (items: EffectiveTag[]) => {
      return [...items].sort((left, right) => {
        const groupDiff = getGroupOrder(left) - getGroupOrder(right)
        if (groupDiff !== 0) {
          return groupDiff
        }
        return compareNames(getTagName(left), getTagName(right))
      })
    }

    if (tagFilter === 'effective') {
      return sortTags(tags.filter((item) => item.is_effective))
    }
    if (tagFilter === 'excluded') {
      return sortTags(tags.filter((item) => !item.is_effective))
    }
    return sortTags(tags)
  }, [tagFilter, tags])

  const filterCounts = useMemo(() => {
    return {
      all: tags.length,
      effective: tags.filter((item) => item.is_effective).length,
      excluded: tags.filter((item) => !item.is_effective).length,
    }
  }, [tags])

  return (
    <div className="bg-white rounded-lg shadow-sm">
      <div className="p-6">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
          <div className="space-y-1">
            <h2 className="text-xl font-semibold">视频打标</h2>
            <div className="text-sm text-gray-600">
              当前视频：{video.title || video.original_filename}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onBackPrev || onBack}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              返回上一页
            </button>
            <button
              type="button"
              onClick={onBack}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              返回选择视频
            </button>
          </div>
        </div>

        <div className="space-y-6">
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
            <div className="rounded-lg border border-gray-200 p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-medium">AI 配置</h3>
                <span className="text-sm text-gray-500">{aiConfigs.length} 个</span>
              </div>
              {aiConfigs.length > 0 ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {aiConfigs.map((config) => (
                    <button
                      key={config.id}
                      type="button"
                      onClick={() => setSelectedAIConfig(config)}
                      className={`text-left p-3 rounded-lg border transition-colors ${
                        selectedAIConfig?.id === config.id
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'
                      }`}
                    >
                      <div className="font-medium text-gray-900">{config.name}</div>
                      <div className="text-xs text-gray-500">
                        {config.provider} / {config.model}
                      </div>
                    </button>
                  ))}
                </div>
              ) : (
                <div className="text-sm text-gray-500">暂无 AI 配置，请先在系统配置中添加。</div>
              )}
            </div>

            <div className="rounded-lg border border-gray-200 p-4 space-y-4">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-lg font-medium">标签组</h3>
                  <span className="text-sm text-gray-500">{selectedTagGroups.length} 个已选</span>
                </div>
                {tagGroups.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {tagGroups
                      .filter((group) => group.is_active)
                      .map((group) => (
                        <button
                          key={group.id}
                          type="button"
                          onClick={() => toggleTagGroup(group.id)}
                          className={`px-3 py-1.5 rounded-full text-sm border transition-colors ${
                            selectedTagGroups.includes(group.id)
                              ? 'bg-blue-50 text-blue-700 border-blue-200'
                              : 'bg-white text-gray-700 border-gray-200 hover:bg-gray-50'
                          }`}
                        >
                          {group.name}
                        </button>
                      ))}
                  </div>
                ) : (
                  <div className="text-sm text-gray-500">暂无标签组。</div>
                )}
              </div>

              <div>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-lg font-medium">视频传输方式</h3>
                  <span className="text-sm text-gray-500">{transmissionMethod}</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {(['url', 'base64', 'upload'] as const).map((method) => (
                    <button
                      key={method}
                      type="button"
                      onClick={() => setTransmissionMethod(method)}
                      className={`px-3 py-1.5 rounded-full text-sm border transition-colors ${
                        transmissionMethod === method
                          ? 'bg-purple-50 text-purple-700 border-purple-200'
                          : 'bg-white text-gray-700 border-gray-200 hover:bg-gray-50'
                      }`}
                    >
                      {method}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <div className="rounded-lg border border-purple-200 bg-purple-50 px-4 py-3 space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h3 className="text-lg font-medium text-purple-900">自动打标</h3>
                <p className="text-sm text-purple-700">
                  启动后会生成历史标签集合；模板解析会默认复用当前生效标签上下文。
                </p>
              </div>
              <div className="flex items-center gap-3">
                {autoTagRefreshing && <span className="text-sm text-gray-500">刷新中...</span>}
                <button
                  type="button"
                  onClick={() => refresh()}
                  disabled={autoTagRefreshing}
                  className="px-4 py-2 border border-purple-200 bg-white text-purple-700 rounded-lg hover:bg-purple-100 disabled:bg-gray-200 disabled:text-gray-500 disabled:cursor-not-allowed transition-colors"
                >
                  刷新
                </button>
                <button
                  type="button"
                  onClick={startAutoTagging}
                  disabled={!selectedAIConfig || autoTagLoading}
                  className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-300 disabled:text-gray-500 disabled:cursor-not-allowed transition-colors"
                >
                  {autoTagLoading ? '启动中...' : '开始自动打标'}
                </button>
              </div>
            </div>

            {autoTagError && (
              <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                {autoTagError}
              </div>
            )}

            {currentAutoTagTask && (
              <div className="rounded-lg border border-purple-200 bg-white px-4 py-3 space-y-2">
                <div className="flex flex-wrap items-center gap-3 text-sm">
                  <span className="font-medium text-purple-900">最近自动打标任务 #{currentAutoTagTask.id}</span>
                  <span className="px-2 py-1 rounded-full bg-purple-50 text-purple-700 border border-purple-200">
                    状态: {currentAutoTagTask.status}
                  </span>
                  <span className="text-purple-700">进度: {currentAutoTagTask.progress}%</span>
                </div>
                {currentAutoTagTask.structured_summary && (
                  <div className="text-sm text-purple-900">
                    <span className="font-medium">结构化摘要：</span>
                    <span className="ml-1">
                      {typeof currentAutoTagTask.structured_summary === 'string'
                        ? currentAutoTagTask.structured_summary
                        : JSON.stringify(currentAutoTagTask.structured_summary)}
                    </span>
                  </div>
                )}
                {currentAutoTagTask.items?.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {currentAutoTagTask.items.map((item) => (
                      <span
                        key={item.id}
                        className="inline-flex items-center px-2.5 py-1 rounded-full text-xs bg-purple-50 text-purple-700 border border-purple-200"
                      >
                        {item.tag_name} ({Math.round(item.confidence * 100)}%)
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
            <div className="rounded-lg border border-gray-200 p-4">
              <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
                <div className="flex items-center gap-2">
                  <h4 className="font-medium text-gray-900">历史标签集合</h4>
                  <span className="text-sm text-gray-500">{filterCounts.all} 个</span>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setTagFilter('all')}
                    className={`px-3 py-1.5 rounded-full text-sm border transition-colors ${
                      tagFilter === 'all'
                        ? 'bg-blue-50 text-blue-700 border-blue-200'
                        : 'bg-white text-gray-700 border-gray-200 hover:bg-gray-50'
                    }`}
                  >
                    全部({filterCounts.all})
                  </button>
                  <button
                    type="button"
                    onClick={() => setTagFilter('effective')}
                    className={`px-3 py-1.5 rounded-full text-sm border transition-colors ${
                      tagFilter === 'effective'
                        ? 'bg-green-50 text-green-700 border-green-200'
                        : 'bg-white text-gray-700 border-gray-200 hover:bg-gray-50'
                    }`}
                  >
                    当前生效({filterCounts.effective})
                  </button>
                  <button
                    type="button"
                    onClick={() => setTagFilter('excluded')}
                    className={`px-3 py-1.5 rounded-full text-sm border transition-colors ${
                      tagFilter === 'excluded'
                        ? 'bg-gray-100 text-gray-700 border-gray-200'
                        : 'bg-white text-gray-700 border-gray-200 hover:bg-gray-50'
                    }`}
                  >
                    已排除({filterCounts.excluded})
                  </button>
                </div>
              </div>

              {filteredTags.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {filteredTags.map((tag) => {
                    const tagName = getTagName(tag) || '未命名标签'
                    const actionLabel = tag.is_effective ? `排除标签 ${tagName}` : `恢复标签 ${tagName}`
                    const isManualTag = tag.source === 'manual_override'
                    return (
                      <span
                        key={tag.id}
                        className={`inline-flex items-center px-2.5 py-1 rounded-full text-sm border ${
                          tag.is_effective
                            ? isManualTag
                              ? 'bg-green-50 text-green-700 border-green-200'
                              : 'bg-blue-50 text-blue-700 border-blue-200'
                            : isManualTag
                              ? 'bg-green-50 text-green-600 border-green-200 opacity-80'
                              : 'bg-gray-100 text-gray-600 border-gray-200'
                        }`}
                      >
                        <span>{tagName}</span>
                        <span
                          className={`ml-2 text-xs ${
                            tag.is_effective
                              ? isManualTag
                                ? 'text-green-600'
                                : 'text-blue-500'
                              : 'text-gray-400'
                          }`}
                        >
                          {Math.round(tag.confidence * 100)}%
                        </span>
                        {!tag.is_effective && (
                          <span className="ml-2 inline-flex items-center rounded-full bg-white px-2 py-0.5 text-xs text-gray-500 border border-gray-200">
                            已排除
                          </span>
                        )}
                        <button
                          type="button"
                          onClick={() => handleTagAction(tag)}
                          className="ml-2 text-blue-600 hover:text-red-600 transition-colors"
                          aria-label={actionLabel}
                        >
                          <i className="fas fa-times"></i>
                        </button>
                      </span>
                    )
                  })}
                </div>
              ) : (
                <div className="text-sm text-gray-500">当前还没有历史标签，可先启动自动打标。</div>
              )}

              <div className="mt-3 text-xs text-gray-500">
                颜色说明：蓝色=AI（自动打标/解析派生），绿色=人工修订，灰色=已排除
              </div>
              <div className="mt-1 text-xs text-gray-500">
                百分比显示为该标签在历史自动打标/人工修订中的最高置信度；人工新增/恢复标签默认按 100% 展示。
              </div>
            </div>

            <div className="rounded-lg border border-gray-200 p-4 space-y-3">
              <h4 className="font-medium text-gray-900">人工修订</h4>
              <input
                type="text"
                value={newManualTag}
                onChange={(e) => setNewManualTag(e.target.value)}
                placeholder="输入要添加的标签"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
              <textarea
                value={revisionReason}
                onChange={(e) => setRevisionReason(e.target.value)}
                placeholder="修订原因（可选）"
                className="w-full h-24 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
              <div className="flex justify-end">
                <button
                  type="button"
                  onClick={addManualTag}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:text-gray-500 disabled:cursor-not-allowed transition-colors"
                >
                  添加标签
                </button>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
            <div className="rounded-lg border border-gray-200 p-4">
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-medium text-gray-900">自动打标历史</h4>
                <span className="text-sm text-gray-500">{autoTagHistory.length} 次</span>
              </div>
              {autoTagHistory.length > 0 ? (
                <div className="space-y-3">
                  {autoTagHistory.map((task) => (
                    <div key={task.id} className="rounded-lg bg-gray-50 p-3">
                      <div className="flex flex-wrap items-center gap-3 mb-2 text-sm">
                        <button
                          type="button"
                          onClick={() => loadAutoTagTaskDetail(task.id)}
                          className="font-medium text-left text-purple-700 hover:text-purple-900 transition-colors"
                        >
                          任务 #{task.id}
                        </button>
                        <span className="px-2 py-1 rounded-full bg-white text-gray-700 border border-gray-200">
                          {task.status}
                        </span>
                        <span className="text-gray-500">{new Date(task.created_at).toLocaleString()}</span>
                      </div>
                      {task.structured_summary && (
                        <div className="text-sm text-gray-700 mb-2">
                          {typeof task.structured_summary === 'string'
                            ? task.structured_summary
                            : JSON.stringify(task.structured_summary)}
                        </div>
                      )}
                      {task.items?.length > 0 && (
                        <div className="flex flex-wrap gap-2">
                          {task.items.map((item) => (
                            <span
                              key={`${task.id}-${item.id}`}
                              className="inline-flex items-center px-2.5 py-1 rounded-full text-xs bg-white text-gray-700 border border-gray-200"
                            >
                              {item.tag_name} ({Math.round(item.confidence * 100)}%)
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-sm text-gray-500">暂无自动打标历史。</div>
              )}
            </div>

            <div className="rounded-lg border border-gray-200 p-4">
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-medium text-gray-900">修订历史</h4>
                <span className="text-sm text-gray-500">{tagRevisions.length} 条</span>
              </div>
              {tagRevisions.length > 0 ? (
                <div className="space-y-3">
                  {tagRevisions.map((revision) => (
                    <div key={revision.id} className="rounded-lg bg-gray-50 p-3">
                      <div className="flex flex-wrap items-center gap-3 mb-2 text-sm">
                        <span className="font-medium text-gray-900">版本 #{revision.revision_number}</span>
                        <span className="text-gray-500">{new Date(revision.created_at).toLocaleString()}</span>
                        {revision.change_reason && (
                          <span className="text-gray-600">原因: {revision.change_reason}</span>
                        )}
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {revision.items.map((item) => (
                          <span
                            key={item.id}
                            className="inline-flex items-center px-2.5 py-1 rounded-full text-xs bg-white text-gray-700 border border-gray-200"
                          >
                            {item.action}: {item.tag_name}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-sm text-gray-500">暂无修订历史。</div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default VideoTaggingPanel
