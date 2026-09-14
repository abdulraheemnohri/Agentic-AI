import React, { useState, useEffect } from 'react';
import { GlassCard, StatusBadge, HealthIndicator } from '../components';

interface Model {
  name: string;
  provider: string;
  endpoint: string;
  enabled: boolean;
  priority: number;
  size: string;
  quantization: string;
  context_length: number;
  network_scope: string;
}

interface System2Health {
  status: string;
  service: string;
  version: string;
  active_model: string | null;
  loopback_only: boolean;
  authority: boolean;
  network_scope: string;
}

const System2Page: React.FC = () => {
  const [health, setHealth] = useState<System2Health | null>(null);
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch System 2 health and models
  useEffect(() => {
    const fetchSystem2Data = async () => {
      try {
        const [healthRes, modelsRes] = await Promise.all([
          fetch('http://127.0.0.1:8102/api/system2/health'),
          fetch('http://127.0.0.1:8102/api/system2/models'),
        ]);
        if (!healthRes.ok || !modelsRes.ok) {
          throw new Error('Failed to fetch System 2 data');
        }
        const healthData = await healthRes.json();
        const modelsData = await modelsRes.json();
        setHealth(healthData);
        setModels(modelsData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };
    fetchSystem2Data();
  }, []);

  // Toggle model enabled status
  const toggleModel = async (modelName: string, enabled: boolean) => {
    try {
      const endpoint = enabled ? 'deactivate' : 'activate';
      const response = await fetch(`http://127.0.0.1:8102/api/system2/models/${modelName}/${endpoint}`, {
        method: 'POST',
      });
      if (!response.ok) {
        throw new Error(`Failed to ${endpoint} model`);
      }
      // Refresh models
      const modelsRes = await fetch('http://127.0.0.1:8102/api/system2/models');
      if (modelsRes.ok) {
        setModels(await modelsRes.json());
      }
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  // Discover local models
  const discoverModels = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8102/api/system2/models/discover', {
        method: 'POST',
      });
      if (!response.ok) {
        throw new Error('Failed to discover models');
      }
      const result = await response.json();
      alert(`Discovered ${result.discovered} models: ${result.models.map((m: any) => m.name).join(', ')}`);
      // Refresh models
      const modelsRes = await fetch('http://127.0.0.1:8102/api/system2/models');
      if (modelsRes.ok) {
        setModels(await modelsRes.json());
      }
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  // Start/Stop System 2
  const handleSystem2Action = async (action: 'start' | 'stop' | 'restart') => {
    try {
      const response = await fetch(`http://127.0.0.1:8102/api/system2/${action}`, {
        method: 'POST',
      });
      if (!response.ok) {
        throw new Error(`Failed to ${action} System 2`);
      }
      const result = await response.json();
      alert(result.message);
      // Refresh health
      const healthRes = await fetch('http://127.0.0.1:8102/api/system2/health');
      if (healthRes.ok) {
        setHealth(await healthRes.json());
      }
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  if (loading) {
    return (
      <div className="page system2-page">
        <h1>System 2 Intelligence</h1>
        <p>Loading System 2 data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page system2-page">
        <h1>System 2 Intelligence</h1>
        <StatusBadge status="error">Error: {error}</StatusBadge>
      </div>
    );
  }

  return (
    <div className="page system2-page">
      <h1>System 2 Intelligence</h1>
      <p>
        System 2 is the <StatusBadge status="info">local reasoning backend</StatusBadge> for Agentic-AI.
        It generates proposals but <strong>cannot authorize or execute</strong>.
      </p>

      {/* System 2 Status */}
      <GlassCard title="System 2 Status">
        <div className="system2-status">
          <div>
            <strong>Status:</strong> <StatusBadge status={health?.status === 'running' ? 'success' : 'warning'}>{health?.status}</StatusBadge>
          </div>
          <div>
            <strong>Service:</strong> {health?.service}
          </div>
          <div>
            <strong>Version:</strong> {health?.version}
          </div>
          <div>
            <strong>Active Model:</strong> {health?.active_model || 'None'}
          </div>
          <div>
            <strong>Loopback Only:</strong> {health?.loopback_only ? '✓ YES' : '✗ NO (SECURITY RISK)'}
          </div>
          <div>
            <strong>Authority:</strong> {health?.authority ? '✗ YES (SECURITY RISK)' : '✓ NO'}
          </div>
          <div>
            <strong>Network Scope:</strong> {health?.network_scope}
          </div>
          <div className="system2-actions">
            <button onClick={() => handleSystem2Action('start')}>Start</button>
            <button onClick={() => handleSystem2Action('stop')}>Stop</button>
            <button onClick={() => handleSystem2Action('restart')}>Restart</button>
          </div>
        </div>
      </GlassCard>

      {/* Local Models */}
      <GlassCard title="Local Models">
        <div className="models-actions">
          <button onClick={discoverModels}>Discover Models</button>
        </div>
        <div className="models-grid">
          {models.map((model) => (
            <div key={model.name} className="model-card">
              <h3>{model.name}</h3>
              <div>
                <strong>Provider:</strong> {model.provider}
              </div>
              <div>
                <strong>Endpoint:</strong> {model.endpoint}
              </div>
              <div>
                <strong>Enabled:</strong> 
                <StatusBadge status={model.enabled ? 'success' : 'warning'}>
                  {model.enabled ? 'YES' : 'NO'}
                </StatusBadge>
              </div>
              <div>
                <strong>Priority:</strong> {model.priority}
              </div>
              <div>
                <strong>Size:</strong> {model.size}
              </div>
              <div>
                <strong>Quantization:</strong> {model.quantization}
              </div>
              <div>
                <strong>Context Length:</strong> {model.context_length}
              </div>
              <div>
                <strong>Network Scope:</strong> {model.network_scope}
              </div>
              <div className="model-actions">
                <button onClick={() => toggleModel(model.name, model.enabled)}>
                  {model.enabled ? 'Deactivate' : 'Activate'}
                </button>
              </div>
            </div>
          ))}
        </div>
      </GlassCard>

      {/* System 2 Rules */}
      <GlassCard title="System 2 Rules">
        <div className="system2-rules">
          <h3>System 2 Restrictions:</h3>
          <ul>
            <li>✓ System 2 is <strong>loopback-only</strong> (127.0.0.1, localhost, ::1).</li>
            <li>✓ System 2 <strong>cannot authorize execution</strong>.</li>
            <li>✓ System 2 <strong>cannot modify System 1</strong>.</li>
            <li>✓ System 2 <strong>cannot stop System 1</strong>.</li>
            <li>✓ System 2 proposals are <strong>always reviewed by System 1</strong>.</li>
          </ul>
        </div>
      </GlassCard>

      {/* Authority Badge */}
      <GlassCard title="Authority Badge">
        <div className="authority-badge">
          <h2>
            <StatusBadge status="warning">AUTHORITY: NONE</StatusBadge>
          </h2>
          <p>
            <StatusBadge status="success">LOOPBACK ONLY</StatusBadge>
          </p>
          <p>System 2 is a reasoning backend. It generates proposals but has no authority to execute or modify System 1.</p>
        </div>
      </GlassCard>
    </div>
  );
};

export default System2Page;
