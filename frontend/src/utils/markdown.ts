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

const decodeHtmlEntities = (value: string): string => {
  return value
    .replace(/&#(\d+);?/gi, (_, dec) => String.fromCharCode(Number(dec)))
    .replace(/&#x([0-9a-f]+);?/gi, (_, hex) => String.fromCharCode(parseInt(hex, 16)))
}

const isSafeUrl = (url: string): boolean => {
  const normalizedUrl = decodeHtmlEntities(url)
    .replace(/[\u0000-\u001F\u007F\s]+/g, '')
    .trim()

  if (!normalizedUrl) {
    return false
  }

  if (
    normalizedUrl.startsWith('#') ||
    normalizedUrl.startsWith('/') ||
    normalizedUrl.startsWith('./') ||
    normalizedUrl.startsWith('../')
  ) {
    return true
  }

  return /^(https?:|mailto:|tel:)/i.test(normalizedUrl)
}

const sanitizeRenderedHtml = (html: string): string => {
  return html.replace(/\s(href|src)=("([^"]*)"|'([^']*)')/gi, (_matched, attribute, quotedValue, doubleQuotedUrl, singleQuotedUrl) => {
    const url = doubleQuotedUrl ?? singleQuotedUrl ?? ''
    if (!isSafeUrl(url)) {
      return ''
    }
    return ` ${attribute}=${quotedValue}`
  })
}

export const renderSafeMarkdown = (markdownText: string): string => {
  const renderedHtml = marked.parse(escapeHtml(markdownText), { async: false }) as string
  return sanitizeRenderedHtml(renderedHtml)
}
