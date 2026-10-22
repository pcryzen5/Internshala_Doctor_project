import { useEffect, useState } from 'react';
import { Activity, CheckCircle2, AlertCircle } from 'lucide-react';
import './App.css';

interface HealthStatus {
  status: string;
  asr: string;
  db: string;
}

export function App() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function checkHealth() {
      try {
        const res = await fetch('/health');
        if (!res.ok) {
          throw new Error(`Health check failed with status: ${res.status}`);
        }
        const data = (await res.json()) as HealthStatus;
        setHealth(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to connect to API');
      } finally {
        setLoading(false);
      }
    }

    checkHealth();
  }, []);

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="header-brand">
          <Activity className="brand-icon" />
          <div className="brand-text">
            <h1>Live Medical Transcription</h1>
            <p>Clinical Intelligence & Structured Summary</p>
          </div>
        </div>

        <div className="header-status" data-testid="status-container">
          {loading && <span className="status-badge loading">Checking backend...</span>}
          {error && (
            <span className="status-badge error" data-testid="api-error">
              <AlertCircle size={14} /> Connection Error
            </span>
          )}
          {health && (
            <div className="status-badge ok" data-testid="api-ok">
              <CheckCircle2 size={16} />
              <span>API OK</span>
              <span className="sub-badge">ASR: {health.asr}</span>
              <span className="sub-badge">DB: {health.db}</span>
            </div>
          )}
        </div>
      </header>

      <main className="main-content">
        <div className="initial-card">
          <h2>Clinical Scribe Workspace Initialized</h2>
          <p>Phase 0 Foundation Scaffold complete. Ready to begin Phase 1 / Step 2.</p>
        </div>
      </main>
    </div>
  );
}

export default App;
