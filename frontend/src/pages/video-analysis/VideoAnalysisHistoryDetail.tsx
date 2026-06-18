/**
 * 解析历史详情页
 *
 * 功能说明：
 * - 从“解析历史列表”跳转进入，替代原弹窗详情
 * - 支持复制链接直达
 * - 仅展示历史详情与已入库标签；候选标签必须手动点击生成
 */
 
import React, { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import apiService from '../../services/api'
import type { AIConfig, AnalysisResult, PromptTemplate, TagGroup } from './types'
import AnalysisDerivedTaggingPanel from './AnalysisDerivedTaggingPanel'
import VideoTagsSummary from './VideoTagsSummary'
 
const VideoAnalysisHistoryDetail: React.FC = () => {
  const navigate = useNavigate()
  const params = useParams()
  const analysisId = Number(params.analysisId)
 
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null)
  const [templates, setTemplates] = useState<PromptTemplate[]>([])
  const [aiConfigs, setAIConfigs] = useState<AIConfig[]>([])
  const [tagGroups, setTagGroups] = useState<TagGroup[]>([])
  const [videoTitle, setVideoTitle] = useState('')
 
  const canLoad = Number.isFinite(analysisId) && analysisId > 0
 
  const templateTitle = useMemo(() => {
    const templateId = (analysis as any)?.template_id
    if (!templateId) {
      return '未使用模板'
    }
    const template = templates.find((item) => item.id === templateId)
    return template?.title || '未使用模板'
  }, [analysis, templates])
 
  const loadAuxData = async () => {
    const [templateResp, groupResp, aiResp] = await Promise.all([
      apiService.get<PromptTemplate[]>('/video-analysis/templates'),
      apiService.get<TagGroup[]>('/video-analysis/tag-groups'),
      apiService.get<AIConfig[]>('/video-analysis/ai-configs'),
    ])
    setTemplates(templateResp.data || [])
    setTagGroups(groupResp.data || [])
    setAIConfigs(aiResp.data || [])
  }
 
  const loadDetail = async () => {
    if (!canLoad) {
      setError('无效的解析记录 ID')
      return
    }
    setLoading(true)
    setError(null)
    try {
      const resp = await apiService.get<AnalysisResult>(`/video-analysis/${analysisId}`)
      setAnalysis(resp.data as any)
      const videoFileId = (resp.data as any)?.video_file_id
      if (videoFileId) {
        try {
          const titleResp = await apiService.get<any>(`/video-analysis/videos/${videoFileId}`)
          setVideoTitle(String((titleResp.data as any)?.title || (titleResp.data as any)?.original_filename || '').trim())
        } catch {
          setVideoTitle('')
        }
      }
    } catch (err: any) {
      const detail = err?.response?.data?.detail
      const message = err?.response?.data?.message
      if (typeof detail === 'string' && detail.trim()) {
        setError(detail.trim())
      } else if (typeof message === 'string' && message.trim()) {
        setError(message.trim())
      } else {
        setError('加载解析详情失败')
      }
      setAnalysis(null)
    } finally {
      setLoading(false)
    }
  }
 
  useEffect(() => {
    loadAuxData().catch(() => {
      setTemplates([])
      setTagGroups([])
      setAIConfigs([])
    })
  }, [])
 
  useEffect(() => {
    loadDetail()
  }, [analysisId])
 
  const goBack = () => {
    navigate(-1)
  }
 
  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3 min-w-0">
          <button
            type="button"
            onClick={goBack}
            className="px-3 py-1.5 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors whitespace-nowrap"
          >
            返回列表
          </button>
          <h2 className="text-xl font-semibold text-gray-900 truncate">
            解析结果详情{canLoad ? ` #${analysisId}` : ''}
            {videoTitle ? ` - ${videoTitle}` : ''}
          </h2>
        </div>
        <button
          type="button"
          onClick={loadDetail}
          disabled={!canLoad || loading}
          className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-300 disabled:text-gray-500 disabled:cursor-not-allowed transition-colors whitespace-nowrap"
        >
          {loading ? '刷新中...' : '刷新'}
        </button>
      </div>
 
      {error && <div className="mb-4 text-sm text-red-600">{error}</div>}
      {loading && !analysis && <div className="text-sm text-gray-500">加载中...</div>}
 
      {analysis && (
        <div className="space-y-6">
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="text-sm text-gray-700 flex flex-wrap gap-x-6 gap-y-2">
              <div className="whitespace-nowrap">
                <span className="font-medium">模板:</span> {templateTitle}
              </div>
              <div className="whitespace-nowrap">
                <span className="font-medium">创建时间:</span> {new Date((analysis as any).created_at).toLocaleString()}
              </div>
              {(analysis as any).completed_at && (
                <div className="whitespace-nowrap">
                  <span className="font-medium">完成时间:</span> {new Date((analysis as any).completed_at).toLocaleString()}
                </div>
              )}
              {(analysis as any).processing_time !== undefined && (analysis as any).processing_time !== null && (
                <div className="whitespace-nowrap">
                  <span className="font-medium">处理时间:</span> {Number((analysis as any).processing_time).toFixed(1)}秒
                </div>
              )}
              {((analysis as any).api_provider || (analysis as any).model_name) && (
                <div className="whitespace-nowrap">
                  <span className="font-medium">模型:</span> {[(analysis as any).api_provider, (analysis as any).model_name].filter(Boolean).join('/')}
                </div>
              )}
              {(analysis as any).total_tokens !== undefined && (analysis as any).total_tokens !== null && (
                <div className="whitespace-nowrap">
                  <span className="font-medium">本次解析Tokens(估算):</span> {(analysis as any).total_tokens}
                  {(analysis as any).prompt_tokens !== undefined && (analysis as any).prompt_tokens !== null && (analysis as any).completion_tokens !== undefined && (analysis as any).completion_tokens !== null
                    ? ` (${(analysis as any).prompt_tokens}+${(analysis as any).completion_tokens})`
                    : ''}
                </div>
              )}
            </div>
          </div>
 
          <VideoTagsSummary videoFileId={(analysis as any).video_file_id} />
 
          <AnalysisDerivedTaggingPanel
            analysisId={analysisId}
            videoFileId={(analysis as any).video_file_id}
            aiConfigs={aiConfigs}
            tagGroups={tagGroups}
            defaultAIConfigId={(analysis as any)?.ai_config_id as any}
            defaultTagGroupIds={(analysis as any)?.tag_group_ids as any}
            showNotification={() => {}}
          />
 
          {(analysis as any).result_summary && (
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <h3 className="text-sm font-medium text-gray-800 mb-2">摘要</h3>
              <div className="text-sm text-gray-700 whitespace-pre-wrap">{(analysis as any).result_summary}</div>
            </div>
          )}
 
          {(analysis as any).analysis_result && (
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <h3 className="text-sm font-medium text-gray-800 mb-2">解析结果</h3>
              <div className="text-sm text-gray-700 whitespace-pre-wrap">{(analysis as any).analysis_result}</div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
 
export default VideoAnalysisHistoryDetail
