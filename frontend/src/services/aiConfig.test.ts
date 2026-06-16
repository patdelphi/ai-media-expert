/**
 * AI 配置服务测试
 *
 * 验证 max_tokens 不再限制上限，但必须为正整数。
 */

import { describe, expect, it } from 'vitest'

import { aiConfigService } from './aiConfig'

describe('AIConfigService.getSupportedProviders', () => {
  it('应只返回当前真实支持的 provider', () => {
    const providers = aiConfigService.getSupportedProviders()

    expect(providers.map((provider) => provider.value)).toEqual(['openai', 'anthropic', 'custom'])
  })
})

describe('AIConfigService.validateConfig', () => {
  it('应允许超大 max_tokens 整数值', () => {
    const errors = aiConfigService.validateConfig({
      name: '自定义配置',
      provider: 'custom',
      api_key: '1234567890-valid-key',
      model: 'gpt-4o',
      max_tokens: 999999999,
      temperature: 1,
    })

    expect(errors).toEqual([])
  })

  it('应拦截非正整数 max_tokens', () => {
    expect(
      aiConfigService.validateConfig({
        max_tokens: 0,
      }),
    ).toContain('最大token数必须是正整数')

    expect(
      aiConfigService.validateConfig({
        max_tokens: -1,
      }),
    ).toContain('最大token数必须是正整数')

    expect(
      aiConfigService.validateConfig({
        max_tokens: 1.5,
      }),
    ).toContain('最大token数必须是正整数')
  })
})
