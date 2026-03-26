/**
 * AI API调试信息显示组件
 * 
 * 功能说明：
 * 1. 实时显示AI API调用的调试信息
 * 2. 展示Token使用情况、调用时间、模型参数等
 * 3. 支持展开/折叠详细信息
 * 4. 提供调试数据的可视化展示
 */

import React, { useState } from 'react';

// 调试信息接口定义
interface DebugInfo {
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
}

interface DebugInfoPanelProps {
  debugInfo: DebugInfo;
  isVisible: boolean;
  onToggle: () => void;
}

const DebugInfoPanel: React.FC<DebugInfoPanelProps> = ({
  debugInfo,
  isVisible,
  onToggle
}) => {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set());

  const toggleSection = (section: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(section)) {
      newExpanded.delete(section);
    } else {
      newExpanded.add(section);
    }
    setExpandedSections(newExpanded);
  };

  const formatDateTime = (dateStr?: string) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleString('zh-CN');
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return 'N/A';
    return `${seconds.toFixed(3)}秒`;
  };

  const calculateCostEstimate = (totalTokens?: number) => {
    if (!totalTokens) return 'N/A';
    // 简单的成本估算（每1000 tokens约0.002美元）
    const cost = (totalTokens / 1000) * 0.002;
    return `$${cost.toFixed(4)}`;
  };

  if (!isVisible) {
    return (
      <div className="fixed bottom-4 right-4 z-50">
        <button
          onClick={onToggle}
          className="bg-blue-600 text-gray-900 px-4 py-2 rounded-lg shadow-lg hover:bg-blue-700 transition-colors"
        >
          <i className="fas fa-bug mr-2"></i>
          调试信息
        </button>
      </div>
    );
  }

  return (
    <div className="fixed bottom-4 right-4 w-96 max-h-96 bg-white border border-gray-300 rounded-lg shadow-xl z-50 overflow-hidden">
      {/* 标题栏 */}
      <div className="bg-white border border-gray-200 shadow-sm text-gray-900 px-4 py-2 flex justify-between items-center">
        <div className="flex items-center">
          <i className="fas fa-bug mr-2"></i>
          <span className="font-medium">AI API 调试信息</span>
        </div>
        <button
          onClick={onToggle}
          className="text-gray-700 hover:text-gray-900 transition-colors"
        >
          <i className="fas fa-times"></i>
        </button>
      </div>

      {/* 内容区域 */}
      <div className="p-4 overflow-y-auto max-h-80">
        {/* 基本信息 */}
        <div className="mb-4">
          <button
            onClick={() => toggleSection('basic')}
            className="flex items-center justify-between w-full text-left font-medium text-gray-800 hover:text-blue-600 transition-colors"
          >
            <span>基本信息</span>
            <i className={`fas fa-chevron-${expandedSections.has('basic') ? 'up' : 'down'}`}></i>
          </button>
          
          {expandedSections.has('basic') && (
            <div className="mt-2 space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">模型:</span>
                <span className="font-mono">{debugInfo.model_name || 'N/A'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">提供商:</span>
                <span className="font-mono">{debugInfo.api_provider || 'N/A'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">请求ID:</span>
                <span className="font-mono text-xs">{debugInfo.request_id || 'N/A'}</span>
              </div>
            </div>
          )}
        </div>

        {/* 时间信息 */}
        <div className="mb-4">
          <button
            onClick={() => toggleSection('timing')}
            className="flex items-center justify-between w-full text-left font-medium text-gray-800 hover:text-blue-600 transition-colors"
          >
            <span>时间信息</span>
            <i className={`fas fa-chevron-${expandedSections.has('timing') ? 'up' : 'down'}`}></i>
          </button>
          
          {expandedSections.has('timing') && (
            <div className="mt-2 space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">调用时间:</span>
                <span className="font-mono text-xs">{formatDateTime(debugInfo.api_call_time)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">响应时间:</span>
                <span className="font-mono text-xs">{formatDateTime(debugInfo.api_response_time)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">耗时:</span>
                <span className={`font-mono ${
                  debugInfo.api_duration && debugInfo.api_duration > 10 ? 'text-red-600' : 'text-green-600'
                }`}>
                  {formatDuration(debugInfo.api_duration)}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Token使用情况 */}
        <div className="mb-4">
          <button
            onClick={() => toggleSection('tokens')}
            className="flex items-center justify-between w-full text-left font-medium text-gray-800 hover:text-blue-600 transition-colors"
          >
            <span>Token 使用</span>
            <i className={`fas fa-chevron-${expandedSections.has('tokens') ? 'up' : 'down'}`}></i>
          </button>
          
          {expandedSections.has('tokens') && (
            <div className="mt-2 space-y-2">
              {/* Token统计 */}
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">输入Token:</span>
                  <span className="font-mono text-blue-600">{debugInfo.prompt_tokens || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">输出Token:</span>
                  <span className="font-mono text-green-600">{debugInfo.completion_tokens || 0}</span>
                </div>
                <div className="flex justify-between font-medium">
                  <span className="text-gray-600">总Token:</span>
                  <span className="font-mono text-purple-600">{debugInfo.total_tokens || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">预估成本:</span>
                  <span className="font-mono text-orange-600">{calculateCostEstimate(debugInfo.total_tokens)}</span>
                </div>
              </div>
              
              {/* Token使用可视化 */}
              {debugInfo.total_tokens && debugInfo.total_tokens > 0 && (
                <div className="mt-3">
                  <div className="text-xs text-gray-600 mb-1">Token分布</div>
                  <div className="flex h-2 bg-gray-200 rounded overflow-hidden">
                    <div 
                      className="bg-blue-500"
                      style={{
                        width: `${((debugInfo.prompt_tokens || 0) / debugInfo.total_tokens) * 100}%`
                      }}
                      title={`输入Token: ${debugInfo.prompt_tokens}`}
                    ></div>
                    <div 
                      className="bg-green-500"
                      style={{
                        width: `${((debugInfo.completion_tokens || 0) / debugInfo.total_tokens) * 100}%`
                      }}
                      title={`输出Token: ${debugInfo.completion_tokens}`}
                    ></div>
                  </div>
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>输入</span>
                    <span>输出</span>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* 模型参数 */}
        <div className="mb-4">
          <button
            onClick={() => toggleSection('params')}
            className="flex items-center justify-between w-full text-left font-medium text-gray-800 hover:text-blue-600 transition-colors"
          >
            <span>模型参数</span>
            <i className={`fas fa-chevron-${expandedSections.has('params') ? 'up' : 'down'}`}></i>
          </button>
          
          {expandedSections.has('params') && (
            <div className="mt-2 space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">温度:</span>
                <span className="font-mono">{debugInfo.temperature || 'N/A'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">最大Token:</span>
                <span className="font-mono">{debugInfo.max_tokens || 'N/A'}</span>
              </div>
              
              {/* 温度可视化 */}
              {debugInfo.temperature !== undefined && (
                <div className="mt-2">
                  <div className="text-xs text-gray-600 mb-1">创造性程度</div>
                  <div className="flex h-2 bg-gray-200 rounded overflow-hidden">
                    <div 
                      className={`h-full ${
                        debugInfo.temperature < 0.3 ? 'bg-blue-500' :
                        debugInfo.temperature < 0.7 ? 'bg-yellow-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${(debugInfo.temperature / 2) * 100}%` }}
                    ></div>
                  </div>
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>保守</span>
                    <span>创新</span>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* 详细调试信息 */}
        {debugInfo.debug_info && (
          <div className="mb-4">
            <button
              onClick={() => toggleSection('detailed')}
              className="flex items-center justify-between w-full text-left font-medium text-gray-800 hover:text-blue-600 transition-colors"
            >
              <span>详细信息</span>
              <i className={`fas fa-chevron-${expandedSections.has('detailed') ? 'up' : 'down'}`}></i>
            </button>
            
            {expandedSections.has('detailed') && (
              <div className="mt-2">
                <pre className="text-xs bg-gray-100 p-2 rounded overflow-x-auto max-h-32">
                  {JSON.stringify(debugInfo.debug_info, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}
      </div>

      {/* 底部状态栏 */}
      <div className="bg-gray-50 px-4 py-2 border-t border-gray-200">
        <div className="flex items-center justify-between text-xs text-gray-600">
          <span>实时调试监控</span>
          <div className="flex items-center">
            <div className="w-2 h-2 bg-green-500 rounded-full mr-1 animate-pulse"></div>
            <span>活跃</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DebugInfoPanel;