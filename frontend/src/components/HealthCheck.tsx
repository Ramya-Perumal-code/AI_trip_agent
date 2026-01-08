import { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import './HealthCheck.css';

const HealthCheck = () => {
  const [health, setHealth] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const checkHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiService.checkHealth();
      setHealth(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to check health');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkHealth();
  }, []);

  return (
    <div className="health-check">
      <h2>API Health Status</h2>
      <button onClick={checkHealth} disabled={loading} className="refresh-button">
        {loading ? 'Checking...' : 'Refresh Status'}
      </button>

      {loading && <div className="loading">Checking API health...</div>}

      {error && (
        <div className="error">
          <strong>Error:</strong> {error}
        </div>
      )}

      {health && (
        <div className="health-status">
          <div className="status-item">
            <span className="label">Status:</span>
            <span className={`value status-${health.status}`}>
              {health.status}
            </span>
          </div>
          <div className="status-item">
            <span className="label">Message:</span>
            <span className="value">{health.message}</span>
          </div>
          <div className="status-item">
            <span className="label">Version:</span>
            <span className="value">{health.version}</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default HealthCheck;





