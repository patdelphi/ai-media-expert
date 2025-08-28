import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { VideoInfo, PromptTemplate, TagGroup, AIApiConfig, AIParams } from '@/types';

const VideoAnalysis: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const resultRef = useRef<HTMLDivElement>(null);

  // 视频信息状态
  const [videoInfo, setVideoInfo] = useState<VideoInfo>({
    id: id || 'V20231115-001',
    title: '如何快速掌握React开发技巧',
    platform: 'B站',
    author: {
      name: '前端开发达人',
      avatar: 'https://ai-public.mastergo.com/ai/img_res/78c9becbcdb331677f04bb7e7372d347.jpg'
    },
    tags: ['React', '前端开发', '教程', 'JavaScript', 'Hooks'],
    duration: '05:32',
    size: '15.6MB',
    createTime: '2023-11-15 14:30:22',
    uploadTime: '2023-11-15 15:45:10',
    status: '已解析',
    parseTime: '2023-11-15 16:20:05',
    thumbnail: 'https://ai-public.mastergo.com/ai/img_res/237456bb54e887c73e45408953f95151.jpg'
  });

  // 模板选择状态
  const [templates, setTemplates] = useState<PromptTemplate[]>([
    { id: 't1', name: '标准解析模板', title: '标准解析模板', content: '请分析这段视频的主要内容，包括核心观点、技术要点和适用场景。' },
    { id: 't2', name: '深度解析模板', title: '深度解析模板', content: '请从专业角度深入分析这段视频的技术要点、实现原理和最佳实践。' },
    { id: 't3', name: '营销分析模板', title: '营销分析模板', content: '请分析这段视频的营销策略、受众定位和传播效果。' }
  ]);
  const [selectedTemplate, setSelectedTemplate] = useState('t1');

  // 打标方式状态
  const [taggingMethods, setTaggingMethods] = useState([
    { id: 'm1', name: '开放式打标' },
    { id: 'm2', name: '按标签组打标' },
    { id: 'm3', name: '标签组+开放打标' }
  ]);
  const [selectedMethod, setSelectedMethod] = useState('m1');
  const [tagGroups, setTagGroups] = useState<TagGroup[]>([
    { id: 'g1', name: '技术标签', tags: ['React', 'Vue', 'Angular', 'JavaScript'] },
    { id: 'g2', name: '内容标签', tags: ['教程', '实战', '理论', '案例'] },
    { id: 'g3', name: '难度标签', tags: ['初级', '中级', '高级'] }
  ]);
  const [selectedTagGroup, setSelectedTagGroup] = useState('g1');

  // AI接口状态
  const [aiApis, setAiApis] = useState<AIApiConfig[]>([
    { id: 'a1', name: '默认API', provider: 'OpenAI', apiKey: 'sk-***', enabled: true },
    { id: 'a2', name: '高性能API', provider: 'Claude', apiKey: 'sk-***', enabled: true },
    { id: 'a3', name: '经济型API', provider: 'Custom', apiKey: 'sk-***', enabled: false }
  ]);
  const [selectedApi, setSelectedApi] = useState('a1');
  const [aiParams, setAiParams] = useState<AIParams>({
    temperature: 0.7,
    thinkMode: false,
    otherParam: ''
  });

  // 提示词状态
  const [promptText, setPromptText] = useState('');
  const [renderedPrompt, setRenderedPrompt] = useState('');

  // AI解析结果状态
  const [aiResult, setAiResult] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);

  // 初始化提示词
  useEffect(() => {
    updatePrompt();
  }, [selectedTemplate, selectedMethod, selectedTagGroup, aiParams]);

  // 更新提示词
  const updatePrompt = () => {
    const template = templates.find(t => t.id === selectedTemplate);
    let newPrompt = template ? template.content : '';
    
    if (selectedMethod !== 'm1') {
      const tagGroup = tagGroups.find(g => g.id === selectedTagGroup);
      if (tagGroup) {
        newPrompt += `\n\n相关标签: ${tagGroup.tags.join(', ')}`;
      }
    }
    
    newPrompt += `\n\nAI参数: 温度=${aiParams.temperature}, 思考模式=${aiParams.thinkMode ? '开启' : '关闭'}`;
    
    setPromptText(newPrompt);
    setRenderedPrompt(newPrompt);
  };

  // 模拟AI流式返回
  const simulateAIStream = () => {
    setIsStreaming(true);
    setAiResult('');
    
    const responses = [
      "## 视频解析报告\n\n",
      "### 1. 主要内容分析\n\n",
      "这段视频主要讲解了React开发中的几个核心技巧...\n\n",
      "### 2. 技术要点\n\n",
      "- 使用Hooks简化组件逻辑\n",
      "- 性能优化技巧\n",
      "- 状态管理最佳实践\n\n",
      "### 3. 适用人群\n\n",
      "适合有一定React基础的中级开发者...\n\n",
      "### 4. 综合评价\n\n",
      "视频内容专业，讲解清晰，对React开发者有很好的指导意义。"
    ];
    
    let index = 0;
    const interval = setInterval(() => {
      if (index < responses.length) {
        setAiResult(prev => prev + responses[index]);
        if (resultRef.current) {
          resultRef.current.scrollTop = resultRef.current.scrollHeight;
        }
        index++;
      } else {
        clearInterval(interval);
        setIsStreaming(false);
      }
    }, 200);
  };

  // 处理提交
  const handleSubmit = () => {
    simulateAIStream();
  };

  // 复制文本
  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    // 这里可以添加复制成功的反馈
  };

  // 获取平台图标
  const getPlatformIcon = (platform: string) => {
    switch (platform) {
      case 'B站':
        return <i className="fab fa-bilibili text-blue-500"></i>;
      case '抖音':
        return <i className="fab fa-tiktok text-black"></i>;
      case '小红书':
        return <i className="fas fa-book text-red-500"></i>;
      case '快手':
        return <i className="fas fa-bolt text-orange-500"></i>;
      case '视频号':
        return <i className="fas fa-video text-green-500"></i>;
      default:
        return <i className="fas fa-globe text-gray-500"></i>;
    }
  };

  return (
    <div className="space-y-6">
      {/* 视频信息区域 */}
      <div className="bg-white shadow-sm rounded-lg p-6">
        <div className="flex flex-col md:flex-row gap-6">
          {/* 视频播放器 */}
          <div className="w-full md:w-1/3 aspect-video bg-gray-200 rounded-lg overflow-hidden relative">
            <div className="absolute inset-0 flex items-center justify-center">
              <i className="fas fa-play text-4xl text-white bg-black bg-opacity-50 rounded-full p-4 cursor-pointer hover:bg-opacity-70"></i>
            </div>
            <img
              src={videoInfo.thumbnail}
              alt="视频缩略图"
              className="w-full h-full object-cover"
            />
          </div>
          
          {/* 视频信息 */}
          <div className="w-full md:w-2/3">
            <div className="flex justify-between items-start mb-2">
              <h1 className="text-2xl font-bold">{videoInfo.title}</h1>
              <span className="text-sm text-gray-500">ID: {videoInfo.id}</span>
            </div>
            <div className="flex items-center gap-2 mb-4">
              {getPlatformIcon(videoInfo.platform)}
              <span className="text-gray-700">{videoInfo.platform}</span>
              <span className="text-gray-500 mx-2">|</span>
              <i className="fas fa-user text-gray-500"></i>
              <span className="text-gray-700">
                {typeof videoInfo.author === 'string' ? videoInfo.author : videoInfo.author.name}
              </span>
            </div>
            
            {/* 标签 */}
            <div className="flex flex-wrap gap-2 mb-4">
              {videoInfo.tags.map((tag, index) => (
                <span
                  key={index}
                  className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm cursor-pointer hover:bg-blue-200"
                >
                  {tag}
                </span>
              ))}
            </div>
            
            {/* 元数据 */}
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-gray-500">时长:</span>
                <span className="ml-2">{videoInfo.duration}</span>
              </div>
              <div>
                <span className="text-gray-500">文件大小:</span>
                <span className="ml-2">{videoInfo.size}</span>
              </div>
              <div>
                <span className="text-gray-500">创作时间:</span>
                <span className="ml-2">{videoInfo.createTime}</span>
              </div>
              <div>
                <span className="text-gray-500">上传时间:</span>
                <span className="ml-2">{videoInfo.uploadTime}</span>
              </div>
              <div>
                <span className="text-gray-500">解析状态:</span>
                <span className={`ml-2 px-2 py-1 rounded text-xs ${
                  videoInfo.status === '已解析' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                }`}>
                  {videoInfo.status}
                </span>
              </div>
              {videoInfo.status === '已解析' && (
                <div>
                  <span className="text-gray-500">解析时间:</span>
                  <span className="ml-2">{videoInfo.parseTime}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* 参数选择区域 */}
      <div className="bg-white shadow-sm rounded-lg p-6">
        <div className="space-y-6">
          {/* 提示词模板设置区域 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 p-4 border border-gray-200 rounded-lg">
            <div>
              <h3 className="text-lg font-medium text-gray-800 mb-3">提示词模板设置</h3>
              <label className="block text-sm font-medium text-gray-700 mb-1">提示词模板</label>
              <div className="relative">
                <select
                  className="block w-full rounded-button border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm"
                  value={selectedTemplate}
                  onChange={(e) => setSelectedTemplate(e.target.value)}
                >
                  {templates.map(template => (
                    <option key={template.id} value={template.id}>{template.name}</option>
                  ))}
                </select>
              </div>
            </div>
            <div>
              <h3 className="text-lg font-medium text-gray-800 mb-3">模板内容</h3>
              <div className="border border-gray-200 rounded p-3 overflow-y-auto bg-gray-50 min-h-[10rem]">
                <div className="prose prose-sm max-w-none">
                  {templates.find(t => t.id === selectedTemplate)?.content}
                </div>
                <button
                  className="mt-2 rounded-button bg-blue-600 text-white px-3 py-1 text-sm hover:bg-blue-700 whitespace-nowrap"
                  onClick={() => copyToClipboard(templates.find(t => t.id === selectedTemplate)?.content || '')}
                >
                  <i className="fas fa-copy mr-1"></i> 复制内容
                </button>
              </div>
            </div>
          </div>

          {/* 打标方式设置区域 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 p-4 border border-gray-200 rounded-lg">
            <div>
              <h3 className="text-lg font-medium text-gray-800 mb-3">打标方式设置</h3>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">打标方式</label>
                <div className="relative">
                  <select
                    className="block w-full rounded-button border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm"
                    value={selectedMethod}
                    onChange={(e) => setSelectedMethod(e.target.value)}
                  >
                    {taggingMethods.map(method => (
                      <option key={method.id} value={method.id}>{method.name}</option>
                    ))}
                  </select>
                </div>
                {selectedMethod !== 'm1' && (
                  <div className="mt-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">选择标签组</label>
                    <div className="relative">
                      <select
                        className="block w-full rounded-button border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm"
                        value={selectedTagGroup}
                        onChange={(e) => setSelectedTagGroup(e.target.value)}
                      >
                        {tagGroups.map(group => (
                          <option key={group.id} value={group.id}>{group.name}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                )}
              </div>
            </div>
            {selectedMethod !== 'm1' && (
              <div>
                <h3 className="text-lg font-medium text-gray-800 mb-3">标签组内容</h3>
                <div className="border border-gray-200 rounded p-3 bg-gray-50">
                  <div className="flex flex-wrap gap-2">
                    {tagGroups.find(g => g.id === selectedTagGroup)?.tags.map((tag, index) => (
                      <span key={index} className="px-2 py-1 bg-gray-200 rounded text-sm">{tag}</span>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* AI接口设置区域 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 p-4 border border-gray-200 rounded-lg">
            <div>
              <h3 className="text-lg font-medium text-gray-800 mb-3">AI接口设置</h3>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">AI接口选择</label>
                <div className="relative">
                  <select
                    className="block w-full rounded-button border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm"
                    value={selectedApi}
                    onChange={(e) => setSelectedApi(e.target.value)}
                  >
                    {aiApis.map(api => (
                      <option key={api.id} value={api.id}>{api.name}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
            <div>
              <h3 className="text-lg font-medium text-gray-800 mb-3">AI参数设置</h3>
              <div className="border border-gray-200 rounded p-3 bg-gray-50 space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-sm">温度: {aiParams.temperature}</label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={aiParams.temperature}
                    onChange={(e) => setAiParams({...aiParams, temperature: parseFloat(e.target.value)})}
                    className="w-24"
                  />
                </div>
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="thinkMode"
                    checked={aiParams.thinkMode}
                    onChange={(e) => setAiParams({...aiParams, thinkMode: e.target.checked})}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="thinkMode" className="ml-2 block text-sm text-gray-700">思考模式</label>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 提示词区域 */}
      <div className="bg-white shadow-sm rounded-lg p-6">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">提示词原文</label>
            <textarea
              className="w-full border border-gray-300 rounded p-3 h-32 focus:border-blue-500 focus:ring-blue-500 text-sm"
              value={promptText}
              onChange={(e) => setPromptText(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">渲染后提示词</label>
            <div className="border border-gray-200 rounded p-3 h-32 overflow-y-auto bg-gray-50">
              <div className="prose prose-sm max-w-none whitespace-pre-wrap">
                {renderedPrompt}
              </div>
            </div>
          </div>
        </div>
        <div className="flex gap-2 mt-4">
          <button
            className="rounded-button bg-blue-600 text-white px-4 py-2 text-sm hover:bg-blue-700 whitespace-nowrap"
            onClick={handleSubmit}
            disabled={isStreaming}
          >
            {isStreaming ? (
              <>
                <i className="fas fa-spinner animate-spin mr-1"></i> 解析中...
              </>
            ) : (
              <>
                <i className="fas fa-paper-plane mr-1"></i> 提交解析
              </>
            )}
          </button>
          <button
            className="rounded-button bg-gray-200 text-gray-700 px-4 py-2 text-sm hover:bg-gray-300 whitespace-nowrap"
            onClick={() => copyToClipboard(renderedPrompt)}
          >
            <i className="fas fa-copy mr-1"></i> 复制提示词
          </button>
          <button className="rounded-button bg-gray-200 text-gray-700 px-4 py-2 text-sm hover:bg-gray-300 whitespace-nowrap">
            保存模板
          </button>
          <button className="rounded-button bg-gray-200 text-gray-700 px-4 py-2 text-sm hover:bg-gray-300 whitespace-nowrap">
            重置
          </button>
        </div>
      </div>

      {/* AI解析结果区域 */}
      <div className="bg-white shadow-sm rounded-lg p-6">
        <div
          ref={resultRef}
          className="border border-gray-200 rounded p-4 h-64 overflow-y-auto bg-gray-50 mb-4"
        >
          <div className="prose prose-sm max-w-none whitespace-pre-wrap">
            {aiResult || (isStreaming ? 'AI正在思考中...' : '请先提交解析请求')}
          </div>
        </div>
        <div className="flex gap-2">
          <button
            className="rounded-button bg-gray-200 text-gray-700 px-4 py-2 text-sm hover:bg-gray-300 whitespace-nowrap"
            onClick={() => copyToClipboard(aiResult)}
            disabled={!aiResult}
          >
            <i className="fas fa-copy mr-1"></i> 复制结果
          </button>
          <button
            className="rounded-button bg-blue-600 text-white px-4 py-2 text-sm hover:bg-blue-700 whitespace-nowrap"
            onClick={simulateAIStream}
            disabled={isStreaming}
          >
            <i className="fas fa-sync-alt mr-1"></i> 重新解析
          </button>
          <button className="rounded-button bg-gray-200 text-gray-700 px-4 py-2 text-sm hover:bg-gray-300 whitespace-nowrap">
            导出结果
          </button>
          <button className="rounded-button bg-gray-200 text-gray-700 px-4 py-2 text-sm hover:bg-gray-300 whitespace-nowrap">
            分享结果
          </button>
        </div>
      </div>
    </div>
  );
};

export default VideoAnalysis;