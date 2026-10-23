import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import App from './App';

describe('App Component', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders application brand, workspace panels, and API OK badge on successful health check', async () => {
    const mockHealth = {
      status: 'ok',
      asr: 'ready',
      db: 'ok',
    };

    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: async () => mockHealth,
    } as Response);

    render(<App />);

    // Brand and card headers exist
    expect(screen.getByRole('heading', { name: /Live Medical Transcription/i, level: 1 })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /Live Medical Transcription/i, level: 2 })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /AI Medical Summary/i, level: 2 })).toBeInTheDocument();

    // Both panels are rendered
    expect(screen.getByLabelText(/Live Medical Transcription/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/AI Medical Summary/i)).toBeInTheDocument();

    // Health badge updates to API OK
    await waitFor(() => {
      expect(screen.getByText('API OK')).toBeInTheDocument();
      expect(screen.getByText('ASR: ready')).toBeInTheDocument();
    });
  });

  it('displays offline badge when health check fails', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValueOnce(new Error('Network error'));

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText(/Backend Offline/i)).toBeInTheDocument();
    });
  });
});
