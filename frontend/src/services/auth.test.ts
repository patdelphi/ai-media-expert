/**
 * 认证服务测试
 *
 * 验证登录接口在后端空响应场景下会返回可读错误，
 * 避免直接抛出 "Unexpected end of JSON input"。
 */

import { beforeEach, describe, expect, it, vi } from 'vitest'

const { apiServiceMock } = vi.hoisted(() => ({
  apiServiceMock: {
    getBaseUrl: vi.fn(() => '/api/v1'),
    post: vi.fn(),
  },
}))

vi.mock('./api', () => ({
  apiService: apiServiceMock,
}))

import { authService } from './auth'

describe('AuthService.login', () => {
  beforeEach(() => {
    window.localStorage.clear()
    vi.restoreAllMocks()
    apiServiceMock.getBaseUrl.mockReturnValue('/api/v1')
  })

  it('后端返回空响应时应提示服务无响应', async () => {
    vi.spyOn(window, 'fetch').mockResolvedValue({
      ok: false,
      text: vi.fn().mockResolvedValue(''),
    } as unknown as Response)

    await expect(
      authService.login({
        username: 'admin',
        password: '123456',
      }),
    ).rejects.toThrow('登录服务无响应，请确认后端已启动')
  })
})
