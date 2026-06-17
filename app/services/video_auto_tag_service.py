"""自动打标服务

负责自动打标任务创建、模型调用、结构化结果解析与当前有效标签同步。
"""

from __future__ import annotations

import json
import os
import re
import time
from typing import Any, Dict, Optional

import httpx
from sqlalchemy.orm import Session

from app.core.app_logging import api_logger
from app.core.config import settings
from app.core.security import create_media_access_token, utcnow
from app.models.tag_group import TagGroup
from app.models.uploaded_file import UploadedFile
from app.models.user import User
from app.models.video import AIConfig, Tag
from app.models.video_auto_tag import (
    UploadedFileTag,
    UploadedFileTagRevision,
    UploadedFileTagRevisionItem,
    VideoAutoTagItem,
    VideoAutoTagTask,
)
from app.services.ai_service import ai_service


class VideoAutoTagService:
    """自动打标服务实现。"""

    prompt_version = "auto-tag-v1"
    free_tag_promotion_threshold = 0.8

    def create_task(
        self,
        *,
        db: Session,
        current_user: User,
        video_file: UploadedFile,
        ai_config: AIConfig,
        tag_group_ids: Optional[list[int]],
        transmission_method: str,
    ) -> VideoAutoTagTask:
        """创建自动打标任务。"""
        active_groups = self._load_tag_groups(db, tag_group_ids)
        prompt_content = self._build_prompt(active_groups)
        resolved_tag_group_ids = [group.id for group in active_groups]

        task = VideoAutoTagTask(
            user_id=str(current_user.id),
            video_file_id=video_file.id,
            ai_config_id=ai_config.id,
            tag_group_ids=resolved_tag_group_ids,
            prompt_version=self.prompt_version,
            prompt_content=prompt_content,
            transmission_method=transmission_method or "url",
            status="pending",
            progress=0,
            is_active=True,
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    async def process_task(self, task_id: int, db: Session) -> None:
        """处理自动打标任务。"""
        task = db.query(VideoAutoTagTask).filter(VideoAutoTagTask.id == task_id).first()
        if not task:
            raise ValueError(f"自动打标任务不存在: {task_id}")

        ai_config = db.query(AIConfig).filter(AIConfig.id == task.ai_config_id, AIConfig.is_active == True).first()
        if not ai_config:
            self._mark_task_failed(db, task, "AI config not found or inactive")
            return

        video_file = db.query(UploadedFile).filter(UploadedFile.id == task.video_file_id).first()
        if not video_file:
            self._mark_task_failed(db, task, "Video file not found")
            return

        if not video_file.file_path or not os.path.exists(video_file.file_path):
            self._mark_task_failed(db, task, "Video file is not available on disk")
            return

        if not ai_service.supports_video_understanding_model(ai_config.model):
            self._mark_task_failed(db, task, f"当前模型不支持视频自动打标: {ai_config.model}")
            return

        task.status = "processing"
        task.progress = 10
        task.started_at = utcnow().isoformat()
        task.video_file_path = video_file.file_path
        db.commit()

        process_started = time.perf_counter()

        try:
            self._prepare_video_access(task, video_file)
            task.progress = 30
            db.commit()

            result = await self._call_structured_tagging_api(ai_config=ai_config, task=task)
            task.progress = 60
            task.request_payload_summary = result["request_payload_summary"]
            task.raw_response = result["raw_response_text"]
            task.structured_summary = result["structured_payload"].get("summary")
            task.result_metadata = {
                "library_tag_count": len(result["structured_payload"].get("library_tags", [])),
                "free_tag_count": len(result["structured_payload"].get("free_tags", [])),
                "model": ai_config.model,
                "provider": ai_config.provider,
            }
            task.token_usage = result.get("token_usage")
            task.cost_estimate = result.get("cost_estimate")
            db.commit()

            self._replace_task_items(db, task, result["structured_payload"])
            task.progress = 80
            db.commit()

            self._sync_effective_tags(db, task)

            task.status = "completed"
            task.progress = 100
            task.processing_time = round(time.perf_counter() - process_started, 3)
            task.completed_at = utcnow().isoformat()
            db.commit()
        except Exception as exc:
            self._mark_task_failed(db, task, str(exc))
            raise

    def _load_tag_groups(self, db: Session, tag_group_ids: Optional[list[int]]) -> list[TagGroup]:
        """加载有效标签组。"""
        query = db.query(TagGroup).filter(TagGroup.is_active == True)
        if tag_group_ids:
            query = query.filter(TagGroup.id.in_(tag_group_ids))
        return query.order_by(TagGroup.id.asc()).all()

    def _build_prompt(self, tag_groups: list[TagGroup]) -> str:
        """构建自动打标提示词。"""
        tag_lines: list[str] = []
        for group in tag_groups:
            for tag in group.tags:
                if not tag.is_active:
                    continue
                tag_lines.append(f'- {{"tag_group_tag_id": {tag.id}, "tag_group_id": {group.id}, "group_name": "{group.name}", "tag_name": "{tag.name}"}}')

        library_section = "\n".join(tag_lines) if tag_lines else "- 没有预设标签，请只输出 free_tags"
        return (
            "你是视频自动打标助手。\n"
            "请直接读取视频内容，并仅输出合法 JSON，不要输出 Markdown，不要输出解释性文字。\n\n"
            "目标：\n"
            "1. 从固定标签库中命中最合适的标签\n"
            "2. 在固定标签不够时补充 free_tags\n"
            "3. 为每个标签给出 confidence、reason、evidence\n\n"
            "固定标签库：\n"
            f"{library_section}\n\n"
            "输出 JSON 结构必须为：\n"
            "{\n"
            '  "summary": {"overview": "一句话摘要"},\n'
            '  "library_tags": [\n'
            '    {"tag_group_tag_id": 1, "tag_name": "示例", "confidence": 0.95, "reason": "命中原因", "evidence": {"text": "证据文本", "start_seconds": 1.2, "end_seconds": 3.4}}\n'
            "  ],\n"
            '  "free_tags": [\n'
            '    {"tag_name": "自由标签", "confidence": 0.85, "reason": "补充原因", "evidence": {"text": "证据文本", "start_seconds": 4.0, "end_seconds": 6.5}}\n'
            "  ]\n"
            "}\n"
            "要求：\n"
            "- confidence 范围必须是 0 到 1\n"
            "- 如果没有命中的固定标签，library_tags 返回空数组\n"
            "- 如果没有自由标签，free_tags 返回空数组\n"
        )

    def _prepare_video_access(self, task: VideoAutoTagTask, video_file: UploadedFile) -> None:
        """为自动打标任务准备可访问视频地址。"""
        filename = os.path.basename(video_file.file_path)
        base_url = settings.get_base_url()
        media_token = create_media_access_token(
            subject=video_file.user_id,
            saved_filename=filename,
        )
        task.video_url = f"{base_url}/api/v1/files/stream/{filename}"
        task.runtime_video_url = f"{base_url}/api/v1/files/stream/{filename}?token={media_token}"

    async def _call_structured_tagging_api(self, *, ai_config: AIConfig, task: VideoAutoTagTask) -> dict[str, Any]:
        """调用模型执行自动打标。"""
        if ai_config.provider.lower() not in {"openai", "custom"}:
            raise ValueError(f"自动打标当前仅支持 openai/custom 提供商，收到: {ai_config.provider}")

        video_content = await ai_service._prepare_video_content(task, ai_config.model, ai_config)
        if not video_content:
            raise ValueError("自动打标未能生成有效的视频内容")

        api_url = ai_config.api_base or "https://api.openai.com/v1/chat/completions"
        api_key = ai_service._decrypt_config_secret(ai_config.api_key, "自动打标 API Key")

        request_data: Dict[str, Any] = {
            "model": ai_config.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        video_content,
                        {
                            "type": "text",
                            "text": task.prompt_content,
                        },
                    ],
                }
            ],
            # 自动打标属于结构化分类场景，固定为低温度以降低重复打标抖动。
            "temperature": 0,
            "max_tokens": ai_config.max_tokens or 1200,
            "stream": False,
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        if ai_service._uses_oss_temp_url(request_data):
            headers["X-DashScope-OssResourceResolve"] = "enable"

        debug_request = ai_service._sanitize_request_data_for_debug(request_data)
        task.debug_info = {
            "api_url": api_url,
            "request_data": debug_request,
            "provider": ai_config.provider,
            "model": ai_config.model,
        }

        async with httpx.AsyncClient(timeout=ai_service.timeout) as client:
            response = await client.post(api_url, headers=headers, json=request_data)
            if response.status_code != 200:
                raise ValueError(f"自动打标 API 调用失败: {response.status_code} - {response.text}")
            payload = response.json()

        raw_response_text = self._extract_response_text(payload)
        structured_payload = self._extract_structured_payload(raw_response_text)
        self._validate_payload(structured_payload)

        return {
            "raw_response_text": raw_response_text,
            "structured_payload": structured_payload,
            "request_payload_summary": debug_request,
            "token_usage": payload.get("usage"),
            "cost_estimate": None,
        }

    def _extract_response_text(self, payload: dict[str, Any]) -> str:
        """从 OpenAI 兼容响应中提取文本。"""
        choices = payload.get("choices") or []
        if not choices:
            raise ValueError("自动打标响应缺少 choices")

        message = choices[0].get("message") or {}
        content = message.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
            if text_parts:
                return "".join(text_parts)
        raise ValueError("自动打标响应缺少可解析文本内容")

    def _extract_structured_payload(self, raw_response_text: str) -> dict[str, Any]:
        """从原始文本中提取 JSON。"""
        candidate = raw_response_text.strip()
        fenced_match = re.search(r"```json\s*(\{.*\})\s*```", candidate, re.DOTALL | re.IGNORECASE)
        if fenced_match:
            candidate = fenced_match.group(1)
        else:
            braces_match = re.search(r"(\{.*\})", candidate, re.DOTALL)
            if braces_match:
                candidate = braces_match.group(1)

        try:
            return json.loads(candidate)
        except json.JSONDecodeError as exc:
            raise ValueError("自动打标响应不是合法 JSON") from exc

    def _validate_payload(self, payload: dict[str, Any]) -> None:
        """校验自动打标结构化输出。"""
        if not isinstance(payload, dict):
            raise ValueError("自动打标结果格式错误")

        for key in ("library_tags", "free_tags"):
            if key not in payload or not isinstance(payload[key], list):
                raise ValueError(f"自动打标结果缺少数组字段: {key}")

        if "summary" not in payload:
            payload["summary"] = {}

        for tag_item in list(payload.get("library_tags", [])) + list(payload.get("free_tags", [])):
            confidence = float(tag_item.get("confidence", 0.0))
            if confidence < 0 or confidence > 1:
                raise ValueError("自动打标签置信度必须在 0 到 1 之间")

            evidence = tag_item.get("evidence") or {}
            start_seconds = evidence.get("start_seconds")
            end_seconds = evidence.get("end_seconds")
            if start_seconds is not None and end_seconds is not None and float(start_seconds) > float(end_seconds):
                raise ValueError("自动打标签证据时间段非法")

    def _replace_task_items(self, db: Session, task: VideoAutoTagTask, payload: dict[str, Any]) -> None:
        """替换任务命中项。"""
        db.query(VideoAutoTagItem).filter(VideoAutoTagItem.task_id == task.id).delete()

        library_tags = payload.get("library_tags", [])
        free_tags = payload.get("free_tags", [])

        for item in library_tags:
            evidence = item.get("evidence") or {}
            db.add(
                VideoAutoTagItem(
                    task_id=task.id,
                    tag_group_id=item.get("tag_group_id"),
                    tag_name=item["tag_name"],
                    tag_source="library",
                    match_type="ai_detected",
                    confidence=float(item.get("confidence", 0.0)),
                    evidence_text=evidence.get("text"),
                    evidence_start_seconds=evidence.get("start_seconds"),
                    evidence_end_seconds=evidence.get("end_seconds"),
                    reason=item.get("reason"),
                    is_promoted=True,
                    is_active=True,
                )
            )

        for item in free_tags:
            evidence = item.get("evidence") or {}
            confidence = float(item.get("confidence", 0.0))
            db.add(
                VideoAutoTagItem(
                    task_id=task.id,
                    tag_name=item["tag_name"],
                    tag_source="free",
                    match_type="ai_detected",
                    confidence=confidence,
                    evidence_text=evidence.get("text"),
                    evidence_start_seconds=evidence.get("start_seconds"),
                    evidence_end_seconds=evidence.get("end_seconds"),
                    reason=item.get("reason"),
                    is_promoted=confidence >= self.free_tag_promotion_threshold,
                    is_active=True,
                )
            )
        db.commit()

    def _sync_effective_tags(self, db: Session, task: VideoAutoTagTask) -> None:
        """同步当前有效标签。

        当前有效标签语义：
        - 默认等于“历史上出现过的所有标签并集”
        - 若用户手动移除，则该标签保持在历史集合中，但不再是当前生效标签
        """
        current_items = (
            db.query(UploadedFileTag)
            .filter(
                UploadedFileTag.video_file_id == task.video_file_id,
                UploadedFileTag.is_effective == True,
            )
            .order_by(UploadedFileTag.id.asc())
            .all()
        )
        current_map = {
            item.tag_name_snapshot: {
                "tag_id": item.tag_id,
                "tag_name": item.tag_name_snapshot,
                "confidence": item.confidence,
                "reason": item.reason,
                "evidence_start_seconds": item.evidence_start_seconds,
                "evidence_end_seconds": item.evidence_end_seconds,
                "source": item.source,
                "created_by": item.created_by,
            }
            for item in current_items
        }

        excluded_tag_names = self._load_manual_excluded_tags(db=db, video_file_id=task.video_file_id)

        items = (
            db.query(VideoAutoTagItem)
            .filter(VideoAutoTagItem.task_id == task.id, VideoAutoTagItem.is_active == True)
            .order_by(VideoAutoTagItem.id.asc())
            .all()
        )

        for item in items:
            if item.tag_name in excluded_tag_names:
                continue

            tag_record = self._get_or_create_tag(
                db=db,
                tag_name=item.tag_name,
                tag_group_id=item.tag_group_id,
                source_type="library" if item.tag_source == "library" else "free_promoted",
            )
            item.tag_id = tag_record.id
            existing_entry = current_map.get(item.tag_name)
            if existing_entry:
                existing_entry["tag_id"] = existing_entry["tag_id"] or tag_record.id
                if float(item.confidence or 0.0) >= float(existing_entry["confidence"] or 0.0):
                    existing_entry["confidence"] = item.confidence
                    existing_entry["reason"] = item.reason
                    existing_entry["evidence_start_seconds"] = item.evidence_start_seconds
                    existing_entry["evidence_end_seconds"] = item.evidence_end_seconds
                    existing_entry["source"] = "ai_auto"
                    existing_entry["created_by"] = "ai"
                continue

            current_map[item.tag_name] = {
                "tag_id": tag_record.id,
                "tag_name": item.tag_name,
                "confidence": item.confidence,
                "reason": item.reason,
                "evidence_start_seconds": item.evidence_start_seconds,
                "evidence_end_seconds": item.evidence_end_seconds,
                "source": "ai_auto",
                "created_by": "ai",
            }

        db.query(UploadedFileTag).filter(
            UploadedFileTag.video_file_id == task.video_file_id,
            UploadedFileTag.is_effective == True,
        ).update({"is_effective": False}, synchronize_session=False)

        for item in current_map.values():
            db.add(
                UploadedFileTag(
                    video_file_id=task.video_file_id,
                    tag_id=item["tag_id"],
                    tag_name_snapshot=item["tag_name"],
                    source=item["source"],
                    confidence=item["confidence"],
                    auto_tag_task_id=task.id,
                    revision_id=None,
                    is_effective=True,
                    evidence_start_seconds=item["evidence_start_seconds"],
                    evidence_end_seconds=item["evidence_end_seconds"],
                    reason=item["reason"],
                    created_by=item["created_by"],
                )
            )

        db.commit()

    def _load_manual_excluded_tags(self, *, db: Session, video_file_id: int) -> set[str]:
        """加载最新状态为 remove 的人工排除标签。"""
        revision_items = (
            db.query(UploadedFileTagRevisionItem, UploadedFileTagRevision)
            .join(UploadedFileTagRevision, UploadedFileTagRevisionItem.revision_id == UploadedFileTagRevision.id)
            .filter(UploadedFileTagRevision.video_file_id == video_file_id)
            .order_by(UploadedFileTagRevision.id.asc(), UploadedFileTagRevisionItem.id.asc())
            .all()
        )

        latest_action_by_tag: dict[str, str] = {}
        for revision_item, _revision in revision_items:
            tag_name = (revision_item.tag_name or "").strip()
            if not tag_name:
                continue
            latest_action_by_tag[tag_name] = revision_item.action

        return {
            tag_name
            for tag_name, action in latest_action_by_tag.items()
            if action == "remove"
        }

    def _get_or_create_tag(
        self,
        *,
        db: Session,
        tag_name: str,
        tag_group_id: Optional[int],
        source_type: str,
    ) -> Tag:
        """获取或创建正式标签。"""
        tag = db.query(Tag).filter(Tag.name == tag_name).first()
        if tag:
            if tag_group_id and getattr(tag, "tag_group_id", None) is None:
                tag.tag_group_id = tag_group_id
            if getattr(tag, "source_type", None) != "library" and source_type == "library":
                tag.source_type = "library"
            if hasattr(tag, "is_active"):
                tag.is_active = True
            db.commit()
            db.refresh(tag)
            return tag

        tag_group_name = None
        if tag_group_id:
            tag_group = db.query(TagGroup).filter(TagGroup.id == tag_group_id).first()
            tag_group_name = tag_group.name if tag_group else None

        tag = Tag(
            name=tag_name,
            category=tag_group_name or "free",
            description=None,
            color=None,
            source_type=source_type,
            tag_group_id=tag_group_id,
            is_active=True,
        )
        db.add(tag)
        db.commit()
        db.refresh(tag)
        return tag

    def _mark_task_failed(self, db: Session, task: VideoAutoTagTask, message: str) -> None:
        """标记任务失败。"""
        task.status = "failed"
        task.error_message = message
        task.completed_at = utcnow().isoformat()
        task.progress = min(task.progress or 0, 99)
        db.commit()


video_auto_tag_service = VideoAutoTagService()
