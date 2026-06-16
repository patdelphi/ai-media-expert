import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Routes, Route, useLocation } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import VideoUpload from './VideoUpload'

vi.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({ isLoading: false }),
}))

const LocationProbe: React.FC = () => {
  const location = useLocation()
  return <div data-testid="location">{location.pathname + location.search}</div>
}

describe('VideoUpload', () => {
  it('点击分析按钮后跳转到视频解析页并带上 saved_filename', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          success: true,
          files: [
            {
              id: 'file-1',
              name: 'a.mp4',
              size: 123,
              upload_time: 1710000000,
              path: '/tmp',
              saved_name: 'saved-a.mp4',
            },
          ],
        }),
      }),
    )

    render(
      <MemoryRouter initialEntries={['/video/upload']}>
        <Routes>
          <Route path="/video/upload" element={<VideoUpload />} />
          <Route path="/video/analysis" element={<LocationProbe />} />
        </Routes>
      </MemoryRouter>,
    )

    const analyzeButton = await screen.findByRole('button', { name: '分析' })
    analyzeButton.click()

    await waitFor(() => {
      expect(screen.getByTestId('location').textContent).toBe(
        '/video/analysis?saved_filename=saved-a.mp4',
      )
    })
  })
})

