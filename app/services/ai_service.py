"""AI服务模块

实现与各种AI服务提供商的集成，包括OpenAI、Anthropic等。
提供统一的AI API调用接口。
"""

import json
import time
from datetime import datetime
from typing import Any, Dict, Generator, Optional, Tuple

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.app_logging import api_logger
from app.models.video import AIConfig
from app.models.video_analysis import VideoAnalysis
from app.utils.video_base64 import video_base64_encoder


class AIService:
    """AI服务类
    
    负责与各种AI服务提供商进行交互，包括：
    - OpenAI GPT系列模型
    - Anthropic Claude系列模型
    - 其他兼容OpenAI API的服务
    """
    
    def __init__(self):
        self.timeout = 300  # 5分钟超时
        self.max_retries = 3
    
    async def call_ai_api(
        self,
        ai_config: AIConfig,
        prompt: str,
        analysis: VideoAnalysis,
        db: Session
    ) -> Generator[str, None, None]:
        """调用AI API进行视频解析
        
        Args:
            ai_config: AI配置信息
            prompt: 提示词内容
            analysis: 解析任务对象
            db: 数据库会话
            
        Yields:
            str: 流式返回的内容片段
        """
        api_call_start = datetime.now()
        
        try:
            # 记录API调用开始时间和基本信息
            analysis.api_call_time = api_call_start
            analysis.temperature = ai_config.temperature or 0.7
            analysis.max_tokens = ai_config.max_tokens or 4000
            analysis.model_name = ai_config.model
            analysis.api_provider = ai_config.provider
            analysis.request_id = f"req_{analysis.id}_{int(api_call_start.timestamp())}"
            
            # 估算输入Token数（粗略估算：1个Token约4个字符）
            analysis.prompt_tokens = max(50, len(prompt) // 4)
            
            # 初始化或更新调试信息（保留已有信息）
            initial_debug_info = {
                "api_start_time": api_call_start.isoformat(),
                "prompt_length": len(prompt),
                "estimated_input_tokens": analysis.prompt_tokens,
                "ai_config": {
                    "provider": ai_config.provider,
                    "model": ai_config.model,
                    "temperature": analysis.temperature,
                    "max_tokens": analysis.max_tokens
                },
                "status": "initializing"
            }
            
            # 如果已有调试信息，合并而不是覆盖
            if analysis.debug_info:
                analysis.debug_info.update(initial_debug_info)
            else:
                analysis.debug_info = initial_debug_info
            
            db.commit()
            
            # 根据提供商选择调用方法
            if ai_config.provider.lower() in ['openai', 'custom']:
                async for chunk in self._call_openai_compatible_api(
                    ai_config, prompt, analysis, db
                ):
                    yield chunk
            elif ai_config.provider.lower() == 'anthropic':
                async for chunk in self._call_anthropic_api(
                    ai_config, prompt, analysis, db
                ):
                    yield chunk
            else:
                raise ValueError(f"Unsupported AI provider: {ai_config.provider}")
                
        except Exception as e:
            api_logger.error(f"AI API call failed: {str(e)}")
            # 记录错误信息
            analysis.status = "failed"
            analysis.error_message = str(e)
            analysis.error_code = "AI_API_ERROR"
            analysis.api_response_time = datetime.now()
            analysis.api_duration = (datetime.now() - api_call_start).total_seconds()
            db.commit()
            raise
    
    async def _call_openai_compatible_api(
        self,
        ai_config: AIConfig,
        prompt: str,
        analysis: VideoAnalysis,
        db: Session
    ) -> Generator[str, None, None]:
        """调用OpenAI兼容的API"""
        
        # 构建请求URL
        api_base = ai_config.api_base or "https://api.openai.com/v1"
        if not api_base.endswith('/chat/completions'):
            api_url = f"{api_base.rstrip('/')}/chat/completions"
        else:
            api_url = api_base
        
        # 构建请求头
        headers = {
            "Authorization": f"Bearer {ai_config.api_key}",
            "Content-Type": "application/json"
        }
        
        # 构建请求体 - 支持GLM-4.5V的视频分析格式
        if ai_config.model.lower() in ['glm-4.5v', 'glm-4v']:
            # 准备视频内容（URL或Base64）
            video_content = self._prepare_video_content(analysis)
            
            if video_content:
                api_logger.info(f"Using GLM video understanding mode with {video_content['type']}")
                # 包含视频内容的多模态消息格式
                request_data = {
                    "model": ai_config.model,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                video_content,
                                {
                                    "type": "text",
                                    "text": prompt
                                }
                            ]
                        }
                    ],
                    "max_tokens": ai_config.max_tokens or 4000,
                    "temperature": ai_config.temperature or 0.7,
                    "stream": True,
                    "thinking": {
                        "type": "enabled"
                    }
                }
            else:
                api_logger.warning(f"GLM video model {ai_config.model} used without video content, falling back to text mode")
                # 仅文本的消息格式（兼容现有逻辑）
                request_data = {
                    "model": ai_config.model,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": prompt
                                }
                            ]
                        }
                    ],
                    "max_tokens": ai_config.max_tokens or 4000,
                    "temperature": ai_config.temperature or 0.7,
                    "stream": True,
                    "thinking": {
                        "type": "enabled"
                    }
                }
        else:
            # 标准OpenAI格式
            request_data = {
                "model": ai_config.model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": ai_config.max_tokens or 4000,
                "temperature": ai_config.temperature or 0.7,
                "stream": True
            }
        
        # 生成curl命令用于调试
        curl_headers = []
        for key, value in headers.items():
            if key.lower() == 'authorization':
                curl_headers.append(f'-H "{key}: Bearer ***"')  # 隐藏API密钥
            else:
                curl_headers.append(f'-H "{key}: {value}"')
        
        curl_command = f"curl -X POST {api_url} {' '.join(curl_headers)} -d '{json.dumps(request_data, ensure_ascii=False)}'"
        
        # 更新调试信息
        if analysis.debug_info:
            analysis.debug_info.update({
                "api_url": api_url,
                "curl_command": curl_command,
                "request_headers": {k: ("***" if k.lower() == "authorization" else v) for k, v in headers.items()},
                "request_data": request_data,
                "status": "sending_request"
            })
        else:
            analysis.debug_info = {
                "api_url": api_url,
                "curl_command": curl_command,
                "request_headers": {k: ("***" if k.lower() == "authorization" else v) for k, v in headers.items()},
                "request_data": request_data,
                "status": "sending_request"
            }
        db.commit()
        
        api_logger.info(f"Calling OpenAI API: {api_url}")
        api_logger.debug(f"Curl command: {curl_command}")
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                api_url,
                headers=headers,
                json=request_data
            ) as response:
                
                if response.status_code != 200:
                    error_text = await response.aread()
                    error_msg = f"API request failed: {response.status_code} - {error_text.decode()}"
                    
                    # 更新错误调试信息
                    analysis.debug_info.update({
                        "status": "error",
                        "error_code": response.status_code,
                        "error_message": error_msg,
                        "response_headers": dict(response.headers)
                    })
                    db.commit()
                    
                    raise Exception(error_msg)
                
                # 记录API响应开始时间
                analysis.api_response_time = datetime.now()
                
                # 更新调试信息
                if analysis.debug_info:
                    analysis.debug_info.update({
                        "status": "receiving_response",
                        "response_status_code": response.status_code,
                        "response_headers": dict(response.headers),
                        "response_start_time": analysis.api_response_time.isoformat()
                    })
                else:
                    analysis.debug_info = {
                        "status": "receiving_response",
                        "response_status_code": response.status_code,
                        "response_headers": dict(response.headers),
                        "response_start_time": analysis.api_response_time.isoformat()
                    }
                db.commit()
                
                full_content = ""
                completion_tokens = 0
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]  # 移除"data: "前缀
                        
                        if data_str.strip() == "[DONE]":
                            break
                        
                        try:
                            data = json.loads(data_str)
                            
                            if "choices" in data and len(data["choices"]) > 0:
                                choice = data["choices"][0]
                                
                                if "delta" in choice and "content" in choice["delta"]:
                                    content_chunk = choice["delta"]["content"]
                                    full_content += content_chunk
                                    completion_tokens += len(content_chunk) // 4  # 粗略估算
                                    
                                    # 更新分析结果和实时统计
                                    analysis.analysis_result = self._clean_response_content(full_content)
                                    analysis.completion_tokens = completion_tokens
                                    analysis.total_tokens = analysis.prompt_tokens + completion_tokens
                                    
                                    # 更新实时调试信息（保留之前的信息）
                                    if analysis.debug_info:
                                        analysis.debug_info.update({
                                            "status": "streaming",
                                            "current_content_length": len(full_content),
                                            "current_completion_tokens": completion_tokens,
                                            "current_total_tokens": analysis.total_tokens,
                                            "last_chunk_time": datetime.now().isoformat(),
                                            "chunks_received": analysis.debug_info.get("chunks_received", 0) + 1
                                        })
                                    else:
                                        # 如果debug_info为空，初始化基本信息
                                        analysis.debug_info = {
                                            "status": "streaming",
                                            "current_content_length": len(full_content),
                                            "current_completion_tokens": completion_tokens,
                                            "current_total_tokens": analysis.total_tokens,
                                            "last_chunk_time": datetime.now().isoformat(),
                                            "chunks_received": 1,
                                            "api_url": "N/A",
                                            "curl_command": "调试信息初始化时丢失"
                                        }
                                    
                                    db.commit()
                                    
                                    yield content_chunk
                                    
                        except json.JSONDecodeError:
                            continue
                
                # 记录最终的API调用信息
                api_end_time = datetime.now()
                analysis.api_duration = (api_end_time - analysis.api_call_time).total_seconds()
                analysis.completion_tokens = completion_tokens
                analysis.total_tokens = analysis.prompt_tokens + completion_tokens
                
                # 更新调试信息（合并而不是覆盖，保留curl命令等重要信息）
                final_debug_info = {
                    "model": ai_config.model,
                    "provider": ai_config.provider,
                    "api_config": {
                        "temperature": ai_config.temperature,
                        "max_tokens": ai_config.max_tokens,
                        "api_base": ai_config.api_base
                    },
                    "token_usage": {
                        "prompt_tokens": analysis.prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "total_tokens": analysis.prompt_tokens + completion_tokens
                    },
                    "response_info": {
                        "status_code": response.status_code,
                        "content_length": len(full_content),
                        "response_headers": dict(response.headers)
                    },
                    "timing": {
                        "api_call_time": analysis.api_call_time.isoformat(),
                        "api_response_time": analysis.api_response_time.isoformat() if analysis.api_response_time else None,
                        "api_end_time": api_end_time.isoformat(),
                        "total_duration": (api_end_time - analysis.api_call_time).total_seconds(),
                        "api_duration": analysis.api_duration
                    },
                    "status": "completed",
                    "completion_reason": "stream_ended"
                }
                
                # 合并调试信息，保留之前的curl命令、api_url等重要信息
                if analysis.debug_info:
                    analysis.debug_info.update(final_debug_info)
                else:
                    # 如果debug_info为空，添加基本信息
                    final_debug_info.update({
                        "api_url": api_url,
                        "curl_command": "调试信息在流式处理中丢失"
                    })
                    analysis.debug_info = final_debug_info
                
                # 确保所有调试信息字段都被正确设置
                analysis.model_name = ai_config.model
                analysis.api_provider = ai_config.provider
                analysis.temperature = ai_config.temperature
                analysis.max_tokens = ai_config.max_tokens
                analysis.api_duration = (api_end_time - analysis.api_call_time).total_seconds()
                analysis.processing_time = (api_end_time - analysis.api_call_time).total_seconds()
                analysis.completed_at = api_end_time
                
                # 设置token使用统计
                analysis.token_usage = {
                    "prompt_tokens": analysis.prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": analysis.prompt_tokens + completion_tokens,
                    "estimated_cost": self._estimate_cost(ai_config.model, analysis.prompt_tokens + completion_tokens)
                }
                
                db.commit()
                
                api_logger.info(f"OpenAI API call completed successfully. Tokens: {analysis.total_tokens}")
    
    async def _call_anthropic_api(
        self,
        ai_config: AIConfig,
        prompt: str,
        analysis: VideoAnalysis,
        db: Session
    ) -> Generator[str, None, None]:
        """调用Anthropic Claude API"""
        
        # 构建请求URL
        api_base = ai_config.api_base or "https://api.anthropic.com"
        api_url = f"{api_base.rstrip('/')}/v1/messages"
        
        # 构建请求头
        headers = {
            "x-api-key": ai_config.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        # 构建请求体
        request_data = {
            "model": ai_config.model,
            "max_tokens": ai_config.max_tokens or 4000,
            "temperature": ai_config.temperature or 0.7,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "stream": True
        }
        
        api_logger.info(f"Calling Anthropic API: {api_url}")
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                api_url,
                headers=headers,
                json=request_data
            ) as response:
                
                if response.status_code != 200:
                    error_text = await response.aread()
                    raise Exception(f"Anthropic API request failed: {response.status_code} - {error_text.decode()}")
                
                # 记录API响应开始时间
                analysis.api_response_time = datetime.now()
                db.commit()
                
                full_content = ""
                completion_tokens = 0
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        
                        if data_str.strip() == "[DONE]":
                            break
                        
                        try:
                            data = json.loads(data_str)
                            
                            if data.get("type") == "content_block_delta":
                                if "delta" in data and "text" in data["delta"]:
                                    content_chunk = data["delta"]["text"]
                                    full_content += content_chunk
                                    completion_tokens += len(content_chunk) // 4
                                    
                                    # 更新分析结果
                                    analysis.analysis_result = self._clean_response_content(full_content)
                                    analysis.completion_tokens = completion_tokens
                                    analysis.total_tokens = analysis.prompt_tokens + completion_tokens
                                    db.commit()
                                    
                                    yield content_chunk
                                    
                        except json.JSONDecodeError:
                            continue
                
                # 记录最终信息
                api_end_time = datetime.now()
                analysis.api_duration = (api_end_time - analysis.api_call_time).total_seconds()
                analysis.completion_tokens = completion_tokens
                analysis.total_tokens = analysis.prompt_tokens + completion_tokens
                
                debug_info = {
                    "api_url": api_url,
                    "model": ai_config.model,
                    "provider": ai_config.provider,
                    "request_data": {
                        "model": request_data["model"],
                        "max_tokens": request_data["max_tokens"],
                        "temperature": request_data["temperature"]
                    },
                    "response_info": {
                        "status_code": response.status_code,
                        "content_length": len(full_content),
                        "completion_tokens": completion_tokens
                    }
                }
                
                analysis.debug_info = debug_info
                db.commit()
                
                api_logger.info(f"Anthropic API call completed successfully. Tokens: {analysis.total_tokens}")
    
    def _clean_response_content(self, content: str) -> str:
        """清理响应内容中的标记符号
        
        Args:
            content: 原始响应内容
            
        Returns:
            清理后的内容
        """
        if not content:
            return content
            
        # 移除常见的标记符号
        markers_to_remove = [
            "<|begin_of_box|>",
            "<|end_of_box|>",
            "<|box_start|>",
            "<|box_end|>",
            "<|start|>",
            "<|end|>"
        ]
        
        cleaned_content = content
        for marker in markers_to_remove:
            cleaned_content = cleaned_content.replace(marker, "")
        
        # 清理多余的空行
        cleaned_content = "\n".join(line for line in cleaned_content.split("\n") if line.strip())
        
        return cleaned_content.strip()
    
    def _estimate_cost(self, model: str, total_tokens: int) -> float:
        """估算API调用成本
        
        Args:
            model: 模型名称
            total_tokens: 总token数量
            
        Returns:
            预估成本（美元）
        """
        # 基于不同模型的定价（每1K tokens的价格，美元）
        pricing = {
            "gpt-4": 0.03,
            "gpt-4-turbo": 0.01,
            "gpt-3.5-turbo": 0.002,
            "glm-4": 0.001,  # 智谱AI GLM-4
            "glm-4v": 0.002,  # GLM-4V视觉模型
            "glm-4.5v": 0.002,  # GLM-4.5V
            "claude-3-opus": 0.015,
            "claude-3-sonnet": 0.003,
            "claude-3-haiku": 0.00025
        }
        
        # 获取模型价格，默认使用GPT-4价格
        price_per_1k = pricing.get(model.lower(), 0.03)
        
        # 计算成本
        return (total_tokens / 1000) * price_per_1k
    
    def _prepare_video_content(self, analysis: VideoAnalysis) -> Optional[Dict[str, Any]]:
        """根据传输方式准备视频内容
        
        Args:
            analysis: 视频分析任务对象
            
        Returns:
            视频内容字典，包含type和相应的数据
        """
        try:
            transmission_method = getattr(analysis, 'transmission_method', 'url')
            api_logger.info(f"使用传输方式: {transmission_method}")
            
            if transmission_method == 'url':
                # URL方式
                video_url = getattr(analysis, 'video_url', None)
                if video_url:
                    api_logger.info(f"使用URL方式: {video_url}")
                    return {
                        "type": "video_url",
                        "video_url": {
                            "url": video_url
                        }
                    }
                else:
                    api_logger.warning("URL方式选择但未找到video_url，回退到Base64")
                    transmission_method = 'base64'  # 回退到Base64
            
            if transmission_method == 'base64':
                # Base64编码方式
                video_file_path = getattr(analysis, 'video_file_path', None)
                if video_file_path:
                    api_logger.info(f"使用Base64编码方式: {video_file_path}")
                    
                    # 检查文件是否适合Base64编码
                    suitable, reason = video_base64_encoder.is_suitable_for_base64(video_file_path)
                    if not suitable:
                        api_logger.warning(f"文件不适合Base64编码: {reason}")
                        return None
                    
                    # 编码视频文件
                    base64_data = video_base64_encoder.encode_video_to_base64(video_file_path, compress=True)
                    if base64_data:
                        api_logger.info("Base64编码成功")
                        # 构建data URL格式，符合GLM API要求
                        data_url = f"data:video/mp4;base64,{base64_data}"
                        return {
                            "type": "video_url",
                            "video_url": {
                                "url": data_url
                            }
                        }
                    else:
                        api_logger.error("Base64编码失败")
                        return None
                else:
                    api_logger.warning("Base64方式选择但未找到video_file_path")
                    return None
            
            if transmission_method == 'upload':
                # 文件上传方式（暂未实现）
                api_logger.warning("文件上传方式暂未实现")
                return None
            
            api_logger.warning(f"未知的传输方式: {transmission_method}")
            return None
            
        except Exception as e:
            api_logger.error(f"准备视频内容失败: {e}")
            return None


# 创建AI服务实例
ai_service = AIService()