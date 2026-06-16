/**
 * 自动管理员登录测试
 *
 * 验证前端会使用 ".env" 中的管理员凭据调用现有登录接口，
 * 而不是伪造本地管理员态。
 */

import React from 'react'
import { render, screen, waitFor, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const { adminUser, authServiceMock } = vi.hoisted(() => {
  const user = {
    id: 1,
    email: 'admin@example.com',
    username: 'admin',
    full_name: '系统管理员',
    avatar_url: '',
    is_active: true,
    is_verified: true,
    role: 'admin',
    last_login_at: '2026-06-16T00:00:00.000Z',
    created_at: '2026-06-16T00:00:00.000Z',
    updated_at: '2026-06-16T00:00:00.000Z',
  }

  return {
    adminUser: user,
    authServiceMock: {
      isAuthenticated: vi.fn(),
      getCurrentUserFromStorage: vi.fn(),
      getCurrentUser: vi.fn(),
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      updateUser: vi.fn(),
      shouldRefreshToken: vi.fn(),
      autoRefreshToken: vi.fn(),
      clearAuthData: vi.fn(),
    },
  }
})

vi.mock('../services/auth', () => ({
  authService: authServiceMock,
}))

import ProtectedRoute from '../components/ProtectedRoute'
import { AuthProvider, useAuth } from './AuthContext'

const AuthStateProbe: React.FC = () => {
  const { isAuthenticated, isLoading, user } = useAuth()

  return (
    <div>
      <span data-testid="auth-state">{isAuthenticated ? 'authenticated' : 'anonymous'}</span>
      <span data-testid="loading-state">{isLoading ? 'loading' : 'ready'}</span>
      <span data-testid="role">{user?.role ?? 'none'}</span>
      <span data-testid="username">{user?.username ?? 'none'}</span>
    </div>
  )
}

describe('AuthContext 自动管理员登录', () => {
  beforeEach(() => {
    window.localStorage.clear()
    vi.unstubAllEnvs()
    vi.stubEnv('VITE_AUTO_LOGIN_USERNAME', '')
    vi.stubEnv('VITE_AUTO_LOGIN_PASSWORD', '')
    Object.values(authServiceMock).forEach((mockFn) => {
      if ('mockReset' in mockFn) {
        mockFn.mockReset()
      }
    })

    authServiceMock.isAuthenticated.mockReturnValue(false)
    authServiceMock.getCurrentUserFromStorage.mockReturnValue(null)
    authServiceMock.getCurrentUser.mockResolvedValue({ code: 200, data: adminUser })
    authServiceMock.login.mockResolvedValue({
      code: 200,
      data: {
        user: adminUser,
        access_token: 'access-token',
        refresh_token: 'refresh-token',
        token_type: 'bearer',
        expires_in: 1800,
      },
    })
    authServiceMock.shouldRefreshToken.mockReturnValue(false)
    authServiceMock.autoRefreshToken.mockResolvedValue(true)
    authServiceMock.logout.mockResolvedValue(undefined)
    authServiceMock.updateUser.mockResolvedValue({ code: 200, data: adminUser })
  })

  it('存在 ".env" 管理员凭据时应自动调用真实登录', async () => {
    vi.stubEnv('VITE_AUTO_LOGIN_USERNAME', 'admin')
    vi.stubEnv('VITE_AUTO_LOGIN_PASSWORD', 'secret')

    render(
      <MemoryRouter>
        <AuthProvider>
          <AuthStateProbe />
        </AuthProvider>
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(screen.getByTestId('auth-state')).toHaveTextContent('authenticated')
    })

    expect(screen.getByTestId('loading-state')).toHaveTextContent('ready')
    expect(screen.getByTestId('role')).toHaveTextContent('admin')
    expect(screen.getByTestId('username')).toHaveTextContent('admin')
    expect(authServiceMock.login).toHaveBeenCalledWith({
      username: 'admin',
      password: 'secret',
    })
  })

  it('没有 ".env" 自动登录凭据时应保持未登录状态', async () => {
    const { container } = render(
      <MemoryRouter>
        <AuthProvider>
          <AuthStateProbe />
        </AuthProvider>
      </MemoryRouter>,
    )
    const testScope = within(container)

    await waitFor(() => {
      expect(testScope.getByTestId('loading-state')).toHaveTextContent('ready')
    })

    expect(testScope.getByTestId('auth-state')).toHaveTextContent('anonymous')
    expect(authServiceMock.login).not.toHaveBeenCalled()
  })

  it('已有真实登录态时不应重复自动登录，且管理员可通过受保护路由', async () => {
    authServiceMock.isAuthenticated.mockReturnValue(true)
    authServiceMock.getCurrentUserFromStorage.mockReturnValue(adminUser)

    render(
      <MemoryRouter>
        <AuthProvider>
          <ProtectedRoute requireRoles={['admin']}>
            <div>受保护内容</div>
          </ProtectedRoute>
        </AuthProvider>
      </MemoryRouter>,
    )

    await waitFor(() => {
      expect(screen.getByText('受保护内容')).toBeInTheDocument()
    })

    expect(authServiceMock.login).not.toHaveBeenCalled()
  })
})
