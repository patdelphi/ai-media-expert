/**
 * 视频解析页面类型定义
 *
 * 将页面内部类型抽离，降低主页面文件复杂度，便于后续继续拆分组件。
 */

export interface VideoFile {
  id: number
  original_filename: string
  saved_filename: string
  title?: string
  file_size: number
  duration?: number
  width?: number
  height?: number
  format_name?: string
  created_at: string
}

export interface PromptTemplate {
  id: number
  title: string
  content: string
  is_active: boolean
  usage_count: number
  created_at: string
  updated_at: string
}

export interface TagGroup {
  id: number
  name: string
  description?: string
  is_active: boolean
  tags: Array<{
    id: number
    name: string
    color?: string
    is_active: boolean
  }>
  created_at: string
  updated_at: string
}

export interface AIConfig {
  id: number
  name: string
  provider: string
  model: string
  max_tokens?: number
  temperature?: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface AnalysisResult {
  id: number
  video_file_id: number
  template_id?: number
  tag_group_ids?: number[]
  ai_config_id: number
  prompt_content: string
  status: string
  progress: number
  analysis_result?: string
  result_summary?: string
  confidence_score?: number
  processing_time?: number
  api_call_time?: string
  api_response_time?: string
  api_duration?: number
  prompt_tokens?: number
  completion_tokens?: number
  total_tokens?: number
  temperature?: number
  max_tokens?: number
  model_name?: string
  api_provider?: string
  request_id?: string
  debug_info?: Record<string, unknown>
  created_at: string
  completed_at?: string
  error_message?: string
}

export interface AnalysisHistoryItem {
  id: number
  video_file_id: number
  template_id?: number
  ai_config_id: number
  status: string
  progress: number
  result_summary?: string
  confidence_score?: number
  processing_time?: number
  created_at: string
  completed_at?: string
}

export interface StreamChunk {
  type: string
  content?: string
  progress?: number
  metadata?: Record<string, unknown>
  timestamp: string
}
