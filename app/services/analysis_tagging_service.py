"""解析结果候选标签生成服务

基于某次视频解析任务的文本结果，再调用一次 AI 生成结构化候选标签列表。
"""

from __future__ import annotations

import ast
import json
import re
from typing import Any, Dict, Optional

import httpx
from sqlalchemy.orm import Session

from app.core.app_logging import api_logger
from app.models.tag_group import TagGroup
from app.models.video import AIConfig
from app.models.video_analysis import VideoAnalysis
from app.services.ai_service import ai_service


class AnalysisTaggingService:
    def _extract_openai_compatible_text(self, payload: dict[str, Any]) -> str:
        choices = payload.get("choices") or []
        if not isinstance(choices, list) or not choices:
            raise ValueError("解析结果打标响应缺少 choices")

        choice = choices[0] if isinstance(choices[0], dict) else {}

        message = choice.get("message")
        if isinstance(message, dict):
            content = message.get("content")
            if isinstance(content, str) and content.strip():
                return content
            if isinstance(content, list):
                text_parts: list[str] = []
                for block in content:
                    if isinstance(block, dict):
                        text = block.get("text")
                        if isinstance(text, str) and text:
                            text_parts.append(text)
                merged = "".join(text_parts).strip()
                if merged:
                    return merged
            reasoning_content = message.get("reasoning_content")
            if isinstance(reasoning_content, str) and reasoning_content.strip():
                return reasoning_content.strip()

        text_choice = choice.get("text")
        if isinstance(text_choice, str) and text_choice.strip():
            return text_choice.strip()

        delta = choice.get("delta")
        if isinstance(delta, dict):
            delta_content = delta.get("content")
            if isinstance(delta_content, str) and delta_content.strip():
                return delta_content.strip()

        raise ValueError("解析结果打标响应缺少可解析文本内容")

    def _extract_first_json_block(self, text: str) -> str:
        candidate = text or ""
        start_obj = candidate.find("{")
        start_arr = candidate.find("[")
        starts = [index for index in (start_obj, start_arr) if index >= 0]
        if not starts:
            return candidate

        start_index = min(starts)
        stack: list[str] = []
        in_string: Optional[str] = None
        escaping = False

        for index in range(start_index, len(candidate)):
            ch = candidate[index]
            if in_string:
                if escaping:
                    escaping = False
                    continue
                if ch == "\\":
                    escaping = True
                    continue
                if ch == in_string:
                    in_string = None
                continue

            if ch in ('"', "'"):
                in_string = ch
                continue

            if ch in "{[":
                stack.append(ch)
                continue

            if ch in "}]":
                if not stack:
                    break
                expected = "{" if ch == "}" else "["
                if stack[-1] != expected:
                    break
                stack.pop()
                if not stack:
                    return candidate[start_index : index + 1]

        return candidate[start_index:]

    def _normalize_candidate_text(self, raw_text: str) -> str:
        candidate = (raw_text or "").strip().replace("\ufeff", "")
        candidate = candidate.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")

        fenced_match = re.search(r"```(?:json)?\s*(.*?)\s*```", candidate, re.DOTALL | re.IGNORECASE)
        if fenced_match:
            candidate = fenced_match.group(1).strip()

        candidate = self._extract_first_json_block(candidate).strip()

        candidate = re.sub(r",(\s*[}\]])", r"\1", candidate)
        return candidate

    def _parse_candidate_payload(self, candidate: str) -> dict[str, Any]:
        try:
            payload = json.loads(candidate)
            if isinstance(payload, dict):
                return payload
            if isinstance(payload, list):
                return {"tag_candidates": payload}
        except json.JSONDecodeError:
            pass

        python_style_candidate = re.sub(r"\bnull\b", "None", candidate, flags=re.IGNORECASE)
        python_style_candidate = re.sub(r"\btrue\b", "True", python_style_candidate, flags=re.IGNORECASE)
        python_style_candidate = re.sub(r"\bfalse\b", "False", python_style_candidate, flags=re.IGNORECASE)

        try:
            payload = ast.literal_eval(python_style_candidate)
        except (ValueError, SyntaxError) as exc:
            snippet = candidate[:1200].replace("\n", "\\n")
            api_logger.warning("解析结果打标 JSON 解析失败，响应片段=%s", snippet)
            raise ValueError("解析结果打标响应不是合法 JSON") from exc

        if isinstance(payload, dict):
            return payload
        if isinstance(payload, list):
            return {"tag_candidates": payload}
        raise ValueError("解析结果打标响应不是合法 JSON")

    def _load_tag_groups(self, db: Session, tag_group_ids: Optional[list[int]]) -> list[TagGroup]:
        query = db.query(TagGroup).filter(TagGroup.is_active == True)
        if tag_group_ids:
            query = query.filter(TagGroup.id.in_(tag_group_ids))
        return query.order_by(TagGroup.id.asc()).all()

    def _build_prompt(self, *, analysis_text: str, tag_groups: list[TagGroup]) -> str:
        tag_lines: list[str] = []
        for group in tag_groups:
            for tag in group.tags:
                if not tag.is_active:
                    continue
                tag_lines.append(f'- {{"tag_group_id": {group.id}, "group_name": "{group.name}", "tag_name": "{tag.name}"}}')

        library_section = "\n".join(tag_lines) if tag_lines else "- 没有预设标签"

        return (
            "你是视频解析结果打标助手。\n"
            "输入是视频解析报告（文本），请从中抽取最合适的标签。\n"
            "请仅输出合法 JSON，不要输出 Markdown，不要输出解释性文字。\n\n"
            "固定标签库（优先命中；不够时可补充自由标签，但仍只输出 tag_name）：\n"
            f"{library_section}\n\n"
            "视频解析结果：\n"
            f"{analysis_text}\n\n"
            "输出 JSON 结构必须为：\n"
            "{\n"
            '  "tag_candidates": [\n'
            '    {"tag_name": "示例", "confidence": 0.95, "reason": "依据解析结果的理由", "evidence_start_seconds": null, "evidence_end_seconds": null}\n'
            "  ]\n"
            "}\n"
            "要求：\n"
            "- confidence 范围必须是 0 到 1\n"
            "- tag_name 去除首尾空格后不能为空\n"
            "- 不要输出重复 tag_name\n"
        )

    def _extract_structured_payload(self, raw_text: str) -> dict[str, Any]:
        candidate = self._normalize_candidate_text(raw_text)
        try:
            payload = self._parse_candidate_payload(candidate)
        except ValueError as exc:
            snippet = (raw_text or "")[:1200].replace("\n", "\\n")
            raise ValueError(f"解析结果打标响应不是合法 JSON，原始响应片段={snippet}") from exc

        tag_candidates = payload.get("tag_candidates")
        if isinstance(tag_candidates, str) and tag_candidates.strip():
            nested_candidate = tag_candidates.strip()
            nested_candidate = self._normalize_candidate_text(nested_candidate)
            try:
                nested_payload = json.loads(nested_candidate)
            except json.JSONDecodeError:
                python_style_nested = re.sub(r"\bnull\b", "None", nested_candidate, flags=re.IGNORECASE)
                python_style_nested = re.sub(r"\btrue\b", "True", python_style_nested, flags=re.IGNORECASE)
                python_style_nested = re.sub(r"\bfalse\b", "False", python_style_nested, flags=re.IGNORECASE)
                try:
                    nested_payload = ast.literal_eval(python_style_nested)
                except (ValueError, SyntaxError):
                    nested_payload = None

            if isinstance(nested_payload, list):
                payload["tag_candidates"] = nested_payload

        return payload

    def _normalize_candidates(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        candidates = payload.get("tag_candidates")
        if not isinstance(candidates, list):
            raise ValueError("解析结果打标输出缺少数组字段: tag_candidates")

        dedup: dict[str, dict[str, Any]] = {}
        for item in candidates:
            if not isinstance(item, dict):
                continue

            tag_name = str(item.get("tag_name") or "").strip()
            if not tag_name:
                continue

            confidence_raw = item.get("confidence", 0.0)
            try:
                confidence = float(confidence_raw)
            except (TypeError, ValueError):
                confidence = 0.0

            if confidence < 0:
                confidence = 0.0
            if confidence > 1:
                confidence = 1.0

            normalized = {
                "tag_name": tag_name,
                "confidence": confidence,
                "reason": item.get("reason"),
                "evidence_start_seconds": item.get("evidence_start_seconds"),
                "evidence_end_seconds": item.get("evidence_end_seconds"),
            }

            existing = dedup.get(tag_name)
            if existing is None or float(normalized["confidence"]) >= float(existing.get("confidence", 0.0)):
                dedup[tag_name] = normalized

        return list(dedup.values())

    async def _call_openai_compatible(self, *, ai_config: AIConfig, prompt: str) -> str:
        api_url = ai_config.api_base or "https://api.openai.com/v1/chat/completions"
        api_key = ai_service._decrypt_config_secret(ai_config.api_key, "解析结果打标 API Key")

        resolved_max_tokens = min(max(int(ai_config.max_tokens or 0), 2000), 3000)
        request_data: Dict[str, Any] = {
            "model": ai_config.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "max_tokens": resolved_max_tokens,
            "stream": False,
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=ai_service.timeout) as client:
            response = await client.post(api_url, headers=headers, json=request_data)
            if response.status_code != 200:
                raise ValueError(f"解析结果打标 API 调用失败: {response.status_code} - {response.text}")
            try:
                payload = response.json()
            except Exception as exc:
                snippet = (response.text or "")[:1200].replace("\n", "\\n")
                raise ValueError(f"解析结果打标响应不是合法 JSON，响应片段={snippet}") from exc

        if not isinstance(payload, dict):
            snippet = str(payload)[:1200].replace("\n", "\\n")
            raise ValueError(f"解析结果打标响应不是合法 JSON，响应片段={snippet}")

        try:
            return self._extract_openai_compatible_text(payload)
        except ValueError as exc:
            try:
                payload_snippet = json.dumps(payload, ensure_ascii=False)[:1200].replace("\n", "\\n")
            except Exception:
                payload_snippet = str(payload)[:1200].replace("\n", "\\n")
            finish_reason = None
            choices = payload.get("choices")
            if isinstance(choices, list) and choices and isinstance(choices[0], dict):
                finish_reason = choices[0].get("finish_reason")
            suffix = f"，finish_reason={finish_reason}" if finish_reason else ""
            raise ValueError(f"{str(exc)}{suffix}，响应JSON片段={payload_snippet}") from exc

    async def _call_anthropic(self, *, ai_config: AIConfig, prompt: str) -> str:
        api_base = ai_config.api_base or "https://api.anthropic.com"
        api_url = f"{api_base.rstrip('/')}/v1/messages"
        api_key = ai_service._decrypt_config_secret(ai_config.api_key, "解析结果打标 API Key")

        request_data: Dict[str, Any] = {
            "model": ai_config.model,
            "max_tokens": min(int(ai_config.max_tokens or 800), 1200),
            "temperature": 0,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }

        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }

        async with httpx.AsyncClient(timeout=ai_service.timeout) as client:
            response = await client.post(api_url, headers=headers, json=request_data)
            if response.status_code != 200:
                raise ValueError(f"解析结果打标 API 调用失败: {response.status_code} - {response.text}")
            payload = response.json()

        content_blocks = payload.get("content") or []
        if not isinstance(content_blocks, list):
            raise ValueError("解析结果打标响应缺少 content")

        text_parts: list[str] = []
        for block in content_blocks:
            if isinstance(block, dict) and block.get("type") == "text":
                text_parts.append(str(block.get("text") or ""))

        output = "".join(text_parts).strip()
        if not output:
            raise ValueError("解析结果打标响应缺少可解析文本内容")
        return output

    async def generate_tag_candidates(
        self,
        *,
        db: Session,
        analysis: VideoAnalysis,
        ai_config: AIConfig,
        tag_group_ids: Optional[list[int]] = None,
    ) -> list[dict[str, Any]]:
        analysis_text_parts = []
        if analysis.result_summary:
            analysis_text_parts.append(str(analysis.result_summary))
        if analysis.analysis_result:
            analysis_text_parts.append(str(analysis.analysis_result))

        analysis_text = "\n\n".join(analysis_text_parts).strip()
        if not analysis_text:
            raise ValueError("解析结果为空，无法生成候选标签")

        analysis_text_max_length = 12_000
        if len(analysis_text) > analysis_text_max_length:
            analysis_text = analysis_text[:analysis_text_max_length]

        resolved_tag_group_ids = tag_group_ids if tag_group_ids is not None else analysis.tag_group_ids
        tag_groups = self._load_tag_groups(db=db, tag_group_ids=resolved_tag_group_ids)
        prompt = self._build_prompt(analysis_text=analysis_text, tag_groups=tag_groups)

        provider = (ai_config.provider or "").lower()
        api_logger.info(f"开始基于解析结果生成候选标签: analysis_id={analysis.id}, provider={provider}, model={ai_config.model}")

        if provider in {"openai", "custom"}:
            raw_text = await self._call_openai_compatible(ai_config=ai_config, prompt=prompt)
        elif provider == "anthropic":
            raw_text = await self._call_anthropic(ai_config=ai_config, prompt=prompt)
        else:
            raise ValueError(f"解析结果打标不支持的 provider: {ai_config.provider}")

        payload = self._extract_structured_payload(raw_text)
        return self._normalize_candidates(payload)


analysis_tagging_service = AnalysisTaggingService()
