import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Dashboard from '../src/components/ui/Dashboard';
import * as api from '../src/api';

// Mock the API module
vi.mock('../src/api', () => ({
  fetchSummary: vi.fn(),
  fetchRecentFiles: vi.fn(),
}));

describe('Dashboard', () => {
  it('renders stat cards', async () => {
    // Mock API responses
    api.fetchSummary.mockResolvedValue({
      totalFiles: 42,
      totalSize: 1073741824,
      totalImages: 10,
      totalPDFs: 8,
      totalJSON: 6,
      totalVideos: 4,
      totalAudio: 2,
      byType: {
        image: 10,
        pdf: 8,
        json: 6,
        video: 4,
        audio: 2,
      },
    });

    api.fetchRecentFiles.mockResolvedValue([]);

    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );

    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('Total Files')).toBeInTheDocument();
      expect(screen.getByText('42')).toBeInTheDocument();
    });
  });

  it('shows correct recent uploads when API returns data', async () => {
    const mockFiles = [
      {
        id: 'test-1',
        filename: 'test.png',
        size: 1024,
        classification: {
          type: 'image',
          category: 'image_screenshot',
          subcategories: ['image_png'],
          confidence: 0.85,
        },
      },
    ];

    api.fetchSummary.mockResolvedValue({
      totalFiles: 1,
      totalSize: 1024,
      byType: { image: 1 },
    });

    api.fetchRecentFiles.mockResolvedValue(mockFiles);

    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('test.png')).toBeInTheDocument();
      expect(screen.getByText('image_screenshot')).toBeInTheDocument();
    });
  });

  it('shows empty state when no files exist', async () => {
    api.fetchSummary.mockResolvedValue({
      totalFiles: 0,
      totalSize: 0,
      byType: {},
    });

    api.fetchRecentFiles.mockResolvedValue([]);

    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/No files yet/i)).toBeInTheDocument();
    });
  });
});
