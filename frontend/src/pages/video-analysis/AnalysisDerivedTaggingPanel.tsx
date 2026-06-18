/**
 * 解析结果打标面板
 *
 * 功能说明：
 * - 基于已完成的 AI 视频解析结果再次调用 AI 生成候选标签
 * - 候选标签需用户勾选确认后才采纳进入当前标签集合
 * - 采纳时写入 source=ai_assisted，用于前端以 AI 颜色展示（不在标签文字上加“人工”字样）
 */

import React, { useEffect, useMemo, useState } from 'react'
import apiService from '../../services/api'
import type { AIConfig, EffectiveTag, TagGroup } from './types'

export interface AnalysisTagCandidate {
  tag_name: string
  confidence: number
  reason?: string
  evidence_start_seconds?: number | null
  evidence_end_seconds?: number | null
}

export interface AnalysisDerivedTaggingPanelProps {
  analysisId: number
  videoFileId: number
  aiConfigs?: AIConfig[]
  tagGroups?: TagGroup[]
  defaultAIConfigId?: number
  defaultTagGroupIds?: number[]
  showNotification: (type: 'success' | 'error' | 'info', message: string) => void
}

const AnalysisDerivedTaggingPanel: React.FC<AnalysisDerivedTaggingPanelProps> = ({
  analysisId,
  videoFileId,
  aiConfigs,
  tagGroups,
  defaultAIConfigId,
  defaultTagGroupIds,
  showNotification,
}) => {
  const [existingTags, setExistingTags] = useState<EffectiveTag[]>([])
  const [loadingTags, setLoadingTags] = useState(false)
  const [candidates, setCandidates] = useState<AnalysisTagCandidate[]>([])
  const [selectedNames, setSelectedNames] = useState<Record<string, boolean>>({})
  const [generating, setGenerating] = useState(false)
  const [adopting, setAdopting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedAIConfigId, setSelectedAIConfigId] = useState<number | ''>(defaultAIConfigId || '')
  const [selectedTagGroupIds, setSelectedTagGroupIds] = useState<number[]>(defaultTagGroupIds || [])

  const effectiveTagNameSet = useMemo(() => {
    return new Set(existingTags.filter((tag) => tag.is_effective).map((tag) => (tag.tag_name || tag.tag_name_snapshot || '').trim()))
  }, [existingTags])

  const excludedTagNameSet = useMemo(() => {
    return new Set(existingTags.filter((tag) => !tag.is_effective).map((tag) => (tag.tag_name || tag.tag_name_snapshot || '').trim()))
  }, [existingTags])

  const refreshTags = async () => {
    setLoadingTags(true)
    try {
      const result = await apiService.get<EffectiveTag[]>(`/uploaded-files/${videoFileId}/tags`)
      setExistingTags(result.data || [])
    } catch (err) {
      setExistingTags([])
    } finally {
      setLoadingTags(false)
    }
  }

  useEffect(() => {
    refreshTags()
  }, [videoFileId])

  useEffect(() => {
    setCandidates([])
    setSelectedNames({})
    setError(null)
  }, [analysisId])

  useEffect(() => {
    const nextSelected: Record<string, boolean> = {}
    for (const item of candidates) {
      const name = (item.tag_name || '').trim()
      if (!name) {
        continue
      }
      if (effectiveTagNameSet.has(name)) {
        nextSelected[name] = false
        continue
      }
      nextSelected[name] = true
    }
    setSelectedNames(nextSelected)
  }, [candidates, effectiveTagNameSet])

  const hasCandidates = candidates.length > 0

  const selectedCandidates = useMemo(() => {
    return candidates.filter((item) => selectedNames[(item.tag_name || '').trim()])
  }, [candidates, selectedNames])

  const canCustomizeGenerator = Boolean(aiConfigs && aiConfigs.length > 0) || Boolean(tagGroups && tagGroups.length > 0)

  const buildGenerateUrl = (force: boolean) => {
    const params: string[] = []
    if (force) {
      params.push('force=true')
    }
    if (selectedAIConfigId !== '') {
      params.push(`ai_config_id=${encodeURIComponent(String(selectedAIConfigId))}`)
    }
    for (const id of selectedTagGroupIds) {
      params.push(`tag_group_ids=${encodeURIComponent(String(id))}`)
    }
    const query = params.length > 0 ? `?${params.join('&')}` : ''
    return `/video-analysis/${analysisId}/tag-candidates${query}`
  }

  const getErrorMessage = (err: any, fallback: string) => {
    const detail = err?.response?.data?.detail
    const message = err?.response?.data?.message
    if (typeof detail === 'string' && detail.trim()) {
      return detail.trim()
    }
    if (typeof message === 'string' && message.trim()) {
      return message.trim()
    }
    if (typeof err?.message === 'string' && err.message.trim()) {
      return err.message.trim()
    }
    return fallback
  }

  const generateCandidates = async (force: boolean) => {
    setGenerating(true)
    setError(null)
    try {
      const url = buildGenerateUrl(force)
      const result = await apiService.post<{ tag_candidates: AnalysisTagCandidate[] }>(url)
      const tagCandidates = (result.data as any)?.tag_candidates || []
      setCandidates(tagCandidates)
      showNotification('success', '候选标签已生成')
    } catch (err) {
      const errorMessage = getErrorMessage(err, '生成候选标签失败')
      setError(errorMessage)
      showNotification('error', errorMessage)
    } finally {
      setGenerating(false)
    }
  }

  const toggleSelected = (tagName: string) => {
    if (effectiveTagNameSet.has(tagName)) {
      return
    }
    setSelectedNames((prev) => ({
      ...prev,
      [tagName]: !prev[tagName],
    }))
  }

  const adoptSelected = async () => {
    const operations = selectedCandidates
      .map((candidate) => {
        const name = (candidate.tag_name || '').trim()
        if (!name) {
          return null
        }
        if (effectiveTagNameSet.has(name)) {
          return null
        }
        return {
          action: 'add',
          tag_name: name,
          confidence: typeof candidate.confidence === 'number' ? candidate.confidence : 0,
          note: `analysis_id=${analysisId}`,
          source: 'ai_assisted',
        }
      })
      .filter(Boolean)

    if (operations.length === 0) {
      showNotification('info', '没有可采纳的标签')
      return
    }

    setAdopting(true)
    setError(null)
    try {
      await apiService.post(`/uploaded-files/${videoFileId}/tags/revisions`, {
        change_reason: '采纳解析候选标签',
        operations,
      })
      await refreshTags()
      showNotification('success', '已采纳所选标签')
      setSelectedNames({})
    } catch (err) {
      setError('采纳标签失败')
      showNotification('error', '采纳标签失败')
    } finally {
      setAdopting(false)
    }
  }

  return (
    <div className="bg-white border border-gray-200 text-gray-800 rounded-lg overflow-hidden shadow-sm mb-4">
      <div className="px-4 py-3 bg-gray-50 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <i className="fas fa-tags text-gray-500 mr-2"></i>
            <span className="font-medium text-gray-900">解析结果打标</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => generateCandidates(true)}
              disabled={generating}
              className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-100 disabled:bg-gray-200 disabled:text-gray-500 disabled:cursor-not-allowed transition-colors"
            >
              {generating ? '生成中...' : hasCandidates ? '重新生成' : '生成候选标签'}
            </button>
          </div>
        </div>
      </div>

      <div className="p-4 space-y-3">
        {error && <div className="text-sm text-red-600">{error}</div>}

        {loadingTags && <div className="text-xs text-gray-500">加载当前标签中...</div>}

        {canCustomizeGenerator && (
          <div className="rounded-lg border border-gray-200 bg-gray-50 p-3 space-y-3">
            {aiConfigs && aiConfigs.length > 0 && (
              <div className="flex items-center gap-3">
                <div className="text-xs text-gray-600 whitespace-nowrap">AI 配置</div>
                <select
                  value={selectedAIConfigId}
                  onChange={(e) => {
                    const next = e.target.value
                    setSelectedAIConfigId(next ? Number(next) : '')
                  }}
                  className="flex-1 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm"
                >
                  <option value="">沿用解析配置</option>
                  {aiConfigs
                    .filter((cfg) => cfg.is_active)
                    .map((cfg) => (
                      <option key={cfg.id} value={cfg.id}>
                        {cfg.name} ({[cfg.provider, cfg.model].filter(Boolean).join('/')})
                      </option>
                    ))}
                </select>
              </div>
            )}

            {tagGroups && tagGroups.length > 0 && (
              <div className="space-y-2">
                <div className="text-xs text-gray-600">标签组（为空则沿用解析配置）</div>
                <div className="flex flex-wrap gap-2">
                  {tagGroups
                    .filter((group) => group.is_active)
                    .map((group) => {
                      const checked = selectedTagGroupIds.includes(group.id)
                      return (
                        <label
                          key={group.id}
                          className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs cursor-pointer ${
                            checked ? 'border-blue-300 bg-white text-blue-700' : 'border-gray-200 bg-white text-gray-700'
                          }`}
                        >
                          <input
                            type="checkbox"
                            aria-label={`选择标签组 ${group.name}`}
                            checked={checked}
                            onChange={() => {
                              setSelectedTagGroupIds((prev) => {
                                if (prev.includes(group.id)) {
                                  return prev.filter((id) => id !== group.id)
                                }
                                return [...prev, group.id]
                              })
                            }}
                          />
                          <span>{group.name}</span>
                        </label>
                      )
                    })}
                </div>
              </div>
            )}
          </div>
        )}

        {candidates.length > 0 ? (
          <div className="space-y-2">
            {candidates.map((item) => {
              const name = (item.tag_name || '').trim()
              if (!name) {
                return null
              }
              const isEffective = effectiveTagNameSet.has(name)
              const isExcluded = excludedTagNameSet.has(name)
              const checked = !!selectedNames[name]
              return (
                <label
                  key={name}
                  className={`flex items-start gap-2 rounded-lg border px-3 py-2 cursor-pointer ${
                    isEffective ? 'bg-gray-50 border-gray-200 cursor-not-allowed' : 'bg-white border-gray-200 hover:bg-gray-50'
                  }`}
                >
                  <input
                    type="checkbox"
                    aria-label={`选择候选标签 ${name}`}
                    checked={checked}
                    disabled={isEffective}
                    onChange={() => toggleSelected(name)}
                    className="mt-1"
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <div className="font-medium text-sm text-gray-900 truncate">{name}</div>
                      <div className="text-xs text-gray-500 whitespace-nowrap">
                        {Math.round((item.confidence || 0) * 100)}%
                      </div>
                    </div>
                    {isEffective && <div className="text-xs text-gray-500 mt-1">已存在（当前生效）</div>}
                    {!isEffective && isExcluded && <div className="text-xs text-gray-500 mt-1">已存在（已排除，采纳将恢复）</div>}
                    {item.reason && <div className="text-xs text-gray-600 mt-1 line-clamp-2">{item.reason}</div>}
                  </div>
                </label>
              )
            })}

            <div className="flex justify-end pt-2">
              <button
                type="button"
                onClick={adoptSelected}
                disabled={adopting || selectedCandidates.length === 0}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:text-gray-500 disabled:cursor-not-allowed transition-colors"
              >
                {adopting ? '采纳中...' : `采纳所选为标签(${selectedCandidates.length})`}
              </button>
            </div>
          </div>
        ) : (
          <div className="text-sm text-gray-500">暂无候选标签，可先点击“生成候选标签”。</div>
        )}
      </div>
    </div>
  )
}

export default AnalysisDerivedTaggingPanel
