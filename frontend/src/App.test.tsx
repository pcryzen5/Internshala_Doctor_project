import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import App from './App';

describe('App Component', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders loading state initially and then shows API OK on successful health check', async () => {
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

    expect(screen.getByText(/Checking backend.../i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByTestId('api-ok')).toBeInTheDocument();
      expect(screen.getByText('API OK')).toBeInTheDocument();
      expect(screen.getByText('ASR: ready')).toBeInTheDocument();
      expect(screen.getByText('DB: ok')).toBeInTheDocument();
    });
  });

  it('displays error badge when health check fails', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValueOnce(new Error('Network error'));

    render(<App />);

    await waitFor(() => {
      expect(screen.getByTestId('api-error')).toBeInTheDocument();
    });
  });
});
