/**
 * Markdown 安全渲染工具
 *
 * 先转义原始 HTML，再交给 marked 解析，避免模板预览直接执行脚本。
 */

import { marked } from 'marked'

export const escapeHtml = (raw: string): string => {
  return raw
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

export const renderSafeMarkdown = (markdownText: string): string => {
  return marked.parse(escapeHtml(markdownText), { async: false }) as string
}
