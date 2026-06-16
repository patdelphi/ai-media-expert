"""AI服务模块

实现与各种AI服务提供商的集成，包括OpenAI、Anthropic等。
提供统一的AI API调用接口。
"""

import ipaddress
import json
import os
import time
from datetime import datetime
from typing import Any, Dict, Generator, Optional, Tuple
from urllib.parse import urlparse

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
        # 给 Qwen 预留一点安全余量，避免贴着接口上限发请求。
        self.qwen_max_video_string_length = 27_500_000
        self.qwen_max_raw_file_size = int((self.qwen_max_video_string_length - 256) * 3 / 4)
        self.qwen_compression_target_mb = 18.0

    def _is_qwen_video_model(self, normalized_model: str) -> bool:
        """判断百炼 Qwen 系列模型是否支持图像/视频输入。"""
        # 先排除明确的纯文本模型，避免把 qwen-plus 误判成视频模型。
        if normalized_model in {
            "qwen-plus",
            "qwen-flash",
            "qwen-max",
            "qwen3.7-max",
            "qwen3-max",
            "qwen3-coder-plus",
            "qwen3-coder-flash",
            "qwen3-coder-next",
        }:
            return False

        qwen_video_prefixes = (
            "qwen3.7-plus",
            "qwen3.6-plus",
            "qwen3.6-flash",
            "qwen3.5-plus",
            "qwen3.5-flash",
            "qwen3.5-omni-plus",
            "qwen3-vl-",
            "qwen-vl-",
            "qwen2.5-vl-",
            "qvq-",
        )
        return normalized_model.startswith(qwen_video_prefixes)

    def supports_video_understanding_model(self, model_name: Optional[str]) -> bool:
        """判断模型是否支持直接接收视频内容。"""
        if not model_name:
            return False

        normalized_model = model_name.lower()
        return normalized_model in {"glm-4.5v", "glm-4v", "mimo-v2.5"} or self._is_qwen_video_model(normalized_model)

    def _is_publicly_accessible_url(self, video_url: Optional[str]) -> bool:
        """判断视频 URL 是否可能被远端模型服务访问。"""
        if not isinstance(video_url, str) or not video_url.startswith(("http://", "https://")):
            return False

        parsed_url = urlparse(video_url)
        hostname = (parsed_url.hostname or "").strip().lower()
        if not hostname:
            return False

        if hostname in {"localhost", "127.0.0.1", "0.0.0.0", "::1"} or hostname.endswith(".local"):
            return False

        try:
            ip_address = ipaddress.ip_address(hostname)
        except ValueError:
            return True

        return not (
            ip_address.is_private
            or ip_address.is_loopback
            or ip_address.is_link_local
            or ip_address.is_multicast
            or ip_address.is_unspecified
        )

    def _build_video_url_content(self, video_url: str, normalized_model: str) -> Dict[str, Any]:
        """构建统一的视频 URL 请求块。"""
        video_content: Dict[str, Any] = {
            "type": "video_url",
            "video_url": {
                "url": video_url
            }
        }
        if normalized_model.startswith("mimo"):
            video_content["fps"] = 2
            video_content["media_resolution"] = "default"
        return video_content

    def _supports_dashscope_temp_upload(self, ai_config: Optional[AIConfig]) -> bool:
        """判断当前 AI 配置是否支持百炼临时文件上传。"""
        if not ai_config or not ai_config.api_base:
            return False

        hostname = (urlparse(ai_config.api_base).hostname or "").lower()
        return hostname in {"dashscope.aliyuncs.com", "coding.dashscope.aliyuncs.com"}

    def _decrypt_config_secret(self, stored_secret: Optional[str], field_name: str) -> str:
        """解密配置中的敏感字段，并统一输出清晰错误。"""
        if not stored_secret:
            raise ValueError(f"{field_name} 未配置")

        if stored_secret.startswith("enc:"):
            try:
                return decrypt_value(stored_secret[4:])
            except Exception as exc:
                raise ValueError(f"{field_name} 无法解密，请重新填写") from exc
        return stored_secret

    def _uses_oss_temp_url(self, request_data: Dict[str, Any]) -> bool:
        """判断请求体中是否使用了 oss:// 临时 URL。"""
        for message in request_data.get("messages", []):
            content = message.get("content")
            if not isinstance(content, list):
                continue

            for item in content:
                if not isinstance(item, dict):
                    continue

                video_url = ((item.get("video_url") or {}).get("url"))
                if isinstance(video_url, str) and video_url.startswith("oss://"):
                    return True
        return False

    async def _upload_file_to_dashscope_temp_url(
        self,
        ai_config: AIConfig,
        video_file_path: str,
        analysis: Optional[VideoAnalysis] = None,
    ) -> str:
        """上传本地视频到百炼临时存储，并返回 oss:// 临时 URL。"""
        if not self._supports_dashscope_temp_upload(ai_config):
            raise ValueError("当前 AI 配置不支持百炼临时文件上传，请改用百炼兼容接口配置")

        if not os.path.exists(video_file_path):
            raise ValueError(f"上传文件不存在: {video_file_path}")

        upload_api_key = self._decrypt_config_secret(getattr(ai_config, "upload_api_key", None), "Qwen 上传专用 API Key")

        upload_api_url = "https://dashscope.aliyuncs.com/api/v1/uploads"
        policy_headers = {
            "Authorization": f"Bearer {upload_api_key}",
            "Content-Type": "application/json",
        }
        policy_params = {
            "action": "getPolicy",
            "model": ai_config.model,
        }

        api_logger.info(f"开始请求百炼上传凭证: model={ai_config.model}")
        if analysis is not None:
            self._update_debug_info(
                analysis,
                upload_api_url=upload_api_url,
                upload_key_source="upload_api_key",
            )
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            policy_response = await client.get(upload_api_url, headers=policy_headers, params=policy_params)
            if policy_response.status_code != 200:
                raise ValueError(f"获取百炼上传凭证失败（upload_api_key）: {policy_response.status_code} - {policy_response.text}")

            policy_payload = policy_response.json()
            policy_data = policy_payload.get("data") or {}
            required_fields = {"upload_host", "upload_dir", "oss_access_key_id", "policy", "signature"}
            missing_fields = sorted(field for field in required_fields if not policy_data.get(field))
            if missing_fields:
                raise ValueError(f"百炼上传凭证缺少必要字段: {', '.join(missing_fields)}")

            file_name = os.path.basename(video_file_path)
            oss_key = f"{str(policy_data['upload_dir']).rstrip('/')}/{file_name}"
            form_data = {
                "OSSAccessKeyId": policy_data["oss_access_key_id"],
                "Signature": policy_data["signature"],
                "policy": policy_data["policy"],
                "key": oss_key,
                "success_action_status": "200",
            }

            # 文档中的 x_oss_* 字段需要原样转换成 OSS 表单字段。
            for key, value in policy_data.items():
                if key.startswith("x_oss_") and value:
                    form_data[key.replace("_", "-")] = value

            mime_type = video_base64_encoder.get_mime_type(video_file_path)
            with open(video_file_path, "rb") as video_file:
                upload_response = await client.post(
                    policy_data["upload_host"],
                    data=form_data,
                    files={"file": (file_name, video_file, mime_type)},
                )

            if upload_response.status_code != 200:
                raise ValueError(f"上传视频到百炼临时存储失败: {upload_response.status_code} - {upload_response.text}")

        oss_url = f"oss://{oss_key}"
        api_logger.info(f"百炼临时上传成功: {oss_url}")
        return oss_url

    def _prepare_qwen_base64_data_url(self, video_file_path: str) -> str:
        """为 Qwen 视频模型准备受限长度的 Base64 Data URL。"""
        source_video_path = video_file_path
        temporary_video_path: Optional[str] = None

        try:
            file_size = os.path.getsize(source_video_path)
            if file_size > self.qwen_max_raw_file_size:
                if video_base64_encoder.check_ffmpeg_available():
                    api_logger.info("Qwen Base64 可能超限，尝试压缩视频后再编码")
                    compressed_path = video_base64_encoder.compress_video(
                        source_video_path,
                        target_size_mb=self.qwen_compression_target_mb,
                    )
                    if compressed_path and compressed_path != source_video_path:
                        source_video_path = compressed_path
                        temporary_video_path = compressed_path
                        file_size = os.path.getsize(source_video_path)

            if file_size > self.qwen_max_raw_file_size:
                raise ValueError(
                    f"Qwen Base64 超限：当前视频约 {file_size / (1024 * 1024):.2f}MB，"
                    f"建议配置 PUBLIC_BASE_URL/NGROK_URL 改走公网 URL，或先压缩视频后重试"
                )

            base64_data = video_base64_encoder.encode_video_to_base64(source_video_path, compress=False)
            if not base64_data:
                raise ValueError("Qwen Base64 编码失败")

            mime_type = video_base64_encoder.get_mime_type(source_video_path)
            data_url = f"data:{mime_type};base64,{base64_data}"
            if len(data_url) > self.qwen_max_video_string_length:
                raise ValueError(
                    f"Qwen Base64 超限：编码后长度 {len(data_url)}，"
                    f"已超过安全上限 {self.qwen_max_video_string_length}，请改用公网 URL 或压缩视频"
                )
            return data_url
        finally:
            if temporary_video_path and os.path.exists(temporary_video_path):
                try:
                    os.remove(temporary_video_path)
                except OSError as exc:
                    api_logger.warning(f"清理 Qwen 临时压缩文件失败: {exc}")

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

    async def _build_openai_compatible_request(
        self,
        ai_config: AIConfig,
        prompt: str,
        analysis: VideoAnalysis,
    ) -> Dict[str, Any]:
        """构建 OpenAI 兼容请求体，并兼容不同供应商的视频参数差异。"""
        normalized_model = (ai_config.model or "").lower()
        supports_video = self.supports_video_understanding_model(ai_config.model)
        video_content = await self._prepare_video_content(analysis, ai_config.model, ai_config) if supports_video else None

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
        
        request_data = await self._build_openai_compatible_request(ai_config, prompt, analysis)
        if self._uses_oss_temp_url(request_data):
            headers["X-DashScope-OssResourceResolve"] = "enable"
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
    
    async def _prepare_video_content(
        self,
        analysis: VideoAnalysis,
        model_name: Optional[str] = None,
        ai_config: Optional[AIConfig] = None,
    ) -> Optional[Dict[str, Any]]:
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
            is_qwen_video_model = self._is_qwen_video_model(normalized_model)
            video_url = getattr(analysis, 'runtime_video_url', None) or getattr(analysis, 'video_url', None)
            
            if transmission_method == 'url':
                # URL方式
                if video_url:
                    if is_qwen_video_model and not self._is_publicly_accessible_url(video_url):
                        api_logger.warning("Qwen 选择了 URL 方式，但当前视频地址不是公网可访问地址，回退到 Base64")
                        transmission_method = 'base64'
                    else:
                        api_logger.info("使用URL方式发送受保护媒体流")
                        return self._build_video_url_content(video_url, normalized_model)
                else:
                    api_logger.warning("URL方式选择但未找到video_url，回退到Base64")
                    transmission_method = 'base64'  # 回退到Base64

            if transmission_method == 'base64':
                if is_qwen_video_model and video_url and self._is_publicly_accessible_url(video_url):
                    api_logger.info("Qwen 检测到公网视频地址，优先使用 URL 方式避免 Base64 超限")
                    return self._build_video_url_content(video_url, normalized_model)

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
                    if is_qwen_video_model:
                        data_url = self._prepare_qwen_base64_data_url(video_file_path)
                    else:
                        base64_data = video_base64_encoder.encode_video_to_base64(video_file_path, compress=True)
                        if not base64_data:
                            api_logger.error("Base64编码失败")
                            return None
                        api_logger.info("Base64编码成功")
                        mime_type = video_base64_encoder.get_mime_type(video_file_path)
                        # 构建data URL格式，符合 Mimo / GLM 视频输入要求
                        data_url = f"data:{mime_type};base64,{base64_data}"

                    if data_url:
                        if is_qwen_video_model:
                            api_logger.info("Qwen Base64 编码成功，长度已通过本地限制校验")
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
                    api_logger.warning("Base64方式选择但未找到video_file_path")
                    return None
            
            if transmission_method == 'upload':
                video_file_path = getattr(analysis, 'video_file_path', None)
                if not video_file_path:
                    raise ValueError("文件上传方式未找到本地视频文件")
                if not ai_config:
                    raise ValueError("文件上传方式缺少 AI 配置")

                if not self._supports_dashscope_temp_upload(ai_config):
                    raise ValueError("当前 AI 配置暂不支持百炼临时文件上传，请改用 URL 或 Base64")
                if not self._is_qwen_video_model(normalized_model):
                    raise ValueError("文件上传专用 Key 目前仅支持 Qwen 视频模型")
                if not getattr(ai_config, "upload_api_key", None):
                    raise ValueError("Qwen 文件上传缺少上传专用 API Key，请先在系统设置中填写")

                api_logger.info(f"使用百炼临时文件上传方式: {video_file_path}")
                oss_url = await self._upload_file_to_dashscope_temp_url(ai_config, video_file_path, analysis)
                return self._build_video_url_content(oss_url, normalized_model)
            
            api_logger.warning(f"未知的传输方式: {transmission_method}")
            return None
            
        except ValueError:
            raise
        except Exception as e:
            api_logger.error(f"准备视频内容失败: {e}")
            return None


# 创建AI服务实例
ai_service = AIService()
