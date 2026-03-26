/**
 * 视频解析页面组件
 * 
 * 功能说明：
 * 1. 选择最近上传的视频进行解析
 * 2. 配置解析参数（模板、标签组、AI配置）
 * 3. 拼装和编辑提示词
 * 4. 实时显示解析进度和结果
 * 5. 查看历史记录和导出结果
 */

import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';

// 类型定义
interface VideoFile {
  id: number;
  original_filename: string;
  saved_filename: string;
  title?: string;
  file_size: number;
  duration?: number;
  width?: number;
  height?: number;
  format_name?: string;
  created_at: string;
}

interface PromptTemplate {
  id: number;
  title: string;
  content: string;
  is_active: boolean;
  usage_count: number;
  created_at: string;
  updated_at: string;
}

interface TagGroup {
  id: number;
  name: string;
  description?: string;
  is_active: boolean;
  tags: Array<{
    id: number;
    name: string;
    color?: string;
    is_active: boolean;
  }>;
  created_at: string;
  updated_at: string;
}

interface AIConfig {
  id: number;
  name: string;
  provider: string;
  model: string;
  max_tokens?: number;
  temperature?: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface AnalysisResult {
  id: number;
  video_file_id: number;
  template_id?: number;
  tag_group_ids?: number[];
  ai_config_id: number;
  prompt_content: string;
  status: string;
  progress: number;
  analysis_result?: string;
  result_summary?: string;
  confidence_score?: number;
  processing_time?: number;
  // AI API调试信息
  api_call_time?: string;
  api_response_time?: string;
  api_duration?: number;
  prompt_tokens?: number;
  completion_tokens?: number;
  total_tokens?: number;
  temperature?: number;
  max_tokens?: number;
  model_name?: string;
  api_provider?: string;
  request_id?: string;
  debug_info?: any;
  created_at: string;
  completed_at?: string;
}

interface AnalysisHistoryItem {
  id: number;
  video_file_id: number;
  template_id?: number;
  ai_config_id: number;
  status: string;
  progress: number;
  result_summary?: string;
  confidence_score?: number;
  processing_time?: number;
  created_at: string;
  completed_at?: string;
}

interface StreamChunk {
  type: string;
  content?: string;
  progress?: number;
  metadata?: any;
  timestamp: string;
}

const VideoAnalysis: React.FC = () => {
  // API基础URL配置
  const getApiBaseUrl = () => {
    return import.meta.env.DEV 
      ? 'http://localhost:8000' 
      : window.location.origin;
  };
  
  // 状态管理
  const [currentStep, setCurrentStep] = useState(1); // 当前步骤：1-选择视频，2-配置参数，3-确认提示词，4-解析中，5-查看结果
  const [selectedVideo, setSelectedVideo] = useState<VideoFile | null>(null);
  const [selectedTemplate, setSelectedTemplate] = useState<PromptTemplate | null>(null);
  const [selectedTagGroups, setSelectedTagGroups] = useState<number[]>([]);
  const [selectedAIConfig, setSelectedAIConfig] = useState<AIConfig | null>(null);
  const [customPrompt, setCustomPrompt] = useState('');
  const [finalPrompt, setFinalPrompt] = useState('');
  const [currentAnalysis, setCurrentAnalysis] = useState<AnalysisResult | null>(null);
  const [analysisHistory, setAnalysisHistory] = useState<AnalysisHistoryItem[]>([]);
  
  // 视频传输方式状态
  const [transmissionMethod, setTransmissionMethod] = useState<'url' | 'base64' | 'upload'>('url');
  
  // 数据状态
  const [videos, setVideos] = useState<VideoFile[]>([]);
  const [videoPage, setVideoPage] = useState(1);
  const [videoPageSize] = useState(12);
  const [videoTotal, setVideoTotal] = useState(0);
  const [videoPages, setVideoPages] = useState(1);
  const [templates, setTemplates] = useState<PromptTemplate[]>([]);
  const [tagGroups, setTagGroups] = useState<TagGroup[]>([]);
  const [aiConfigs, setAIConfigs] = useState<AIConfig[]>([]);
  const [historyPage, setHistoryPage] = useState(1);
  const [historyPageSize] = useState(10);
  const [historyTotal, setHistoryTotal] = useState(0);
  const [historyPages, setHistoryPages] = useState(1);
  
  // UI状态
  const [loading, setLoading] = useState(false);
  // const [error, setError] = useState<string | null>(null);
  const [notification, setNotification] = useState<{type: 'success' | 'error' | 'info', message: string} | null>(null);
  
  // 流式结果
  const [streamingResult, setStreamingResult] = useState('');
  const [streamingProgress, setStreamingProgress] = useState(0);
  const eventSourceRef = useRef<EventSource | null>(null);
  const pollingIntervalRef = useRef<number | null>(null);
  const pollingTimeoutRef = useRef<number | null>(null);
  
  // 调试信息
  const [currentDebugInfo, setCurrentDebugInfo] = useState<any>({});
  
  // 历史记录展示
  const [selectedHistoryItem, setSelectedHistoryItem] = useState<AnalysisResult | null>(null);
  const [selectedHistoryId, setSelectedHistoryId] = useState<number | null>(null);
  const [selectedHistoryVideoTitle, setSelectedHistoryVideoTitle] = useState('');
  const [showHistoryModal, setShowHistoryModal] = useState(false);
  const [historyDetailLoading, setHistoryDetailLoading] = useState(false);
  const [historyDetailError, setHistoryDetailError] = useState<string | null>(null);

  // 页面加载时获取数据
  useEffect(() => {
    loadInitialData();
  }, []);

  // 保存用户选择到本地存储
  const saveUserPreferences = () => {
    const preferences = {
      templateId: selectedTemplate?.id,
      tagGroupIds: selectedTagGroups,
      aiConfigId: selectedAIConfig?.id,
      transmissionMethod: transmissionMethod
    };
    localStorage.setItem('videoAnalysisPreferences', JSON.stringify(preferences));
  };

  // 从本地存储恢复用户选择
  const restoreUserPreferences = (templates: PromptTemplate[], tagGroups: TagGroup[], aiConfigs: AIConfig[]) => {
    try {
      const saved = localStorage.getItem('videoAnalysisPreferences');
      if (saved) {
        const preferences = JSON.parse(saved);
        
        // 恢复模板选择
        if (preferences.templateId) {
          const template = templates.find(t => t.id === preferences.templateId);
          if (template) {
            setSelectedTemplate(template);
          }
        }
        
        // 恢复标签组选择
        if (preferences.tagGroupIds && Array.isArray(preferences.tagGroupIds)) {
          const validTagGroupIds = preferences.tagGroupIds.filter((id: number) => 
            tagGroups.some(tg => tg.id === id)
          );
          setSelectedTagGroups(validTagGroupIds);
        }
        
        // 恢复AI配置选择
        if (preferences.aiConfigId) {
          const aiConfig = aiConfigs.find(ac => ac.id === preferences.aiConfigId);
          if (aiConfig) {
            setSelectedAIConfig(aiConfig);
          }
        }
        
        // 恢复传输方式选择
        if (preferences.transmissionMethod && ['url', 'base64', 'upload'].includes(preferences.transmissionMethod)) {
          setTransmissionMethod(preferences.transmissionMethod);
        }
      }
    } catch (error) {
      console.warn('Failed to restore user preferences:', error);
    }
  };

  // 监听选择变化并保存
  useEffect(() => {
    if (selectedTemplate || selectedTagGroups.length > 0 || selectedAIConfig || transmissionMethod !== 'url') {
      saveUserPreferences();
    }
  }, [selectedTemplate, selectedTagGroups, selectedAIConfig, transmissionMethod]);

  // 清除用户偏好设置
  const clearUserPreferences = () => {
    localStorage.removeItem('videoAnalysisPreferences');
    setSelectedTemplate(null);
    setSelectedTagGroups([]);
    setSelectedAIConfig(null);
    setTransmissionMethod('url'); // 重置为默认的URL方式
    showNotification('info', '已清除保存的选择偏好');
  };

  // 显示通知
  const showNotification = (type: 'success' | 'error' | 'info', message: string) => {
    setNotification({ type, message });
    setTimeout(() => setNotification(null), 5000);
  };

  const loadVideos = async (page: number = 1) => {
    try {
      const baseUrl = getApiBaseUrl();
      const response = await fetch(`${baseUrl}/api/v1/video-analysis/videos?page=${page}&size=${videoPageSize}`);
      if (!response.ok) return;
      const result = await response.json();
      const data = result.data;
      setVideos(data?.items || []);
      setVideoTotal(data?.total || 0);
      setVideoPage(data?.page || page);
      setVideoPages(data?.pages || 1);
    } catch (err) {
      console.error('Failed to load videos:', err);
    }
  };

  // 加载初始数据
  const loadInitialData = async () => {
    setLoading(true);
    try {
      // 并行加载所有数据
      const baseUrl = getApiBaseUrl();
      const [videosRes, templatesRes, tagGroupsRes, aiConfigsRes] = await Promise.all([
        fetch(`${baseUrl}/api/v1/video-analysis/videos?page=1&size=${videoPageSize}`),
        fetch(`${baseUrl}/api/v1/video-analysis/templates`),
        fetch(`${baseUrl}/api/v1/video-analysis/tag-groups`),
        fetch(`${baseUrl}/api/v1/video-analysis/ai-configs`)
      ]);

      let loadedTemplates: PromptTemplate[] = [];
      let loadedTagGroups: TagGroup[] = [];
      let loadedAIConfigs: AIConfig[] = [];

      if (videosRes.ok) {
        const videosData = await videosRes.json();
        const data = videosData.data;
        setVideos(data?.items || []);
        setVideoTotal(data?.total || 0);
        setVideoPage(data?.page || 1);
        setVideoPages(data?.pages || 1);
      }

      if (templatesRes.ok) {
        const templatesData = await templatesRes.json();
        loadedTemplates = templatesData.data || [];
        setTemplates(loadedTemplates);
      }

      if (tagGroupsRes.ok) {
        const tagGroupsData = await tagGroupsRes.json();
        loadedTagGroups = tagGroupsData.data || [];
        setTagGroups(loadedTagGroups);
      }

      if (aiConfigsRes.ok) {
        const aiConfigsData = await aiConfigsRes.json();
        loadedAIConfigs = aiConfigsData.data || [];
        setAIConfigs(loadedAIConfigs);
      }

      // 数据加载完成后恢复用户偏好设置
      restoreUserPreferences(loadedTemplates, loadedTagGroups, loadedAIConfigs);
      
      // 加载解析历史
      loadAnalysisHistory(1);

    } catch (err) {
      console.error('Failed to load initial data:', err);
      showNotification('error', '加载数据失败，请刷新页面重试');
    } finally {
      setLoading(false);
    }
  };

  // 格式化文件大小
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // 格式化时长
  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // 生成提示词
  const generatePrompt = () => {
    let prompt = '请按照如下模板进行视频解析，输出为markdown格式\n\n';
    
    // 添加模板内容
    if (selectedTemplate) {
      prompt += selectedTemplate.content;
    }
    
    // 添加标签信息
    if (selectedTagGroups.length > 0) {
      const selectedTags: string[] = [];
      tagGroups.forEach(group => {
        if (selectedTagGroups.includes(group.id)) {
          group.tags.forEach(tag => {
            if (tag.is_active) {
              selectedTags.push(tag.name);
            }
          });
        }
      });
      
      if (selectedTags.length > 0) {
        prompt += '\n\n输出相关标签，用逗号分开\n';
        prompt += selectedTags.join(', ');
      }
    }
    
    // 添加自定义内容
    if (customPrompt.trim()) {
      prompt += `\n\n${customPrompt.trim()}`;
    }
    
    setFinalPrompt(prompt);
  };

  // 监听配置变化，自动生成提示词
  useEffect(() => {
    if (selectedTemplate || selectedTagGroups.length > 0 || customPrompt) {
      generatePrompt();
    }
  }, [selectedTemplate, selectedTagGroups, customPrompt]);

  // 开始解析
  const startAnalysis = async () => {
    if (!selectedVideo || !selectedAIConfig || !finalPrompt.trim()) {
      showNotification('error', '请完成所有必要的配置');
      return;
    }

    setLoading(true);
    setCurrentStep(4);
    
    // 重置流式结果和进度
    setStreamingResult('');
    setStreamingProgress(0);
    // 保留调试信息，不清空currentDebugInfo
    
    try {
      const response = await fetch(`${getApiBaseUrl()}/api/v1/video-analysis/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          video_file_id: selectedVideo.id,
          template_id: selectedTemplate?.id,
          tag_group_ids: selectedTagGroups,
          custom_prompt: customPrompt,
          ai_config_id: selectedAIConfig.id,
          transmission_method: transmissionMethod
        })
      });

      if (!response.ok) {
        throw new Error('启动解析失败');
      }

      const result = await response.json();
      const analysisId = result.data.analysis_id;
      
      // 设置初始调试信息
      setCurrentDebugInfo({
        model_name: selectedAIConfig.model,
        api_provider: selectedAIConfig.provider,
        temperature: selectedAIConfig.temperature,
        max_tokens: selectedAIConfig.max_tokens,
        request_id: `req_${analysisId}_${Date.now()}`,
        api_call_time: new Date().toISOString()
      });
      
      // 开始流式接收结果
      startStreaming(analysisId);
      
      showNotification('success', '解析任务已启动');
      
    } catch (err) {
      console.error('Failed to start analysis:', err);
      showNotification('error', '启动解析失败，请重试');
      setCurrentStep(3);
    } finally {
      setLoading(false);
    }
  };

  // 开始流式接收结果
  const startStreaming = (analysisId: number, retryCount = 0) => {
    // 关闭之前的连接
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    // 使用完整的后端URL，避免代理问题
    const streamUrl = `${getApiBaseUrl()}/api/v1/video-analysis/${analysisId}/stream`;
    
    console.log(`Connecting to stream (attempt ${retryCount + 1}):`, streamUrl);
    
    // 先测试后端连通性
    fetch(`${getApiBaseUrl()}/health`)
      .then(response => {
        if (!response.ok) {
          throw new Error(`Backend health check failed: ${response.status}`);
        }
        console.log('Backend health check passed');
        
        // 后端正常，尝试建立EventSource连接
        let eventSource: EventSource;
        
        try {
          // 创建EventSource时添加配置选项
          eventSource = new EventSource(streamUrl, {
            withCredentials: false  // 跨域时不发送凭据
          });
          eventSourceRef.current = eventSource;

          const connectionTimeout = setTimeout(() => {
            if (eventSource.readyState === EventSource.CONNECTING) {
              console.error('EventSource connection timeout');
              eventSource.close();
              handleStreamDisconnected(analysisId, '连接超时');
            }
          }, 10000);
           
           // 设置事件处理器
           setupEventSourceHandlers(eventSource, analysisId, connectionTimeout as any);
           
         } catch (error) {
           console.error('Failed to create EventSource:', error);
           showNotification('error', '无法创建连接，请检查网络设置');
           return;
         }
      })
      .catch(healthError => {
        console.error('Backend health check failed:', healthError);
        showNotification('error', '后端服务不可用，请检查服务器状态');
        return;
       });
  };

  // EventSource消息处理函数
  const setupEventSourceHandlers = (eventSource: EventSource, analysisId: number, connectionTimeout: number) => {
    // 连接打开时的处理
    eventSource.onopen = (event) => {
      clearTimeout(connectionTimeout);
      console.log('EventSource connection opened:', event);
      showNotification('info', '已连接到服务器，开始接收数据');
    };
    
    eventSource.onmessage = (event) => {
      try {
        const data: StreamChunk = JSON.parse(event.data);
        
        switch (data.type) {
          case 'progress':
            setStreamingProgress(data.progress || 0);
            // 更新调试信息中的进度
            if (data.metadata) {
              setCurrentDebugInfo((prev: any) => ({
                ...prev,
                ...data.metadata
              }));
            }
            break;
          case 'content':
            // 累积流式内容，而不是替换
            setStreamingResult(prev => prev + (data.content || ''));
            break;
          case 'debug':
            // 实时更新调试信息
            if (data.metadata) {
              setCurrentDebugInfo((prev: any) => ({
                ...prev,
                ...data.metadata
              }));
            }
            break;
          case 'complete':
            setStreamingProgress(100);
            setCurrentStep(5);
            showNotification('success', '解析完成！');
            // 获取完整的解析结果包含调试信息
            fetchAnalysisResult(analysisId);
            loadAnalysisHistory(1);
            break;
          case 'timeout':
            handleStreamDisconnected(analysisId, '连接超时');
            break;
          case 'error':
            handleStreamDisconnected(analysisId, data.content || '连接中断');
            break;
        }
      } catch (err) {
        console.error('Failed to parse stream data:', err);
      }
    };

    eventSource.onerror = (error) => {
      console.error('EventSource failed:', error);
      console.error('EventSource readyState:', eventSource.readyState);
      console.error('EventSource URL:', `${getApiBaseUrl()}/api/v1/video-analysis/${analysisId}/stream`);
      
      // 清除连接超时定时器
      clearTimeout(connectionTimeout);
      eventSource.close();

      handleStreamDisconnected(analysisId, '连接中断');
    };
  };

  const fetchAnalysisData = async (analysisId: number): Promise<any | null> => {
    try {
      const response = await fetch(`${getApiBaseUrl()}/api/v1/video-analysis/${analysisId}`);
      if (!response.ok) return null;
      const result = await response.json();
      return result.data;
    } catch (err) {
      return null;
    }
  };

  const handleStreamDisconnected = async (analysisId: number, message: string) => {
    showNotification('info', `${message}，正在检查任务状态...`);

    const analysisData = await fetchAnalysisData(analysisId);
    if (!analysisData) {
      startPollingAnalysis(analysisId);
      return;
    }

    if (analysisData.status === 'completed') {
      setStreamingProgress(100);
      setCurrentStep(5);
      setCurrentAnalysis(analysisData);
      if (analysisData.analysis_result) {
        setStreamingResult(analysisData.analysis_result);
      }
      showNotification('success', '解析完成！');
      loadAnalysisHistory(1);
      return;
    }

    if (analysisData.status === 'failed') {
      showNotification('error', analysisData.error_message || '解析失败');
      setCurrentStep(3);
      return;
    }

    startPollingAnalysis(analysisId);
  };

  // 获取解析结果和调试信息
  const fetchAnalysisResult = async (analysisId: number) => {
    try {
      const response = await fetch(`${getApiBaseUrl()}/api/v1/video-analysis/${analysisId}`);
      if (response.ok) {
        const result = await response.json();
        const analysisData = result.data;
        
        // 更新当前分析结果
        setCurrentAnalysis(analysisData);
        
        // 更新调试信息，包含所有新增字段
        setCurrentDebugInfo({
          api_call_time: analysisData.api_call_time,
          api_response_time: analysisData.api_response_time,
          api_duration: analysisData.api_duration,
          prompt_tokens: analysisData.prompt_tokens,
          completion_tokens: analysisData.completion_tokens,
          total_tokens: analysisData.total_tokens,
          temperature: analysisData.temperature,
          max_tokens: analysisData.max_tokens,
          model_name: analysisData.model_name,
          api_provider: analysisData.api_provider,
          request_id: analysisData.request_id,
          debug_info: analysisData.debug_info,
          // 新增字段
          token_usage: analysisData.token_usage,
          cost_estimate: analysisData.cost_estimate,
          processing_time: analysisData.processing_time,
          confidence_score: analysisData.confidence_score,
          started_at: analysisData.started_at,
          completed_at: analysisData.completed_at,
          transmission_method: analysisData.transmission_method
        });
        
        // 确保分析完成后流式结果与最终结果一致
        if (analysisData.analysis_result && analysisData.status === 'completed') {
          setStreamingResult(analysisData.analysis_result);
        }
      }
    } catch (err) {
      console.error('Failed to fetch analysis result:', err);
    }
  };

  // 加载解析历史
  const loadAnalysisHistory = async (page: number = 1) => {
    try {
      const response = await fetch(`${getApiBaseUrl()}/api/v1/video-analysis/?page=${page}&size=${historyPageSize}`);
      if (response.ok) {
        const result = await response.json();
        const data = result.data;
        setAnalysisHistory(data?.items || []);
        setHistoryTotal(data?.total || 0);
        setHistoryPage(data?.page || page);
        setHistoryPages(data?.pages || 1);
      }
    } catch (err) {
      console.error('Failed to load analysis history:', err);
    }
  };

  const loadHistoryDetail = async (analysisId: number) => {
    setHistoryDetailLoading(true);
    setHistoryDetailError(null);
    setSelectedHistoryItem(null);
    setSelectedHistoryVideoTitle('');
    try {
      const response = await fetch(`${getApiBaseUrl()}/api/v1/video-analysis/${analysisId}`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const result = await response.json();
      const analysisData = result.data;
      setSelectedHistoryItem(analysisData);

      if (analysisData?.video_file_id) {
        const title = await fetchVideoTitle(analysisData.video_file_id);
        if (title) {
          setSelectedHistoryVideoTitle(title);
        }
      }
    } catch (err: any) {
      console.error('Failed to load analysis detail:', err);
      setHistoryDetailError('加载解析结果详情失败，请重试');
    } finally {
      setHistoryDetailLoading(false);
    }
  };

  const fetchVideoTitle = async (videoFileId: number): Promise<string | null> => {
    try {
      const response = await fetch(`${getApiBaseUrl()}/api/v1/video-analysis/videos/${videoFileId}`);
      if (!response.ok) return null;
      const result = await response.json();
      const data = result.data;
      return data?.title || data?.original_filename || null;
    } catch {
      return null;
    }
  };

  const formatExportTimestamp = (dateInput?: string | Date) => {
    const d = dateInput ? new Date(dateInput) : new Date();
    const pad = (n: number) => String(n).padStart(2, '0');
    const yy = pad(d.getFullYear() % 100);
    const mm = pad(d.getMonth() + 1);
    const dd = pad(d.getDate());
    const hh = pad(d.getHours());
    const mi = pad(d.getMinutes());
    const ss = pad(d.getSeconds());
    return `${yy}${mm}${dd}${hh}${mi}${ss}`;
  };

  const sanitizeFilename = (name: string) => {
    return name.replace(/[\\\/:*?"<>|]/g, '_').trim();
  };

  const stripExtension = (name: string) => {
    return name.replace(/\.[^/.]+$/, '');
  };

  const buildExportFilename = (videoTitle: string, completedAt?: string | Date) => {
    const safeTitle = sanitizeFilename(stripExtension(videoTitle || '视频标题'));
    return `${safeTitle} - 解析结果 - ${formatExportTimestamp(completedAt)}.md`;
  };

  const exportHistoryResult = async (analysisId: number) => {
    try {
      const response = await fetch(`${getApiBaseUrl()}/api/v1/video-analysis/${analysisId}`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const result = await response.json();
      const analysisData = result.data;
      if (analysisData?.analysis_result) {
        const title = (analysisData.video_file_id && await fetchVideoTitle(analysisData.video_file_id)) || `analysis-${analysisId}`;
        exportResult(analysisData.analysis_result, buildExportFilename(title, analysisData.completed_at || analysisData.created_at));
      } else {
        showNotification('info', '该记录暂无可导出的解析结果');
      }
    } catch (err) {
      console.error('Failed to export analysis result:', err);
      showNotification('error', '导出失败，请稍后重试');
    }
  };

  // 导出结果为MD文件
  const exportResult = (result: string, filename: string) => {
    const blob = new Blob([result], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };
  
  // 查看历史记录详情
  const viewHistoryDetails = async (analysis: AnalysisHistoryItem) => {
    setShowHistoryModal(true);
    setSelectedHistoryId(analysis.id);
    await loadHistoryDetail(analysis.id);
  };
  
  // 关闭历史记录模态框
  const closeHistoryModal = () => {
    setShowHistoryModal(false);
    setSelectedHistoryItem(null);
    setSelectedHistoryId(null);
    setHistoryDetailLoading(false);
    setHistoryDetailError(null);
  };

  // 重置到第一步
  const resetToStart = () => {
    setCurrentStep(1);
    setSelectedVideo(null);
    setSelectedTemplate(null);
    setSelectedTagGroups([]);
    setSelectedAIConfig(null);
    setCustomPrompt('');
    setFinalPrompt('');
    setCurrentAnalysis(null);
    setStreamingResult('');
    setStreamingProgress(0);
    
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }
  };

  // 轮询模式作为EventSource的备用方案
  const startPollingAnalysis = (analysisId: number) => {
    console.log('Starting polling mode for analysis:', analysisId);
    showNotification('info', '切换到轮询模式，继续监控分析进度');

    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
    if (pollingTimeoutRef.current) {
      clearTimeout(pollingTimeoutRef.current);
      pollingTimeoutRef.current = null;
    }
    
    const pollInterval = window.setInterval(async () => {
      try {
        const response = await fetch(`${getApiBaseUrl()}/api/v1/video-analysis/${analysisId}`);
        if (response.ok) {
          const result = await response.json();
          const analysisData = result.data;
          
          // 更新进度
          setStreamingProgress(analysisData.progress || 0);
          
          // 更新调试信息
          setCurrentDebugInfo({
            api_call_time: analysisData.api_call_time,
            api_response_time: analysisData.api_response_time,
            api_duration: analysisData.api_duration,
            prompt_tokens: analysisData.prompt_tokens,
            completion_tokens: analysisData.completion_tokens,
            total_tokens: analysisData.total_tokens,
            temperature: analysisData.temperature,
            max_tokens: analysisData.max_tokens,
            model_name: analysisData.model_name,
            api_provider: analysisData.api_provider,
            request_id: analysisData.request_id,
            debug_info: analysisData.debug_info,
            token_usage: analysisData.token_usage,
            cost_estimate: analysisData.cost_estimate,
            processing_time: analysisData.processing_time,
            confidence_score: analysisData.confidence_score,
            started_at: analysisData.started_at,
            completed_at: analysisData.completed_at,
            transmission_method: analysisData.transmission_method
          });
          
          // 更新分析结果
          if (analysisData.analysis_result) {
            setStreamingResult(analysisData.analysis_result);
          }
          
          // 检查是否完成
          if (analysisData.status === 'completed') {
            clearInterval(pollInterval);
            pollingIntervalRef.current = null;
            if (pollingTimeoutRef.current) {
              clearTimeout(pollingTimeoutRef.current);
              pollingTimeoutRef.current = null;
            }
            setStreamingProgress(100);
            setCurrentStep(5);
            showNotification('success', '解析完成！');
            setCurrentAnalysis(analysisData);
            loadAnalysisHistory(1);
          } else if (analysisData.status === 'failed') {
            clearInterval(pollInterval);
            pollingIntervalRef.current = null;
            if (pollingTimeoutRef.current) {
              clearTimeout(pollingTimeoutRef.current);
              pollingTimeoutRef.current = null;
            }
            showNotification('error', analysisData.error_message || '解析失败');
            setCurrentStep(3);
          }
        }
      } catch (error) {
        console.error('Polling error:', error);
        // 继续轮询，不中断
      }
    }, 3000); // 每3秒轮询一次

    pollingIntervalRef.current = pollInterval;
    const scheduleTimeoutCheck = () => {
      pollingTimeoutRef.current = window.setTimeout(async () => {
        const analysisData = await fetchAnalysisData(analysisId);
        if (analysisData?.status === 'completed') {
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
          }
          if (pollingTimeoutRef.current) {
            clearTimeout(pollingTimeoutRef.current);
            pollingTimeoutRef.current = null;
          }
          setStreamingProgress(100);
          setCurrentStep(5);
          setCurrentAnalysis(analysisData);
          if (analysisData.analysis_result) {
            setStreamingResult(analysisData.analysis_result);
          }
          showNotification('success', '解析完成！');
          loadAnalysisHistory(1);
          return;
        }

        if (analysisData?.status === 'failed') {
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
          }
          if (pollingTimeoutRef.current) {
            clearTimeout(pollingTimeoutRef.current);
            pollingTimeoutRef.current = null;
          }
          showNotification('error', analysisData.error_message || '解析失败');
          setCurrentStep(3);
          return;
        }

        showNotification('info', '解析耗时较长，继续监控中...');
        scheduleTimeoutCheck();
      }, 300000);
    };

    scheduleTimeoutCheck();
  };

  // 组件卸载时清理
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
      if (pollingTimeoutRef.current) {
        clearTimeout(pollingTimeoutRef.current);
        pollingTimeoutRef.current = null;
      }
    };
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* 通知栏 */}
        {notification && (
          <div className={`fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg max-w-md ${
            notification.type === 'success' ? 'bg-green-100 border border-green-400 text-green-700' :
            notification.type === 'error' ? 'bg-red-100 border border-red-400 text-red-700' :
            'bg-blue-100 border border-blue-400 text-blue-700'
          }`}>
            <div className="flex items-center">
              <i className={`fas ${
                notification.type === 'success' ? 'fa-check-circle' :
                notification.type === 'error' ? 'fa-exclamation-circle' :
                'fa-info-circle'
              } mr-2`}></i>
              <span className="text-sm">{notification.message}</span>
              <button 
                onClick={() => setNotification(null)}
                className="ml-auto text-gray-500 hover:text-gray-700"
              >
                <i className="fas fa-times"></i>
              </button>
            </div>
          </div>
        )}

        {/* 页面标题 */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">视频解析</h1>
          <p className="mt-2 text-gray-600">使用AI技术智能分析视频内容</p>
        </div>

        {/* 步骤指示器 */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            {[
              { step: 1, title: '选择视频', icon: 'fa-video' },
              { step: 2, title: '配置参数', icon: 'fa-cog' },
              { step: 3, title: '确认提示词', icon: 'fa-edit' },
              { step: 4, title: '解析中', icon: 'fa-spinner' },
              { step: 5, title: '查看结果', icon: 'fa-chart-line' }
            ].map((item, index) => (
              <div key={item.step} className="flex items-center">
                <div className={`flex items-center justify-center w-10 h-10 rounded-full ${
                  currentStep >= item.step ? 'bg-blue-600 text-white' : 'bg-gray-300 text-gray-600'
                }`}>
                  <i className={`fas ${item.icon} ${item.step === 4 && currentStep === 4 ? 'fa-spin' : ''}`}></i>
                </div>
                <span className={`ml-2 text-sm font-medium ${
                  currentStep >= item.step ? 'text-blue-600' : 'text-gray-500'
                }`}>
                  {item.title}
                </span>
                {index < 4 && (
                  <div className={`flex-1 h-0.5 mx-4 ${
                    currentStep > item.step ? 'bg-blue-600' : 'bg-gray-300'
                  }`}></div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* 主要内容区域 */}
        <div className="bg-white rounded-lg shadow-sm">
          {/* 步骤1：选择视频 */}
          {currentStep === 1 && (
            <div className="p-6">
              <h2 className="text-xl font-semibold mb-4">选择要解析的视频</h2>
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <i className="fas fa-spinner fa-spin text-2xl text-blue-600 mr-3"></i>
                  <span className="text-gray-600">加载视频列表...</span>
                </div>
              ) : videos.length === 0 ? (
                <div className="text-center py-12">
                  <i className="fas fa-video text-4xl text-gray-500 mb-4"></i>
                  <p className="text-gray-600">暂无可用视频</p>
                  <p className="text-sm text-gray-500 mt-2">请先上传视频文件</p>
                </div>
              ) : (
                <div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                    {videos.map((video) => (
                      <div
                        key={video.id}
                        className={`border rounded-lg p-4 cursor-pointer transition-all ${
                          selectedVideo?.id === video.id
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                        onClick={() => setSelectedVideo(video)}
                      >
                        <div className="flex items-center mb-3">
                          <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mr-3">
                            <i className="fas fa-video text-blue-600 text-lg"></i>
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-gray-900 truncate">
                              {video.title || video.original_filename}
                            </p>
                            <p className="text-xs text-gray-500">
                              {formatFileSize(video.file_size)}
                            </p>
                          </div>
                        </div>
                        <div className="text-xs text-gray-600 space-y-1">
                          {video.duration && (
                            <div>时长: {formatDuration(video.duration)}</div>
                          )}
                          {video.width && video.height && (
                            <div>分辨率: {video.width}×{video.height}</div>
                          )}
                          {video.format_name && (
                            <div>格式: {video.format_name.toUpperCase()}</div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>

                  {videoPages > 1 && (
                    <div className="mt-4 flex items-center justify-between">
                      <div className="text-sm text-gray-500">
                        共 {videoTotal} 条，第 {videoPage}/{videoPages} 页
                      </div>
                      <div className="flex space-x-2">
                        <button
                          onClick={() => loadVideos(videoPage - 1)}
                          disabled={videoPage <= 1}
                          className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 disabled:bg-gray-100 disabled:text-gray-400 disabled:cursor-not-allowed transition-colors"
                        >
                          上一页
                        </button>
                        <button
                          onClick={() => loadVideos(videoPage + 1)}
                          disabled={videoPage >= videoPages}
                          className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 disabled:bg-gray-100 disabled:text-gray-400 disabled:cursor-not-allowed transition-colors"
                        >
                          下一页
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}
              
              {selectedVideo && (
                <div className="mt-6 flex justify-end">
                  <button
                    onClick={() => setCurrentStep(2)}
                    className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    下一步
                  </button>
                </div>
              )}
              
              {/* 解析历史 */}
              {analysisHistory.length > 0 && (
                <div className="mt-8 border-t pt-6">
                  <h3 className="text-lg font-semibold mb-4">解析历史</h3>
                  <div className="space-y-3">
                    {analysisHistory.map((analysis) => (
                      <div key={analysis.id} className="border rounded-lg p-4 hover:bg-gray-50 transition-colors">
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <div className="flex items-center space-x-3 mb-2">
                              <span className="font-medium text-gray-900">
                                视频ID: {analysis.video_file_id}
                              </span>
                              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                analysis.status === 'completed' ? 'bg-green-100 text-green-800' :
                                analysis.status === 'failed' ? 'bg-red-100 text-red-800' :
                                analysis.status === 'processing' ? 'bg-blue-100 text-blue-800' :
                                'bg-gray-100 text-gray-800'
                              }`}>
                                {analysis.status === 'completed' ? '已完成' :
                                 analysis.status === 'failed' ? '失败' :
                                 analysis.status === 'processing' ? '处理中' : '等待中'}
                              </span>
                            </div>
                            {analysis.result_summary && (
                              <p className="text-sm text-gray-600 mb-2">{analysis.result_summary}</p>
                            )}
                            <div className="flex items-center space-x-4 text-xs text-gray-500">
                              <span>创建时间: {new Date(analysis.created_at).toLocaleString()}</span>
                              {analysis.processing_time && (
                                <span>处理时间: {analysis.processing_time.toFixed(1)}秒</span>
                              )}
                              {analysis.confidence_score && (
                                <span>置信度: {(analysis.confidence_score * 100).toFixed(1)}%</span>
                              )}
                            </div>
                          </div>
                          <div className="flex space-x-2">
                            <button
                              onClick={() => viewHistoryDetails(analysis)}
                              className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors"
                            >
                              <i className="fas fa-eye mr-1"></i>
                              查看
                            </button>
                            {analysis.status === 'completed' && (
                              <button
                                onClick={() => exportHistoryResult(analysis.id)}
                                className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
                              >
                                <i className="fas fa-download mr-1"></i>
                                导出
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>

                  {historyPages > 1 && (
                    <div className="mt-4 flex items-center justify-between">
                      <div className="text-sm text-gray-500">
                        共 {historyTotal} 条，第 {historyPage}/{historyPages} 页
                      </div>
                      <div className="flex space-x-2">
                        <button
                          onClick={() => loadAnalysisHistory(historyPage - 1)}
                          disabled={historyPage <= 1}
                          className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 disabled:bg-gray-100 disabled:text-gray-400 disabled:cursor-not-allowed transition-colors"
                        >
                          上一页
                        </button>
                        <button
                          onClick={() => loadAnalysisHistory(historyPage + 1)}
                          disabled={historyPage >= historyPages}
                          className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 disabled:bg-gray-100 disabled:text-gray-400 disabled:cursor-not-allowed transition-colors"
                        >
                          下一页
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* 步骤2：配置参数 */}
          {currentStep === 2 && (
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold">配置解析参数</h2>
                <div className="text-sm text-gray-500 flex items-center">
                  <i className="fas fa-save mr-2"></i>
                  系统会自动保存您的选择偏好
                </div>
              </div>
              
              <div className="space-y-6">
                {/* 选择模板 */}
                <div>
                  <h3 className="text-lg font-medium mb-3">选择提示词模板</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {templates.map((template) => (
                      <div
                        key={template.id}
                        className={`border rounded-lg p-4 cursor-pointer transition-all ${
                          selectedTemplate?.id === template.id
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                        onClick={() => setSelectedTemplate(template)}
                      >
                        <div className="flex items-start justify-between mb-2">
                          <h4 className="font-medium text-gray-900">{template.title}</h4>
                          <span className="text-xs text-gray-500">使用 {template.usage_count} 次</span>
                        </div>
                        <p className="text-sm text-gray-600 line-clamp-3">
                          {template.content.substring(0, 100)}...
                        </p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* 选择标签组 */}
                <div>
                  <h3 className="text-lg font-medium mb-3">选择标签组</h3>
                  <div className="space-y-3">
                    {tagGroups.map((group) => (
                      <div key={group.id} className="border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-3">
                          <div>
                            <h4 className="font-medium text-gray-900">{group.name}</h4>
                            {group.description && (
                              <p className="text-sm text-gray-600">{group.description}</p>
                            )}
                          </div>
                          <label className="flex items-center">
                            <input
                              type="checkbox"
                              checked={selectedTagGroups.includes(group.id)}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setSelectedTagGroups([...selectedTagGroups, group.id]);
                                } else {
                                  setSelectedTagGroups(selectedTagGroups.filter(id => id !== group.id));
                                }
                              }}
                              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                            />
                            <span className="ml-2 text-sm text-gray-700">选择</span>
                          </label>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {group.tags.map((tag) => (
                            <span
                              key={tag.id}
                              className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                              style={{
                                backgroundColor: tag.color ? `${tag.color}20` : '#f3f4f6',
                                color: tag.color || '#6b7280'
                              }}
                            >
                              {tag.name}
                            </span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* 选择AI配置 */}
                <div>
                  <h3 className="text-lg font-medium mb-3">选择AI配置</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {aiConfigs.map((config) => (
                      <div
                        key={config.id}
                        className={`border rounded-lg p-4 cursor-pointer transition-all ${
                          selectedAIConfig?.id === config.id
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                        onClick={() => setSelectedAIConfig(config)}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-medium text-gray-900">{config.name}</h4>
                          <span className="text-xs text-gray-500">{config.provider}</span>
                        </div>
                        <div className="text-sm text-gray-600 space-y-1">
                          <div>模型: {config.model}</div>
                          {config.max_tokens && (
                            <div>最大Token: {config.max_tokens}</div>
                          )}
                          {config.temperature && (
                            <div>温度: {config.temperature}</div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* 视频传输方式选择 */}
                <div>
                  <h3 className="text-lg font-medium mb-3">视频传输方式</h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {/* URL方式 */}
                    <div
                      className={`border rounded-lg p-4 cursor-pointer transition-all ${
                        transmissionMethod === 'url'
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                      onClick={() => setTransmissionMethod('url')}
                    >
                      <div className="flex items-center mb-2">
                        <i className="fas fa-link text-blue-600 mr-2"></i>
                        <h4 className="font-medium text-gray-900">URL方式</h4>
                        <span className="ml-auto text-xs bg-green-100 text-green-800 px-2 py-1 rounded">推荐</span>
                      </div>
                      <div className="text-sm text-gray-600 space-y-1">
                        <div>• 通过公网URL访问视频</div>
                        <div>• 适合所有文件大小</div>
                        <div>• 传输速度快</div>
                      </div>
                    </div>

                    {/* Base64编码方式 */}
                    <div
                      className={`border rounded-lg p-4 cursor-pointer transition-all ${
                        transmissionMethod === 'base64'
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                      onClick={() => setTransmissionMethod('base64')}
                    >
                      <div className="flex items-center mb-2">
                        <i className="fas fa-code text-orange-600 mr-2"></i>
                        <h4 className="font-medium text-gray-900">Base64编码</h4>
                      </div>
                      <div className="text-sm text-gray-600 space-y-1">
                        <div>• 直接编码视频数据</div>
                        <div>• 适合小文件（&lt;10MB）</div>
                        <div>• 无需公网访问</div>
                      </div>
                    </div>

                    {/* 文件上传方式 */}
                    <div
                      className={`border rounded-lg p-4 cursor-pointer transition-all ${
                        transmissionMethod === 'upload'
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                      onClick={() => setTransmissionMethod('upload')}
                    >
                      <div className="flex items-center mb-2">
                        <i className="fas fa-upload text-purple-600 mr-2"></i>
                        <h4 className="font-medium text-gray-900">文件上传</h4>
                        <span className="ml-auto text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">开发中</span>
                      </div>
                      <div className="text-sm text-gray-600 space-y-1">
                        <div>• 上传到AI服务商</div>
                        <div>• 支持大文件</div>
                        <div>• 可重复使用</div>
                      </div>
                    </div>
                  </div>
                  
                  {/* 传输方式说明 */}
                  <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                    <div className="text-sm text-gray-600">
                      {transmissionMethod === 'url' && (
                        <div className="flex items-start">
                          <i className="fas fa-info-circle text-blue-500 mr-2 mt-0.5"></i>
                          <div>
                            <strong>URL方式：</strong>通过公网URL让AI直接访问视频文件。需要确保网络连接稳定，适合所有文件大小。
                          </div>
                        </div>
                      )}
                      {transmissionMethod === 'base64' && (
                        <div className="flex items-start">
                          <i className="fas fa-info-circle text-orange-500 mr-2 mt-0.5"></i>
                          <div>
                            <strong>Base64编码：</strong>将视频文件编码后直接发送给AI。适合小文件，会自动压缩大文件。无需公网访问。
                          </div>
                        </div>
                      )}
                      {transmissionMethod === 'upload' && (
                        <div className="flex items-start">
                          <i className="fas fa-info-circle text-purple-500 mr-2 mt-0.5"></i>
                          <div>
                            <strong>文件上传：</strong>先上传视频到AI服务商的存储服务，然后引用文件ID进行分析。支持大文件且可重复使用。
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* 自定义提示词 */}
                <div>
                  <h3 className="text-lg font-medium mb-3">自定义提示词（可选）</h3>
                  <textarea
                    value={customPrompt}
                    onChange={(e) => setCustomPrompt(e.target.value)}
                    placeholder="在此添加自定义的分析要求..."
                    className="w-full h-32 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>

              <div className="mt-6 flex justify-between items-center">
                <button
                  onClick={() => setCurrentStep(1)}
                  className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  上一步
                </button>
                
                <div className="flex items-center space-x-3">
                  <button
                    onClick={clearUserPreferences}
                    className="px-4 py-2 text-sm border border-gray-300 text-gray-600 rounded-lg hover:bg-gray-50 transition-colors flex items-center"
                    title="清除保存的选择偏好"
                  >
                    <i className="fas fa-eraser mr-2"></i>
                    清除偏好
                  </button>
                  
                  <button
                    onClick={() => setCurrentStep(3)}
                    disabled={!selectedTemplate && !customPrompt}
                    className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:text-gray-500 disabled:cursor-not-allowed transition-colors"
                  >
                    下一步
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* 步骤3：确认提示词 */}
          {currentStep === 3 && (
            <div className="p-6">
              <h2 className="text-xl font-semibold mb-6">确认提示词</h2>
              
              <div className="space-y-6">
                {/* 配置摘要 */}
                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="font-medium text-gray-900 mb-3">配置摘要</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-600">视频:</span>
                      <span className="ml-2 font-medium">{selectedVideo?.original_filename}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">模板:</span>
                      <span className="ml-2 font-medium">{selectedTemplate?.title || '无'}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">标签组:</span>
                      <span className="ml-2 font-medium">
                        {selectedTagGroups.length > 0 
                          ? tagGroups.filter(g => selectedTagGroups.includes(g.id)).map(g => g.name).join(', ')
                          : '无'
                        }
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-600">AI配置:</span>
                      <span className="ml-2 font-medium">{selectedAIConfig?.name}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">传输方式:</span>
                      <span className="ml-2 font-medium">
                        {transmissionMethod === 'url' && '🔗 URL方式'}
                        {transmissionMethod === 'base64' && '📝 Base64编码'}
                        {transmissionMethod === 'upload' && '📤 文件上传'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* 最终提示词 */}
                <div>
                  <h3 className="font-medium text-gray-900 mb-3">最终提示词</h3>
                  <textarea
                    value={finalPrompt}
                    onChange={(e) => setFinalPrompt(e.target.value)}
                    className="w-full h-64 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
                    placeholder="提示词将在此显示..."
                  />
                  <p className="text-xs text-gray-500 mt-2">
                    您可以直接编辑上述提示词内容
                  </p>
                </div>
              </div>

              <div className="mt-6 flex justify-between">
                <button
                  onClick={() => setCurrentStep(2)}
                  className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  上一步
                </button>
                <button
                  onClick={startAnalysis}
                  disabled={!finalPrompt.trim() || !selectedAIConfig || loading}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:text-gray-500 disabled:cursor-not-allowed transition-colors"
                >
                  {loading ? (
                    <>
                      <i className="fas fa-spinner fa-spin mr-2"></i>
                      启动中...
                    </>
                  ) : (
                    '开始解析'
                  )}
                </button>
              </div>
            </div>
          )}

          {/* 步骤4：解析中 */}
          {currentStep === 4 && (
            <div className="p-6">
              <h2 className="text-xl font-semibold mb-6">正在解析视频</h2>
              
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* 左侧：进度和结果 */}
                <div className="lg:col-span-2 space-y-6">
                  {/* 进度条 */}
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium text-gray-700">解析进度</span>
                      <span className="text-sm text-gray-500">{streamingProgress}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${streamingProgress}%` }}
                      ></div>
                    </div>
                  </div>

                  {/* 实时结果 */}
                  {streamingResult && (
                    <div>
                      <div className="flex justify-between items-center mb-3">
                        <h3 className="font-medium text-gray-900">解析结果</h3>
                        <div className="flex items-center text-sm text-gray-500">
                          <div className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></div>
                          <span>实时更新中</span>
                        </div>
                      </div>
                      <div className="border rounded-lg p-4 bg-gray-50 max-h-96 overflow-y-auto">
                        <div className="prose prose-sm max-w-none">
                          <ReactMarkdown 
                            components={{
                              // 自定义渲染组件以优化显示效果
                              h1: ({children}) => <h1 className="text-xl font-bold mb-3 text-gray-900">{children}</h1>,
                              h2: ({children}) => <h2 className="text-lg font-semibold mb-2 text-gray-800">{children}</h2>,
                              h3: ({children}) => <h3 className="text-md font-medium mb-2 text-gray-700">{children}</h3>,
                              p: ({children}) => <p className="mb-2 text-gray-600 leading-relaxed">{children}</p>,
                              ul: ({children}) => <ul className="list-disc list-inside mb-2 text-gray-600">{children}</ul>,
                              ol: ({children}) => <ol className="list-decimal list-inside mb-2 text-gray-600">{children}</ol>,
                              li: ({children}) => <li className="mb-1">{children}</li>,
                              strong: ({children}) => <strong className="font-semibold text-gray-800">{children}</strong>,
                              code: ({children}) => <code className="bg-gray-200 px-1 py-0.5 rounded text-sm font-mono">{children}</code>,
                              blockquote: ({children}) => <blockquote className="border-l-4 border-blue-500 pl-4 italic text-gray-600 mb-2">{children}</blockquote>
                            }}
                          >
                            {streamingResult}
                          </ReactMarkdown>
                        </div>
                        {/* 流式输入指示器 */}
                        <div className="flex items-center mt-2 text-xs text-gray-500">
                          <div className="w-1 h-4 bg-blue-500 animate-pulse mr-1"></div>
                          <span>正在生成内容...</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* 右侧：AI API调试信息 */}
                <div className="lg:col-span-1">
                  <div className="bg-white border border-gray-200 text-gray-800 rounded-lg overflow-hidden shadow-sm">
                    <div className="px-4 py-3 bg-gray-50 border-b border-gray-200">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center">
                          <i className="fas fa-bug text-gray-500 mr-2"></i>
                          <span className="font-medium text-gray-900">AI API 调试信息</span>
                        </div>
                        {/* API状态指示器 */}
                        <div className="flex items-center">
                          {currentDebugInfo.api_call_time && !currentDebugInfo.api_response_time ? (
                            <div className="flex items-center text-yellow-600">
                              <i className="fas fa-spinner fa-spin mr-1"></i>
                              <span className="text-xs font-medium">调用中</span>
                            </div>
                          ) : currentDebugInfo.api_response_time ? (
                            <div className="flex items-center text-green-600">
                              <i className="fas fa-check-circle mr-1"></i>
                              <span className="text-xs font-medium">成功</span>
                            </div>
                          ) : (
                            <div className="flex items-center text-gray-500">
                              <i className="fas fa-clock mr-1"></i>
                              <span className="text-xs font-medium">等待中</span>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="p-4 space-y-4 max-h-96 overflow-y-auto">
                      {/* 基本信息 */}
                      <div>
                        <h4 className="text-sm font-medium text-gray-700 mb-2">基本信息</h4>
                        <div className="space-y-1 text-xs">
                          <div className="flex justify-between">
                            <span className="text-gray-500">模型:</span>
                            <span className="text-gray-900">{currentDebugInfo.model_name || 'N/A'}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-500">提供商:</span>
                            <span className="text-gray-900">{currentDebugInfo.api_provider || 'N/A'}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-500">请求ID:</span>
                            <span className="text-gray-900 text-xs truncate">{currentDebugInfo.request_id || 'N/A'}</span>
                          </div>
                        </div>
                      </div>

                      {/* 时间信息 */}
                      <div>
                        <h4 className="text-sm font-medium text-gray-700 mb-2">时间信息</h4>
                        <div className="space-y-1 text-xs">
                          <div className="flex justify-between">
                            <span className="text-gray-500">调用时间:</span>
                            <span className="text-gray-900">
                              {currentDebugInfo.api_call_time ? new Date(currentDebugInfo.api_call_time).toLocaleTimeString() : 'N/A'}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-500">耗时:</span>
                            <span className={`${currentDebugInfo.api_duration && currentDebugInfo.api_duration > 10 ? 'text-red-500' : 'text-green-600'}`}>
                              {currentDebugInfo.api_duration ? `${currentDebugInfo.api_duration.toFixed(3)}秒` : 'N/A'}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Token使用情况 */}
                      <div>
                        <h4 className="text-sm font-medium text-gray-700 mb-2">Token 使用</h4>
                        <div className="space-y-1 text-xs">
                          <div className="flex justify-between">
                            <span className="text-gray-500">输入:</span>
                            <span className="text-blue-600">{currentDebugInfo.prompt_tokens || 0}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-500">输出:</span>
                            <span className="text-green-600">{currentDebugInfo.completion_tokens || 0}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-500">总计:</span>
                            <span className="text-purple-600">{currentDebugInfo.total_tokens || 0}</span>
                          </div>
                          {/* 成本估算 */}
                          {currentDebugInfo.token_usage?.estimated_cost && (
                            <div className="flex justify-between">
                              <span className="text-gray-500">预估成本:</span>
                              <span className="text-yellow-600">${currentDebugInfo.token_usage.estimated_cost.toFixed(4)}</span>
                            </div>
                          )}
                        </div>
                        
                        {/* Token使用可视化 */}
                        {currentDebugInfo.total_tokens && currentDebugInfo.total_tokens > 0 && (
                          <div className="mt-2">
                            <div className="flex h-1 bg-gray-200 rounded overflow-hidden">
                              <div 
                                className="bg-blue-500"
                                style={{
                                  width: `${((currentDebugInfo.prompt_tokens || 0) / currentDebugInfo.total_tokens) * 100}%`
                                }}
                              ></div>
                              <div 
                                className="bg-green-500"
                                style={{
                                  width: `${((currentDebugInfo.completion_tokens || 0) / currentDebugInfo.total_tokens) * 100}%`
                                }}
                              ></div>
                            </div>
                          </div>
                        )}
                      </div>

                      {/* 模型参数 */}
                      <div>
                        <h4 className="text-sm font-medium text-gray-700 mb-2">模型参数</h4>
                        <div className="space-y-1 text-xs">
                          <div className="flex justify-between">
                            <span className="text-gray-500">温度:</span>
                            <span className="text-gray-900">{currentDebugInfo.temperature || 'N/A'}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-500">最大Token:</span>
                            <span className="text-gray-900">{currentDebugInfo.max_tokens || 'N/A'}</span>
                          </div>
                        </div>
                      </div>

                      {/* API调用日志 */}
                      <div>
                        <h4 className="text-sm font-medium text-gray-700 mb-2">调用日志</h4>
                        <div className="bg-gray-100 rounded p-2 text-xs max-h-32 overflow-y-auto border border-gray-200">
                          {currentDebugInfo.api_call_time && (
                            <div className="text-blue-600 mb-1">
                              [{new Date(currentDebugInfo.api_call_time).toLocaleTimeString()}] API调用开始
                            </div>
                          )}
                          {currentDebugInfo.debug_info?.status && (
                            <div className="text-yellow-600 mb-1">
                              状态: {currentDebugInfo.debug_info.status}
                            </div>
                          )}
                          {currentDebugInfo.debug_info?.chunks_received && (
                            <div className="text-cyan-600 mb-1">
                              已接收: {currentDebugInfo.debug_info.chunks_received} 个数据块
                            </div>
                          )}
                          {currentDebugInfo.api_response_time && (
                            <div className="text-green-600 mb-1">
                              [{new Date(currentDebugInfo.api_response_time).toLocaleTimeString()}] API响应完成
                            </div>
                          )}
                          {currentDebugInfo.api_duration && (
                            <div className="text-purple-600 mb-1">
                              总耗时: {currentDebugInfo.api_duration.toFixed(3)}秒
                            </div>
                          )}
                          {!currentDebugInfo.api_call_time && (
                            <div className="text-gray-500">等待API调用...</div>
                          )}
                        </div>
                      </div>

                      {/* 视频处理模式说明 */}
                       <div>
                         <h4 className="text-sm font-medium text-gray-700 mb-2">处理模式</h4>
                         <div className="bg-gray-100 rounded p-2 text-xs border border-gray-200">
                           {transmissionMethod === 'base64' ? (
                             <>
                               <div className="text-purple-600 mb-1">
                                 <i className="fas fa-code mr-1"></i>
                                 Base64编码传输模式
                               </div>
                               <div className="text-gray-600 text-xs">
                                 视频文件直接编码传输
                               </div>
                             </>
                           ) : (currentDebugInfo.model_name?.toLowerCase().includes('glm-4.5v') || currentDebugInfo.model_name?.toLowerCase().includes('glm-4v')) && transmissionMethod !== ('base64' as any) ? (
                             <>
                               <div className="text-green-600 mb-1">
                                 <i className="fas fa-video mr-1"></i>
                                 视频内容理解模式
                               </div>
                               <div className="text-gray-600 text-xs">
                                 使用公网URL访问视频内容
                               </div>
                             </>
                           ) : (
                             <>
                               <div className="text-yellow-600 mb-1">
                                 <i className="fas fa-info-circle mr-1"></i>
                                 元数据分析模式
                               </div>
                               <div className="text-gray-600 text-xs">
                                 基于视频文件信息分析
                               </div>
                             </>
                           )}
                         </div>
                       </div>
                       
                       {/* URL配置状态 */}
                       <div>
                         <h4 className="text-sm font-medium text-gray-700 mb-2">URL配置</h4>
                         <div className="bg-gray-100 rounded p-2 text-xs border border-gray-200">
                           <div className="text-blue-600 mb-1">
                             <i className="fas fa-globe mr-1"></i>
                             {window.location.hostname === 'localhost' ? '本地开发环境' : '公网环境'}
                           </div>
                           <div className="text-gray-600 text-xs">
                             {window.location.hostname === 'localhost' 
                               ? '建议配置ngrok获得更好的GLM体验' 
                               : '已配置公网访问，支持GLM视频理解'}
                           </div>
                         </div>
                       </div>

                      {/* Curl命令 */}
                      {currentDebugInfo.debug_info?.curl_command && (
                        <div>
                          <h4 className="text-sm font-medium text-gray-700 mb-2">Curl命令</h4>
                          <div className="bg-gray-100 rounded p-2 text-xs border border-gray-200">
                            <code className="text-green-700 break-all">
                              {currentDebugInfo.debug_info.curl_command}
                            </code>
                          </div>
                        </div>
                      )}

                      {/* 实时统计 */}
                      {currentDebugInfo.debug_info?.current_content_length && (
                        <div>
                          <h4 className="text-sm font-medium text-gray-700 mb-2">实时统计</h4>
                          <div className="bg-gray-100 rounded p-2 text-xs space-y-1 border border-gray-200">
                            <div className="text-blue-600">
                              内容长度: {currentDebugInfo.debug_info.current_content_length} 字符
                            </div>
                            <div className="text-green-600">
                              输出Token: {currentDebugInfo.debug_info.current_completion_tokens}
                            </div>
                            <div className="text-purple-600">
                              总Token: {currentDebugInfo.debug_info.current_total_tokens}
                            </div>
                          </div>
                        </div>
                      )}

                      {/* 状态指示器 */}
                      <div className="flex items-center justify-between pt-2 border-t border-gray-200">
                        <span className="text-xs text-gray-500">实时监控</span>
                        <div className="flex items-center">
                          <div className={`w-2 h-2 rounded-full mr-1 ${
                            currentDebugInfo.api_response_time && currentAnalysis?.status === 'completed' ? 'bg-green-500' :
                            currentDebugInfo.api_call_time ? 'bg-yellow-500 animate-pulse' :
                            'bg-gray-400'
                          }`}></div>
                          <span className={`text-xs ${
                            currentDebugInfo.api_response_time && currentAnalysis?.status === 'completed' ? 'text-green-600' :
                            currentDebugInfo.api_call_time ? 'text-yellow-600' :
                            'text-gray-500'
                          }`}>
                            {currentDebugInfo.api_response_time && currentAnalysis?.status === 'completed' ? '已完成' :
                             currentDebugInfo.api_call_time ? '处理中' : '等待中'}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 步骤5：查看结果 */}
          {currentStep === 5 && (
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-semibold">解析结果</h2>
                <div className="flex space-x-3">
                  <button
                    onClick={() => exportResult(streamingResult, buildExportFilename(selectedVideo?.title || selectedVideo?.original_filename || '视频标题', currentAnalysis?.completed_at || currentAnalysis?.created_at))}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                  >
                    <i className="fas fa-download mr-2"></i>
                    导出MD
                  </button>
                  <button
                    onClick={resetToStart}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    <i className="fas fa-plus mr-2"></i>
                    新建解析
                  </button>
                </div>
              </div>
              
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* 左侧：解析结果 */}
                <div className="lg:col-span-2">
                  {/* 完成状态进度条 */}
                  <div className="mb-6">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium text-gray-700">解析进度</span>
                      <span className="text-sm text-green-600 font-medium">100% 已完成</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div className="bg-green-600 h-2 rounded-full w-full transition-all duration-300"></div>
                    </div>
                  </div>
                  
                  {streamingResult && (
                    <div className="border rounded-lg p-6 bg-white">
                      <div className="prose max-w-none">
                        <ReactMarkdown>
                          {streamingResult}
                        </ReactMarkdown>
                      </div>
                    </div>
                  )}
                </div>
                
                {/* 右侧：AI API调试信息 */}
                <div className="lg:col-span-1">
                  <div className="bg-white border border-gray-200 text-gray-800 rounded-lg overflow-hidden shadow-sm">
                    <div className="px-4 py-3 bg-gray-50 border-b border-gray-200">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center">
                          <i className="fas fa-bug text-gray-500 mr-2"></i>
                          <span className="font-medium text-gray-900">AI API 调试信息</span>
                        </div>
                        {/* API状态指示器 */}
                        <div className="flex items-center">
                          {currentAnalysis?.status === 'completed' ? (
                            <div className="flex items-center text-green-600">
                              <i className="fas fa-check-circle mr-1"></i>
                              <span className="text-xs font-medium">已完成</span>
                            </div>
                          ) : currentAnalysis?.status === 'processing' ? (
                            <div className="flex items-center text-yellow-600">
                              <i className="fas fa-spinner fa-spin mr-1"></i>
                              <span className="text-xs font-medium">处理中</span>
                            </div>
                          ) : currentAnalysis?.status === 'failed' ? (
                            <div className="flex items-center text-red-600">
                              <i className="fas fa-exclamation-circle mr-1"></i>
                              <span className="text-xs font-medium">失败</span>
                            </div>
                          ) : (
                            <div className="flex items-center text-gray-500">
                              <i className="fas fa-clock mr-1"></i>
                              <span className="text-xs font-medium">等待中</span>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="p-4 space-y-4 max-h-96 overflow-y-auto">
                      {/* 基本信息 */}
                      <div>
                        <h4 className="text-sm font-medium text-gray-700 mb-2">基本信息</h4>
                        <div className="space-y-1 text-xs">
                          <div className="flex justify-between">
                            <span className="text-gray-500">模型:</span>
                            <span className="text-gray-900">{currentDebugInfo.model_name || 'N/A'}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-500">提供商:</span>
                            <span className="text-gray-900">{currentDebugInfo.api_provider || 'N/A'}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-500">请求ID:</span>
                            <span className="text-gray-900 text-xs truncate">{currentDebugInfo.request_id || 'N/A'}</span>
                          </div>
                        </div>
                      </div>

                      {/* 时间信息 */}
                      <div>
                        <h4 className="text-sm font-medium text-gray-700 mb-2">时间信息</h4>
                        <div className="space-y-1 text-xs">
                          <div className="flex justify-between">
                            <span className="text-gray-500">调用时间:</span>
                            <span className="text-gray-900">
                              {currentDebugInfo.api_call_time ? new Date(currentDebugInfo.api_call_time).toLocaleTimeString() : 'N/A'}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-500">耗时:</span>
                            <span className={`${currentDebugInfo.api_duration && currentDebugInfo.api_duration > 10 ? 'text-red-500' : 'text-green-600'}`}>
                              {currentDebugInfo.api_duration ? `${currentDebugInfo.api_duration.toFixed(3)}秒` : 'N/A'}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Token使用情况 */}
                      <div>
                        <h4 className="text-sm font-medium text-gray-700 mb-2">Token 使用</h4>
                        <div className="space-y-1 text-xs">
                          <div className="flex justify-between">
                            <span className="text-gray-500">输入:</span>
                            <span className="text-blue-600">{currentDebugInfo.prompt_tokens || 0}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-500">输出:</span>
                            <span className="text-green-600">{currentDebugInfo.completion_tokens || 0}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-500">总计:</span>
                            <span className="text-purple-600">{currentDebugInfo.total_tokens || 0}</span>
                          </div>
                        </div>
                        
                        {/* Token使用可视化 */}
                        {currentDebugInfo.total_tokens && currentDebugInfo.total_tokens > 0 && (
                          <div className="mt-2">
                            <div className="flex h-1 bg-gray-200 rounded overflow-hidden">
                              <div 
                                className="bg-blue-500"
                                style={{
                                  width: `${((currentDebugInfo.prompt_tokens || 0) / currentDebugInfo.total_tokens) * 100}%`
                                }}
                              ></div>
                              <div 
                                className="bg-green-500"
                                style={{
                                  width: `${((currentDebugInfo.completion_tokens || 0) / currentDebugInfo.total_tokens) * 100}%`
                                }}
                              ></div>
                            </div>
                          </div>
                        )}
                      </div>
                      
                      {/* 性能指标 */}
                      <div>
                        <h4 className="text-sm font-medium text-gray-700 mb-2">性能指标</h4>
                        <div className="space-y-1 text-xs">
                          <div className="flex justify-between">
                            <span className="text-gray-500">处理时间:</span>
                            <span className={`${currentDebugInfo.processing_time && currentDebugInfo.processing_time > 30 ? 'text-red-500' : 'text-green-600'}`}>
                              {currentDebugInfo.processing_time ? `${currentDebugInfo.processing_time.toFixed(2)}秒` : 'N/A'}
                            </span>
                          </div>
                          {currentDebugInfo.confidence_score && (
                            <div className="flex justify-between">
                              <span className="text-gray-500">置信度:</span>
                              <span className={`${currentDebugInfo.confidence_score > 0.8 ? 'text-green-600' : currentDebugInfo.confidence_score > 0.6 ? 'text-yellow-600' : 'text-red-500'}`}>
                                {(currentDebugInfo.confidence_score * 100).toFixed(1)}%
                              </span>
                            </div>
                          )}
                          {currentDebugInfo.transmission_method && (
                            <div className="flex justify-between">
                              <span className="text-gray-500">传输方式:</span>
                              <span className="text-cyan-600">{currentDebugInfo.transmission_method}</span>
                            </div>
                          )}
                        </div>
                      </div>
                      
                      {/* 视频信息说明 */}
                        <div>
                          <h4 className="text-sm font-medium text-gray-700 mb-2">视频处理说明</h4>
                          <div className="bg-gray-100 rounded p-2 text-xs border border-gray-200">
                            {(currentDebugInfo.model_name?.toLowerCase().includes('glm-4.5v') || currentDebugInfo.model_name?.toLowerCase().includes('glm-4v')) && currentDebugInfo.transmission_method !== 'base64' ? (
                              <>
                                <div className="text-green-600 mb-1">
                                  <i className="fas fa-video mr-1"></i>
                                  AI分析基于视频实际内容
                                </div>
                                <div className="text-gray-600 text-xs leading-relaxed">
                                  使用GLM-4.5V视频理解模型，AI可以直接观看和分析视频的实际内容，
                                  包括画面、动作、场景、文字等视觉信息，提供更准确的分析结果。
                                </div>
                              </>
                            ) : currentDebugInfo.transmission_method === 'base64' ? (
                              <>
                                <div className="text-purple-600 mb-1">
                                  <i className="fas fa-code mr-1"></i>
                                  AI分析基于Base64编码视频
                                </div>
                                <div className="text-gray-600 text-xs leading-relaxed">
                                  视频文件通过Base64编码直接传输给AI模型进行分析，
                                  适合小文件（&lt;10MB），无需公网访问，安全性更高。
                                </div>
                              </>
                            ) : (
                              <>
                                <div className="text-yellow-600 mb-1">
                                  <i className="fas fa-info-circle mr-1"></i>
                                  AI分析基于视频元数据
                                </div>
                                <div className="text-gray-500 text-xs leading-relaxed">
                                  当前AI模型分析的是视频的元数据信息（文件名、时长、分辨率、格式等），
                                  而非视频的实际内容。建议使用GLM-4.5V模型获得真正的视频内容分析。
                                </div>
                              </>
                            )}
                          </div>
                        </div>
                        
                        {/* API请求详情 */}
                        {currentDebugInfo.debug_info && (
                          <div>
                            <h4 className="text-sm font-medium text-gray-700 mb-2">API请求详情</h4>
                            <div className="bg-gray-100 rounded p-2 text-xs space-y-2 border border-gray-200">
                              {/* API URL */}
                              {currentDebugInfo.debug_info.api_url && (
                                <div>
                                  <div className="text-cyan-600 mb-1">
                                    <i className="fas fa-link mr-1"></i>
                                    API端点
                                  </div>
                                  <div className="text-gray-600 font-mono text-xs break-all bg-gray-200 p-1 rounded">
                                    {currentDebugInfo.debug_info.api_url}
                                  </div>
                                </div>
                              )}
                              
                              {/* cURL命令 */}
                              {currentDebugInfo.debug_info.curl_command && (
                                <div>
                                  <div className="text-green-600 mb-1">
                                    <i className="fas fa-terminal mr-1"></i>
                                    cURL命令
                                  </div>
                                  <div className="text-gray-600 font-mono text-xs break-all bg-gray-200 p-2 rounded max-h-20 overflow-y-auto">
                                    {currentDebugInfo.debug_info.curl_command}
                                  </div>
                                </div>
                              )}
                              
                              {/* 请求头 */}
                              {currentDebugInfo.debug_info.request_headers && (
                                <div>
                                  <div className="text-yellow-600 mb-1">
                                    <i className="fas fa-list mr-1"></i>
                                    请求头
                                  </div>
                                  <div className="text-gray-600 font-mono text-xs bg-gray-200 p-2 rounded max-h-20 overflow-y-auto">
                                    {Object.entries(currentDebugInfo.debug_info.request_headers).map(([key, value]) => (
                                      <div key={key} className="mb-1">
                                        <span className="text-blue-600">{key}:</span> <span className="text-gray-700">{String(value)}</span>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}
                              
                              {/* 请求体大小 */}
                              {currentDebugInfo.debug_info.request_data && (
                                <div>
                                  <div className="text-purple-600 mb-1">
                                    <i className="fas fa-database mr-1"></i>
                                    请求体信息
                                  </div>
                                  <div className="text-gray-600 text-xs">
                                    <div>模型: {currentDebugInfo.debug_info.request_data.model || 'N/A'}</div>
                                    <div>最大Token: {currentDebugInfo.debug_info.request_data.max_tokens || 'N/A'}</div>
                                    <div>温度: {currentDebugInfo.debug_info.request_data.temperature || 'N/A'}</div>
                                    <div>流式: {currentDebugInfo.debug_info.request_data.stream ? '是' : '否'}</div>
                                    {currentDebugInfo.debug_info.request_data.messages && (
                                      <div>消息数量: {currentDebugInfo.debug_info.request_data.messages.length}</div>
                                    )}
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                        )}

                        {/* 传输配置状态 */}
                        <div>
                          <h4 className="text-sm font-medium text-gray-700 mb-2">传输配置</h4>
                          <div className="bg-gray-100 rounded p-2 text-xs border border-gray-200">
                            {currentDebugInfo.transmission_method === 'base64' ? (
                              <>
                                <div className="text-purple-600 mb-1">
                                  <i className="fas fa-code mr-1"></i>
                                  Base64编码传输
                                </div>
                                <div className="text-gray-600 text-xs leading-relaxed">
                                    视频文件被编码为Base64格式直接传输给AI模型，适合小文件（&lt;10MB），
                                    无需公网访问，安全性更高。
                                  </div>
                              </>
                            ) : currentDebugInfo.transmission_method === 'url' ? (
                              <>
                                <div className="text-blue-600 mb-1">
                                  <i className="fas fa-globe mr-1"></i>
                                  {window.location.hostname === 'localhost' ? '本地开发环境' : '公网环境'}
                                </div>
                                <div className="text-gray-600 text-xs leading-relaxed">
                                   {window.location.hostname === 'localhost' 
                                     ? 'GLM模型通过ngrok公网隧道访问视频文件，确保视频内容理解功能正常工作。' 
                                     : '已配置公网访问，GLM模型可直接访问视频文件进行内容分析。'}
                                 </div>
                               </>
                             ) : (
                               <>
                                 <div className="text-gray-500 mb-1">
                                   <i className="fas fa-question-circle mr-1"></i>
                                   未知传输方式
                                 </div>
                                 <div className="text-gray-500 text-xs leading-relaxed">
                                   传输方式信息不可用。
                                 </div>
                               </>
                             )}
                           </div>
                         </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>


        
        {/* 历史记录详情模态框 */}
        {showHistoryModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] flex flex-col overflow-hidden">
              <div className="flex justify-between items-center p-6 border-b shrink-0">
                <h3 className="text-xl font-semibold">分析结果详情{selectedHistoryId ? ` - ID: ${selectedHistoryId}` : ''}</h3>
                <button
                  onClick={closeHistoryModal}
                  className="text-gray-500 hover:text-gray-600 text-2xl"
                >
                  ×
                </button>
              </div>
              
              <div className="p-6 overflow-y-auto flex-1">
                {historyDetailLoading && (
                  <div className="flex items-center justify-center py-12">
                    <i className="fas fa-spinner fa-spin text-2xl text-blue-600 mr-3"></i>
                    <span className="text-gray-600">加载解析详情...</span>
                  </div>
                )}

                {!historyDetailLoading && historyDetailError && (
                  <div className="py-10 text-center">
                    <i className="fas fa-exclamation-circle text-3xl text-red-500 mb-3"></i>
                    <p className="text-gray-700 mb-4">{historyDetailError}</p>
                    <button
                      onClick={() => selectedHistoryId && loadHistoryDetail(selectedHistoryId)}
                      disabled={!selectedHistoryId}
                      className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-300 disabled:text-gray-500 disabled:cursor-not-allowed transition-colors"
                    >
                      重试
                    </button>
                  </div>
                )}

                {!historyDetailLoading && !historyDetailError && selectedHistoryItem && (
                  <>
                {/* 基本信息 */}
                <div className="mb-6">
                  <h4 className="text-lg font-medium mb-3">基本信息</h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div><span className="font-medium">视频ID:</span> {selectedHistoryItem.video_file_id}</div>
                    <div><span className="font-medium">状态:</span> 
                      <span className={`ml-2 px-2 py-1 rounded text-xs ${
                        selectedHistoryItem.status === 'completed' ? 'bg-green-100 text-green-800' :
                        selectedHistoryItem.status === 'failed' ? 'bg-red-100 text-red-800' :
                        'bg-blue-100 text-blue-800'
                      }`}>
                        {selectedHistoryItem.status === 'completed' ? '已完成' :
                         selectedHistoryItem.status === 'failed' ? '失败' : '处理中'}
                      </span>
                    </div>
                    <div><span className="font-medium">创建时间:</span> {new Date(selectedHistoryItem.created_at).toLocaleString()}</div>
                    {selectedHistoryItem.completed_at && (
                      <div><span className="font-medium">完成时间:</span> {new Date(selectedHistoryItem.completed_at).toLocaleString()}</div>
                    )}
                    {selectedHistoryItem.processing_time && (
                      <div><span className="font-medium">处理时间:</span> {selectedHistoryItem.processing_time.toFixed(2)}秒</div>
                    )}
                    {selectedHistoryItem.confidence_score && (
                      <div><span className="font-medium">置信度:</span> {(selectedHistoryItem.confidence_score * 100).toFixed(1)}%</div>
                    )}
                  </div>
                </div>
                
                {/* AI API 调试信息 */}
                {selectedHistoryItem.status === 'completed' && (
                  <div className="mb-6">
                    <h4 className="text-lg font-medium mb-3">AI API 调试信息</h4>
                    <div className="bg-white border border-gray-200 text-gray-800 rounded-lg overflow-hidden shadow-sm">
                      <div className="px-4 py-3 bg-gray-50 border-b border-gray-200">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center">
                            <i className="fas fa-bug text-gray-500 mr-2"></i>
                            <span className="font-medium text-gray-900">调试信息</span>
                          </div>
                          <div className="flex items-center text-green-600">
                            <i className="fas fa-check-circle mr-1"></i>
                            <span className="text-xs font-medium">已完成</span>
                          </div>
                        </div>
                      </div>
                      <div className="p-4 space-y-4">
                        {/* 基本信息 */}
                        <div>
                          <h5 className="text-sm font-medium text-gray-700 mb-2">基本信息</h5>
                          <div className="space-y-1 text-xs">
                            <div className="flex justify-between">
                              <span className="text-gray-500">模型:</span>
                              <span className="text-gray-900">{selectedHistoryItem.model_name || 'N/A'}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-500">提供商:</span>
                              <span className="text-gray-900">{selectedHistoryItem.api_provider || 'N/A'}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-500">请求ID:</span>
                              <span className="text-gray-900 text-xs truncate">{selectedHistoryItem.request_id || 'N/A'}</span>
                            </div>
                          </div>
                        </div>

                        {/* 时间信息 */}
                        <div>
                          <h5 className="text-sm font-medium text-gray-700 mb-2">时间信息</h5>
                          <div className="space-y-1 text-xs">
                            <div className="flex justify-between">
                              <span className="text-gray-500">调用时间:</span>
                              <span className="text-gray-900">
                                {selectedHistoryItem.api_call_time ? new Date(selectedHistoryItem.api_call_time).toLocaleTimeString() : 'N/A'}
                              </span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-500">耗时:</span>
                              <span className={`${selectedHistoryItem.api_duration && selectedHistoryItem.api_duration > 10 ? 'text-red-500' : 'text-green-600'}`}>
                                {selectedHistoryItem.api_duration ? `${selectedHistoryItem.api_duration.toFixed(3)}秒` : 'N/A'}
                              </span>
                            </div>
                          </div>
                        </div>

                        {/* Token使用情况 */}
                        <div>
                          <h5 className="text-sm font-medium text-gray-700 mb-2">Token 使用</h5>
                          <div className="space-y-1 text-xs">
                            <div className="flex justify-between">
                              <span className="text-gray-500">输入:</span>
                              <span className="text-blue-600">{selectedHistoryItem.prompt_tokens || 0}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-500">输出:</span>
                              <span className="text-green-600">{selectedHistoryItem.completion_tokens || 0}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-500">总计:</span>
                              <span className="text-purple-600">{selectedHistoryItem.total_tokens || 0}</span>
                            </div>
                          </div>
                          
                          {/* Token使用可视化 */}
                          {selectedHistoryItem.total_tokens && selectedHistoryItem.total_tokens > 0 && (
                            <div className="mt-2">
                              <div className="flex h-1 bg-gray-200 rounded overflow-hidden">
                                <div 
                                  className="bg-blue-500"
                                  style={{
                                    width: `${((selectedHistoryItem.prompt_tokens || 0) / selectedHistoryItem.total_tokens) * 100}%`
                                  }}
                                ></div>
                                <div 
                                  className="bg-green-500"
                                  style={{
                                    width: `${((selectedHistoryItem.completion_tokens || 0) / selectedHistoryItem.total_tokens) * 100}%`
                                  }}
                                ></div>
                              </div>
                            </div>
                          )}
                        </div>
                        
                        {/* 性能指标 */}
                        <div>
                          <h5 className="text-sm font-medium text-gray-700 mb-2">性能指标</h5>
                          <div className="space-y-1 text-xs">
                            <div className="flex justify-between">
                              <span className="text-gray-500">处理时间:</span>
                              <span className={`${selectedHistoryItem.processing_time && selectedHistoryItem.processing_time > 30 ? 'text-red-500' : 'text-green-600'}`}>
                                {selectedHistoryItem.processing_time ? `${selectedHistoryItem.processing_time.toFixed(2)}秒` : 'N/A'}
                              </span>
                            </div>
                            {selectedHistoryItem.confidence_score && (
                              <div className="flex justify-between">
                                <span className="text-gray-500">置信度:</span>
                                <span className={`${selectedHistoryItem.confidence_score > 0.8 ? 'text-green-600' : selectedHistoryItem.confidence_score > 0.6 ? 'text-yellow-600' : 'text-red-500'}`}>
                                  {(selectedHistoryItem.confidence_score * 100).toFixed(1)}%
                                </span>
                              </div>
                            )}
                            {selectedHistoryItem.temperature && (
                              <div className="flex justify-between">
                                <span className="text-gray-500">温度:</span>
                                <span className="text-cyan-600">{selectedHistoryItem.temperature}</span>
                              </div>
                            )}
                            {selectedHistoryItem.max_tokens && (
                              <div className="flex justify-between">
                                <span className="text-gray-500">最大Token:</span>
                                <span className="text-cyan-600">{selectedHistoryItem.max_tokens}</span>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
                
                {/* 提示词内容 */}
                {selectedHistoryItem.prompt_content && (
                  <div className="mb-6">
                    <h4 className="text-lg font-medium mb-3">提示词内容</h4>
                    <div className="bg-gray-50 p-4 rounded-lg text-sm whitespace-pre-wrap">
                      {selectedHistoryItem.prompt_content}
                    </div>
                  </div>
                )}
                
                {/* 分析结果 */}
                {selectedHistoryItem.analysis_result && (
                  <div className="mb-6">
                    <div className="flex justify-between items-center mb-3">
                      <h4 className="text-lg font-medium">分析结果</h4>
                      <button
                        onClick={() => exportResult(selectedHistoryItem.analysis_result!, buildExportFilename(selectedHistoryVideoTitle || `analysis-${selectedHistoryItem.video_file_id}`, selectedHistoryItem.completed_at || selectedHistoryItem.created_at))}
                        className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors"
                      >
                        <i className="fas fa-download mr-1"></i>
                        导出结果
                      </button>
                    </div>
                    <div className="bg-white border rounded-lg p-4 max-h-96 overflow-y-auto">
                      <div className="prose max-w-none">
                        <ReactMarkdown>
                          {selectedHistoryItem.analysis_result}
                        </ReactMarkdown>
                      </div>
                    </div>
                  </div>
                )}
                
                {/* 结果摘要 */}
                {selectedHistoryItem.result_summary && (
                  <div className="mb-6">
                    <h4 className="text-lg font-medium mb-3">结果摘要</h4>
                    <div className="bg-gray-50 p-4 rounded-lg text-sm">
                      {selectedHistoryItem.result_summary}
                    </div>
                  </div>
                )}
                  </>
                )}
              </div>
              
              <div className="flex justify-end p-6 border-t bg-gray-50 shrink-0">
                <button
                  onClick={closeHistoryModal}
                  className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 transition-colors"
                >
                  关闭
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
      

    </div>
  );
};

export default VideoAnalysis;
