import React, { useState, useEffect, useRef } from 'react';
import { VideoAnalysis } from '../types';
import { formatDate } from '../utils';

const VideoAnalysisPage: React.FC = () => {
  // 视频信息状态
  const [videoInfo, setVideoInfo] = useState({
    id: 'V20231115-001',
    title: '如何快速掌握React开发技巧',
    platform: 'bilibili',
    author: '前端开发达人',
    tags: ['React', '前端开发', '教程', 'JavaScript', 'Hooks'],
    duration: '05:32',
    size: '15.6MB',
    createTime: '2023-11-15 14:30:22',
    uploadTime: '2023-11-15 15:45:10',
    status: '已解析',
    parseTime: '2023-11-15 16:20:05',
    thumbnail: 'https://via.placeholder.com/320x180'
  });

  // 模板选择状态
  const [templates, setTemplates] = useState([
    { id: 't1', name: '标准解析模板', content: '请分析这段视频的主要内容，包括核心观点、技术要点和适用场景。' },
    { id: 't2', name: '深度解析模板', content: '请从专业角度深入分析这段视频的技术要点、实现原理和最佳实践。' },
    { id: 't3', name: '营销分析模板', content: '请分析这段视频的营销策略、受众定位和传播效果。' },
    { id: 't4', name: '教育分析模板', content: '请从教育角度分析视频的教学方法、知识结构和学习效果。' }
  ]);
  const [selectedTemplate, setSelectedTemplate] = useState('t1');

  // 打标方式状态
  const [taggingMethods, setTaggingMethods] = useState([
    { id: 'm1', name: '开放式打标', description: '自由添加标签' },
    { id: 'm2', name: '按标签组打标', description: '从预设标签组中选择' },
    { id: 'm3', name: '标签组+开放打标', description: '结合预设标签和自定义标签' }
  ]);
  const [selectedMethod, setSelectedMethod] = useState('m1');
  
  const [tagGroups, setTagGroups] = useState([
    { id: 'g1', name: '技术标签', tags: ['React', 'Vue', 'Angular', 'JavaScript', 'TypeScript', 'Node.js'] },
    { id: 'g2', name: '内容标签', tags: ['教程', '实战', '理论', '案例', '演示', '讲解'] },
    { id: 'g3', name: '难度标签', tags: ['初级', '中级', '高级', '专家级'] },
    { id: 'g4', name: '行业标签', tags: ['前端', '后端', '全栈', '移动端', 'AI', '数据分析'] }
  ]);
  const [selectedTagGroup, setSelectedTagGroup] = useState('g1');
  const [customTags, setCustomTags] = useState<string[]>([]);
  const [newTag, setNewTag] = useState('');

  // AI接口状态
  const [aiApis, setAiApis] = useState([
    { id: 'a1', name: '默认API', description: '平衡性能和成本' },
    { id: 'a2', name: '高性能API', description: '更快的响应速度' },
    { id: 'a3', name: '经济型API', description: '成本优化选择' }
  ]);
  const [selectedApi, setSelectedApi] = useState('a1');
  const [aiParams, setAiParams] = useState({
    temperature: 0.7,
    thinkMode: false,
    maxTokens: 2000,
    otherParam: ''
  });

  // 提示词状态
  const [promptText, setPromptText] = useState('');
  const [renderedPrompt, setRenderedPrompt] = useState('');

  // AI解析结果状态
  const [aiResult, setAiResult] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [analysisHistory, setAnalysisHistory] = useState<any[]>([]);
  const resultRef = useRef<HTMLDivElement>(null);

  // 初始化提示词
  useEffect(() => {
    updatePrompt();
  }, [selectedTemplate, selectedMethod, selectedTagGroup, aiParams, customTags]);

  // 更新提示词
  const updatePrompt = () => {
    const template = templates.find(t => t.id === selectedTemplate);
    let newPrompt = template ? template.content : '';
    
    // 添加视频信息
    newPrompt += `\n\n## 视频信息\n`;
    newPrompt += `- 标题: ${videoInfo.title}\n`;
    newPrompt += `- 平台: ${videoInfo.platform}\n`;
    newPrompt += `- 作者: ${videoInfo.author}\n`;
    newPrompt += `- 时长: ${videoInfo.duration}\n`;
    
    // 添加标签信息
    if (selectedMethod !== 'm1') {
      const tagGroup = tagGroups.find(g => g.id === selectedTagGroup);
      if (tagGroup) {
        newPrompt += `\n## 相关标签\n${tagGroup.name}: ${tagGroup.tags.join(', ')}\n`;
      }
    }
    
    if (customTags.length > 0) {
      newPrompt += `\n自定义标签: ${customTags.join(', ')}\n`;
    }
    
    // 添加AI参数
    newPrompt += `\n## 分析要求\n`;
    newPrompt += `- 分析深度: ${aiParams.temperature > 0.8 ? '深入' : aiParams.temperature > 0.5 ? '中等' : '简要'}\n`;
    newPrompt += `- 思考模式: ${aiParams.thinkMode ? '开启逐步推理' : '直接分析'}\n`;
    
    setPromptText(newPrompt);
    setRenderedPrompt(newPrompt);
  };

  // 添加自定义标签
  const addCustomTag = () => {
    if (newTag.trim() && !customTags.includes(newTag.trim())) {
      setCustomTags([...customTags, newTag.trim()]);
      setNewTag('');
    }
  };

  // 删除自定义标签
  const removeCustomTag = (tag: string) => {
    setCustomTags(customTags.filter(t => t !== tag));
  };

  // 模拟AI流式返回
  const simulateAIStream = () => {
    setIsStreaming(true);
    setAiResult('');
    
    const responses = [
      "## 视频解析报告\n\n",
      "### 1. 主要内容分析\n\n",
      "这段视频主要讲解了React开发中的几个核心技巧，包括Hooks的使用、性能优化和状态管理等关键概念。\n\n",
      "### 2. 技术要点\n\n",
      "- **Hooks使用**: 详细介绍了useState、useEffect等常用Hooks的实际应用\n",
      "- **性能优化**: 讲解了React.memo、useMemo、useCallback等优化技巧\n",
      "- **状态管理**: 展示了Context API和第三方状态管理库的使用场景\n",
      "- **最佳实践**: 分享了组件设计和代码组织的经验\n\n",
      "### 3. 适用人群\n\n",
      "适合有一定React基础的中级开发者，特别是希望提升开发效率和代码质量的前端工程师。\n\n",
      "### 4. 学习价值\n\n",
      "- 实用性强，可以直接应用到实际项目中\n",
      "- 讲解清晰，配有代码示例\n",
      "- 涵盖了React开发的核心概念\n\n",
      "### 5. 综合评价\n\n",
      "视频内容专业且实用，讲解方式通俗易懂，对React开发者具有很好的指导意义。建议配合实际项目练习以加深理解。"
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
        // 添加到历史记录
        const newAnalysis = {
          id: Date.now().toString(),
          timestamp: new Date().toISOString(),
          template: templates.find(t => t.id === selectedTemplate)?.name,
          result: aiResult + responses[responses.length - 1],
          prompt: renderedPrompt
        };
        setAnalysisHistory([newAnalysis, ...analysisHistory]);
      }
    }, 200);
  };

  const startAnalysis = () => {
    if (!renderedPrompt.trim()) {
      alert('请先配置分析模板和参数');
      return;
    }
    simulateAIStream();
  };

  const exportResult = () => {
    if (!aiResult) {
      alert('暂无分析结果可导出');
      return;
    }
    
    const content = `# 视频解析报告\n\n## 视频信息\n- 标题: ${videoInfo.title}\n- 分析时间: ${new Date().toLocaleString()}\n\n## 分析结果\n\n${aiResult}`;
    const blob = new Blob([content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${videoInfo.title}-分析报告.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-800">视频解析</h1>
        <div className="text-sm text-gray-500">
          AI智能分析视频内容，提取关键信息
        </div>
      </div>

      {/* 视频信息卡片 */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex items-start space-x-4">
          <img
            src={videoInfo.thumbnail}
            alt={videoInfo.title}
            className="w-32 h-20 object-cover rounded"
          />
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-800 mb-2">{videoInfo.title}</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-600">
              <div>平台：{videoInfo.platform}</div>
              <div>作者：{videoInfo.author}</div>
              <div>时长：{videoInfo.duration}</div>
              <div>大小：{videoInfo.size}</div>
            </div>
            <div className="flex flex-wrap gap-2 mt-3">
              {videoInfo.tags.map((tag, index) => (
                <span key={index} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                  {tag}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 左侧配置面板 */}
        <div className="space-y-6">
          {/* 模板选择 */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">分析模板</h3>
            <div className="space-y-3">
              {templates.map(template => (
                <label key={template.id} className="flex items-start space-x-3 cursor-pointer">
                  <input
                    type="radio"
                    name="template"
                    value={template.id}
                    checked={selectedTemplate === template.id}
                    onChange={(e) => setSelectedTemplate(e.target.value)}
                    className="mt-1"
                  />
                  <div>
                    <div className="font-medium text-gray-800">{template.name}</div>
                    <div className="text-sm text-gray-600">{template.content}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* 打标方式 */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">打标方式</h3>
            <div className="space-y-3 mb-4">
              {taggingMethods.map(method => (
                <label key={method.id} className="flex items-start space-x-3 cursor-pointer">
                  <input
                    type="radio"
                    name="method"
                    value={method.id}
                    checked={selectedMethod === method.id}
                    onChange={(e) => setSelectedMethod(e.target.value)}
                    className="mt-1"
                  />
                  <div>
                    <div className="font-medium text-gray-800">{method.name}</div>
                    <div className="text-sm text-gray-600">{method.description}</div>
                  </div>
                </label>
              ))}
            </div>

            {/* 标签组选择 */}
            {selectedMethod !== 'm1' && (
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">选择标签组</label>
                <select
                  value={selectedTagGroup}
                  onChange={(e) => setSelectedTagGroup(e.target.value)}
                  className="input-field"
                >
                  {tagGroups.map(group => (
                    <option key={group.id} value={group.id}>{group.name}</option>
                  ))}
                </select>
                <div className="mt-2 flex flex-wrap gap-2">
                  {tagGroups.find(g => g.id === selectedTagGroup)?.tags.map((tag, index) => (
                    <span key={index} className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* 自定义标签 */}
            {(selectedMethod === 'm1' || selectedMethod === 'm3') && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">自定义标签</label>
                <div className="flex space-x-2 mb-2">
                  <input
                    type="text"
                    value={newTag}
                    onChange={(e) => setNewTag(e.target.value)}
                    placeholder="输入标签名称"
                    className="input-field flex-1"
                    onKeyPress={(e) => e.key === 'Enter' && addCustomTag()}
                  />
                  <button onClick={addCustomTag} className="btn-primary">
                    添加
                  </button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {customTags.map((tag, index) => (
                    <span key={index} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded flex items-center">
                      {tag}
                      <button
                        onClick={() => removeCustomTag(tag)}
                        className="ml-1 text-blue-600 hover:text-blue-800"
                      >
                        <i className="fas fa-times text-xs"></i>
                      </button>
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* AI接口配置 */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">AI接口配置</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">选择API</label>
                <select
                  value={selectedApi}
                  onChange={(e) => setSelectedApi(e.target.value)}
                  className="input-field"
                >
                  {aiApis.map(api => (
                    <option key={api.id} value={api.id}>{api.name} - {api.description}</option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  创造性 ({aiParams.temperature})
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={aiParams.temperature}
                  onChange={(e) => setAiParams({...aiParams, temperature: parseFloat(e.target.value)})}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>保守</span>
                  <span>创新</span>
                </div>
              </div>
              
              <div>
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={aiParams.thinkMode}
                    onChange={(e) => setAiParams({...aiParams, thinkMode: e.target.checked})}
                  />
                  <span className="text-sm font-medium text-gray-700">启用思考模式</span>
                </label>
                <p className="text-xs text-gray-500 mt-1">AI将展示分析过程和推理步骤</p>
              </div>
            </div>
          </div>
        </div>

        {/* 右侧分析面板 */}
        <div className="space-y-6">
          {/* 提示词预览 */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-gray-800">提示词预览</h3>
              <button
                onClick={startAnalysis}
                disabled={isStreaming}
                className="btn-primary"
              >
                {isStreaming ? (
                  <>
                    <i className="fas fa-spinner fa-spin mr-2"></i>
                    分析中...
                  </>
                ) : (
                  <>
                    <i className="fas fa-play mr-2"></i>
                    开始分析
                  </>
                )}
              </button>
            </div>
            <div className="bg-gray-50 rounded p-4 max-h-64 overflow-y-auto">
              <pre className="text-sm text-gray-700 whitespace-pre-wrap">{renderedPrompt}</pre>
            </div>
          </div>

          {/* 分析结果 */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-gray-800">分析结果</h3>
              {aiResult && (
                <button onClick={exportResult} className="btn-secondary">
                  <i className="fas fa-download mr-2"></i>
                  导出报告
                </button>
              )}
            </div>
            <div 
              ref={resultRef}
              className="bg-gray-50 rounded p-4 min-h-64 max-h-96 overflow-y-auto"
            >
              {aiResult ? (
                <div className="prose prose-sm max-w-none">
                  <pre className="text-sm text-gray-700 whitespace-pre-wrap">{aiResult}</pre>
                  {isStreaming && (
                    <div className="inline-block w-2 h-4 bg-blue-600 animate-pulse ml-1"></div>
                  )}
                </div>
              ) : (
                <div className="text-center text-gray-500 py-8">
                  <i className="fas fa-robot text-4xl mb-4"></i>
                  <p>点击"开始分析"按钮开始AI分析</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* 历史记录 */}
      {analysisHistory.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">分析历史</h3>
          <div className="space-y-4">
            {analysisHistory.slice(0, 5).map((analysis) => (
              <div key={analysis.id} className="border border-gray-200 rounded p-4">
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <span className="font-medium text-gray-800">{analysis.template}</span>
                    <span className="text-sm text-gray-500 ml-2">
                      {formatDate(analysis.timestamp)}
                    </span>
                  </div>
                  <button className="text-blue-600 hover:text-blue-800 text-sm">
                    查看详情
                  </button>
                </div>
                <div className="text-sm text-gray-600 line-clamp-3">
                  {analysis.result.substring(0, 200)}...
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default VideoAnalysisPage;