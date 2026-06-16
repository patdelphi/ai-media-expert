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
from app.core.security import decrypt_value
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

    def supports_video_understanding_model(self, model_name: Optional[str]) -> bool:
        """判断模型是否支持直接接收视频内容。"""
        if not model_name:
            return False

        normalized_model = model_name.lower()
        return normalized_model in {"glm-4.5v", "glm-4v", "mimo-v2.5"}

    def _update_debug_info(self, analysis: VideoAnalysis, **updates: Any) -> None:
        """通过重新赋值的方式更新 JSON 调试信息，确保 ORM 能持久化变更。"""
        merged_debug_info = dict(analysis.debug_info or {})
        merged_debug_info.update(updates)
        analysis.debug_info = merged_debug_info

    def _sanitize_request_data_for_debug(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """裁剪调试信息中的超长字段，避免 Base64 请求撑爆数据库。"""
        sanitized_request_data: Dict[str, Any] = {
            "model": request_data.get("model"),
            "temperature": request_data.get("temperature"),
            "stream": request_data.get("stream"),
        }

        if "max_tokens" in request_data:
            sanitized_request_data["max_tokens"] = request_data.get("max_tokens")
        if "max_completion_tokens" in request_data:
            sanitized_request_data["max_completion_tokens"] = request_data.get("max_completion_tokens")

        sanitized_messages = []
        for message in request_data.get("messages", []):
            sanitized_message: Dict[str, Any] = {"role": message.get("role")}
            content = message.get("content")

            if isinstance(content, str):
                sanitized_message["content"] = content
            elif isinstance(content, list):
                sanitized_content = []
                for item in content:
                    if not isinstance(item, dict):
                        sanitized_content.append(item)
                        continue

                    sanitized_item = dict(item)
                    video_url = ((sanitized_item.get("video_url") or {}).get("url"))
                    if isinstance(video_url, str) and video_url.startswith("data:"):
                        sanitized_item["video_url"] = {
                            "url": f"{video_url[:64]}... [length={len(video_url)}]"
                        }
                    sanitized_content.append(sanitized_item)
                sanitized_message["content"] = sanitized_content
            else:
                sanitized_message["content"] = content

            sanitized_messages.append(sanitized_message)

        sanitized_request_data["messages"] = sanitized_messages
        return sanitized_request_data

    def _build_openai_compatible_request(
        self,
        ai_config: AIConfig,
        prompt: str,
        analysis: VideoAnalysis,
    ) -> Dict[str, Any]:
        """构建 OpenAI 兼容请求体，并兼容不同供应商的视频参数差异。"""
        normalized_model = (ai_config.model or "").lower()
        supports_video = self.supports_video_understanding_model(ai_config.model)
        video_content = self._prepare_video_content(analysis, ai_config.model) if supports_video else None

        if video_content:
            api_logger.info(f"Using video understanding mode with {video_content['type']}")
            user_content: Any = [
                video_content,
                {
                    "type": "text",
                    "text": prompt,
                },
            ]
        elif supports_video:
            transmission_method = getattr(analysis, "transmission_method", "url")
            raise ValueError(
                f"视频模型 {ai_config.model} 未能生成有效的视频内容，当前传输方式为 {transmission_method}"
            )
        else:
            user_content = prompt

        request_data: Dict[str, Any] = {
            "model": ai_config.model,
            "messages": [
                {
                    "role": "user",
                    "content": user_content,
                }
            ],
            "temperature": ai_config.temperature or 0.7,
            "stream": True,
        }

        if normalized_model.startswith("mimo"):
            request_data["max_completion_tokens"] = ai_config.max_tokens or 4000
        else:
            request_data["max_tokens"] = ai_config.max_tokens or 4000

        if normalized_model in {"glm-4.5v", "glm-4v"}:
            request_data["thinking"] = {
                "type": "enabled"
            }

        return request_data
    
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
            self._update_debug_info(analysis, **initial_debug_info)
            
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
        
        # 构建请求URL：尊重配置中的完整地址，不再自动拼接路径
        api_url = ai_config.api_base or "https://api.openai.com/v1/chat/completions"
        
        # 构建请求头
        api_key = ai_config.api_key
        if api_key and api_key.startswith("enc:"):
            api_key = decrypt_value(api_key[4:])

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        request_data = self._build_openai_compatible_request(ai_config, prompt, analysis)
        debug_request_data = self._sanitize_request_data_for_debug(request_data)
        
        # 生成curl命令用于调试
        curl_headers = []
        for key, value in headers.items():
            if key.lower() == 'authorization':
                curl_headers.append(f'-H "{key}: Bearer ***"')  # 隐藏API密钥
            else:
                curl_headers.append(f'-H "{key}: {value}"')
        
        curl_command = f"curl -X POST {api_url} {' '.join(curl_headers)} -d '{json.dumps(debug_request_data, ensure_ascii=False)}'"
        
        # 更新调试信息
        self._update_debug_info(
            analysis,
            api_url=api_url,
            curl_command=curl_command,
            request_headers={k: ("***" if k.lower() == "authorization" else v) for k, v in headers.items()},
            request_data=debug_request_data,
            status="sending_request",
        )
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
                    self._update_debug_info(
                        analysis,
                        status="error",
                        error_code=response.status_code,
                        error_message=error_msg,
                        response_headers=dict(response.headers),
                    )
                    db.commit()
                    
                    raise Exception(error_msg)
                
                # 记录API响应开始时间
                analysis.api_response_time = datetime.now()
                
                # 更新调试信息
                self._update_debug_info(
                    analysis,
                    status="receiving_response",
                    response_status_code=response.status_code,
                    response_headers=dict(response.headers),
                    response_start_time=analysis.api_response_time.isoformat(),
                )
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
                                    if not isinstance(content_chunk, str) or not content_chunk:
                                        continue

                                    full_content += content_chunk
                                    completion_tokens += len(content_chunk) // 4  # 粗略估算
                                    
                                    # 更新分析结果和实时统计
                                    analysis.completion_tokens = completion_tokens
                                    analysis.total_tokens = analysis.prompt_tokens + completion_tokens
                                    
                                    # 更新实时调试信息（保留之前的信息）
                                    existing_debug_info = dict(analysis.debug_info or {})
                                    self._update_debug_info(
                                        analysis,
                                        status="streaming",
                                        current_content_length=len(full_content),
                                        current_completion_tokens=completion_tokens,
                                        current_total_tokens=analysis.total_tokens,
                                        last_chunk_time=datetime.now().isoformat(),
                                        chunks_received=existing_debug_info.get("chunks_received", 0) + 1,
                                    )
                                    
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
                }
                
                # 合并调试信息，保留之前的curl命令、api_url等重要信息
                if not analysis.debug_info:
                    final_debug_info.update({
                        "api_url": api_url,
                        "curl_command": "调试信息在流式处理中丢失"
                    })
                self._update_debug_info(analysis, **final_debug_info)
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
        api_key = ai_config.api_key
        if api_key and api_key.startswith("enc:"):
            api_key = decrypt_value(api_key[4:])

        headers = {
            "x-api-key": api_key,
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
    
    def _prepare_video_content(self, analysis: VideoAnalysis, model_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """根据传输方式准备视频内容
        
        Args:
            analysis: 视频分析任务对象
            
        Returns:
            视频内容字典，包含type和相应的数据
        """
        try:
            transmission_method = getattr(analysis, 'transmission_method', 'url')
            api_logger.info(f"使用传输方式: {transmission_method}")
            normalized_model = (model_name or "").lower()
            
            if transmission_method == 'url':
                # URL方式
                video_url = getattr(analysis, 'runtime_video_url', None) or getattr(analysis, 'video_url', None)
                if video_url:
                    api_logger.info("使用URL方式发送受保护媒体流")
                    video_content = {
                        "type": "video_url",
                        "video_url": {
                            "url": video_url
                        }
                    }
                    if normalized_model.startswith("mimo"):
                        video_content["fps"] = 2
                        video_content["media_resolution"] = "default"
                    return video_content
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
                        mime_type = video_base64_encoder.get_mime_type(video_file_path)
                        # 构建data URL格式，符合 Mimo / GLM 视频输入要求
                        data_url = f"data:{mime_type};base64,{base64_data}"
                        video_content = {
                            "type": "video_url",
                            "video_url": {
                                "url": data_url
                            }
                        }
                        if normalized_model.startswith("mimo"):
                            video_content["fps"] = 2
                            video_content["media_resolution"] = "default"
                        return video_content
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
