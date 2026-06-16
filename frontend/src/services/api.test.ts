/**
 * API 刷新令牌测试
 *
 * 验证并发 401 场景下只会触发一次 refresh 请求，避免重复刷新。
 */

import { beforeEach, describe, expect, it, vi } from 'vitest'

const { axiosCreateMock, axiosInstances } = vi.hoisted(() => {
  const instances: Array<Record<string, unknown>> = []
  const createMock = vi.fn(() => {
    const instance = {
      interceptors: {
        request: { use: vi.fn() },
        response: { use: vi.fn() },
      },
      post: vi.fn(),
      get: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
      patch: vi.fn(),
    }
    instances.push(instance)
    return instance
  })

  return {
    axiosCreateMock: createMock,
    axiosInstances: instances,
  }
})

vi.mock('axios', () => ({
  default: {
    create: axiosCreateMock,
  },
  create: axiosCreateMock,
}))

import { ApiService, type TokenPayload } from './api'

describe('ApiService.refreshAuthToken', () => {
  beforeEach(() => {
    axiosCreateMock.mockClear()
    axiosInstances.length = 0
    window.localStorage.clear()
  })

  it('并发刷新时应复用同一个 refresh Promise', async () => {
    const apiService = new ApiService()
    const refreshClient = axiosInstances[1] as {
      post: ReturnType<typeof vi.fn>
    }

    let resolveRefresh: ((value: { data: { data: TokenPayload } }) => void) | null = null
    const refreshResponse = new Promise<{ data: { data: TokenPayload } }>((resolve) => {
      resolveRefresh = resolve
    })
    refreshClient.post.mockReturnValue(refreshResponse)

    const firstPromise = apiService.refreshAuthToken('refresh-token')
    const secondPromise = apiService.refreshAuthToken('refresh-token')

    expect(refreshClient.post).toHaveBeenCalledTimes(1)

    resolveRefresh!({
      data: {
        data: {
          access_token: 'access-token',
          refresh_token: 'next-refresh-token',
          token_type: 'bearer',
          expires_in: 1800,
        },
      },
    })

    const [firstResult, secondResult] = await Promise.all([firstPromise, secondPromise])

    expect(firstResult).toEqual({
      access_token: 'access-token',
      refresh_token: 'next-refresh-token',
      token_type: 'bearer',
      expires_in: 1800,
    })
    expect(secondResult).toEqual(firstResult)
  })

  it('401 且刷新令牌失效时应清空本地认证数据', async () => {
    const apiService = new ApiService()
    const apiClient = axiosInstances[0] as {
      interceptors: {
        response: {
          use: ReturnType<typeof vi.fn>
        }
      }
    }
    const refreshClient = axiosInstances[1] as {
      post: ReturnType<typeof vi.fn>
    }

    const responseErrorHandler = apiClient.interceptors.response.use.mock.calls[0][1] as (
      error: unknown,
    ) => Promise<unknown>
    const authError = {
      response: { status: 401 },
      config: { headers: {} },
    }
    window.localStorage.setItem('access_token', 'expired-access-token')
    window.localStorage.setItem('refresh_token', 'expired-refresh-token')
    window.localStorage.setItem('user', JSON.stringify({ id: 1 }))
    const refreshError = new Error('refresh failed')
    refreshClient.post.mockRejectedValue(refreshError)

    await expect(responseErrorHandler(authError)).rejects.toBe(refreshError)
    expect(window.localStorage.getItem('access_token')).toBeNull()
    expect(window.localStorage.getItem('refresh_token')).toBeNull()
    expect(window.localStorage.getItem('user')).toBeNull()
    expect(apiService).toBeInstanceOf(ApiService)
  })
})
