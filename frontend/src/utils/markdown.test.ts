/**
 * Markdown 安全渲染测试
 *
 * 验证恶意 HTML 不会执行，同时正常 Markdown 语法仍可渲染。
 */

import { describe, expect, it } from 'vitest'

import { escapeHtml, renderSafeMarkdown } from './markdown'

describe('markdown 安全渲染', () => {
  it('应转义危险 HTML 标签', () => {
    expect(escapeHtml('<script>alert("xss")</script>')).toContain('&lt;script&gt;')
  })

  it('应保留正常 Markdown 渲染能力并阻断脚本注入', () => {
    const renderedHtml = renderSafeMarkdown('# 标题\n\n<script>alert("xss")</script>')

    expect(renderedHtml).toContain('<h1>标题</h1>')
    expect(renderedHtml).not.toContain('<script>')
    expect(renderedHtml).toContain('&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;')
  })
})
