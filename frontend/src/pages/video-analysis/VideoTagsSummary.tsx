import React, { useEffect, useMemo, useState } from 'react'
import apiService from '../../services/api'
import type { EffectiveTag, VideoTokenSummary } from './types'

export interface VideoTagsSummaryProps {
  videoFileId: number
}

const VideoTagsSummary: React.FC<VideoTagsSummaryProps> = ({ videoFileId }) => {
  const [tags, setTags] = useState<EffectiveTag[]>([])
  const [loading, setLoading] = useState(false)
  const [tokenSummary, setTokenSummary] = useState<VideoTokenSummary | null>(null)
  const [tokenLoading, setTokenLoading] = useState(false)

  const getTagName = (tag: EffectiveTag) => {
    return (tag.tag_name || tag.tag_name_snapshot || '').trim()
  }

  const loadTags = async () => {
    setLoading(true)
    try {
      const result = await apiService.get<EffectiveTag[]>(`/uploaded-files/${videoFileId}/tags`)
      const next = (result.data || []).map((item) => ({
        ...item,
        tag_name: getTagName(item),
      }))
      setTags(next)
    } catch {
      setTags([])
    } finally {
      setLoading(false)
    }
  }

  const loadTokenSummary = async () => {
    setTokenLoading(true)
    try {
      const result = await apiService.get<VideoTokenSummary>(`/video-analysis/videos/${videoFileId}/token-summary`)
      setTokenSummary(result.data || null)
    } catch {
      setTokenSummary(null)
    } finally {
      setTokenLoading(false)
    }
  }

  useEffect(() => {
    loadTags()
    loadTokenSummary()
  }, [videoFileId])

  const effectiveCount = useMemo(() => tags.filter((tag) => tag.is_effective).length, [tags])

  return (
    <div className="mb-6">
      <div className="mb-6 bg-white border border-gray-200 rounded-lg p-4">
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-lg font-medium">Token 汇总</h4>
          <span className="text-xs text-gray-500">用于解释“多次解析/多次打标”的累计消耗</span>
        </div>
        {tokenLoading ? (
          <div className="text-sm text-gray-500">加载中...</div>
        ) : !tokenSummary ? (
          <div className="text-sm text-gray-500">暂无 token 汇总数据</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm text-gray-700">
            <div className="flex items-center justify-between">
              <span className="text-gray-600">解析（估算）</span>
              <span>
                {tokenSummary.analysis.total_tokens} ({tokenSummary.analysis.prompt_tokens}+{tokenSummary.analysis.completion_tokens})
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">上传视频打标</span>
              <span>
                {tokenSummary.auto_tag.total_tokens} ({tokenSummary.auto_tag.prompt_tokens}+{tokenSummary.auto_tag.completion_tokens})
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">根据解析结果打标</span>
              <span>
                {tokenSummary.analysis_derived_tagging.total_tokens} ({tokenSummary.analysis_derived_tagging.prompt_tokens}+{tokenSummary.analysis_derived_tagging.completion_tokens})
              </span>
            </div>
            <div className="flex items-center justify-between font-medium">
              <span>总计</span>
              <span>
                {tokenSummary.total.total_tokens} ({tokenSummary.total.prompt_tokens}+{tokenSummary.total.completion_tokens})
              </span>
            </div>
          </div>
        )}
      </div>

      <div className="flex items-center justify-between mb-3">
        <h4 className="text-lg font-medium">当前标签</h4>
        <span className="text-sm text-gray-500">{effectiveCount} 个生效</span>
      </div>

      {loading ? (
        <div className="text-sm text-gray-500">加载标签中...</div>
      ) : tags.length === 0 ? (
        <div className="text-sm text-gray-500">暂无标签</div>
      ) : (
        <div className="flex flex-wrap gap-2">
          {tags.map((tag) => {
            const tagName = getTagName(tag) || '未命名标签'
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
                <span className="ml-2 text-xs text-gray-500">{Math.round(tag.confidence * 100)}%</span>
                {!tag.is_effective && (
                  <span className="ml-2 inline-flex items-center rounded-full bg-white px-2 py-0.5 text-xs text-gray-500 border border-gray-200">
                    已排除
                  </span>
                )}
              </span>
            )
          })}
        </div>
      )}

      <div className="mt-3 text-xs text-gray-500">
        颜色说明：蓝色=AI（自动打标/解析派生），绿色=人工修订，灰色=已排除
      </div>
    </div>
  )
}

export default VideoTagsSummary
