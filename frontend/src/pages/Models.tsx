import React, { useState, useEffect } from 'react';
import { GlassCard, StatusBadge, HealthIndicator, ModelCard } from '../components';

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
  role?: string;
  healthy?: boolean;
  calls?: number;
  successes?: number;
  errors?: number;
  latency?: number;
}

const ModelsPage: React.FC = () => {
  const [system1Models, setSystem1Models] = useState<Model[]>([]);
  const [system2Models, setSystem2Models] = useState<Model[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch models from System 1 and System 2
  useEffect(() => {
    const fetchModels = async () => {
      try {
        // Fetch System 1 providers (models)
        const system1Res = await fetch('http://127.0.0.1:8101/api/system1/providers');
        if (!system1Res.ok) {
          throw new Error('Failed to fetch System 1 models');
        }
        const system1Data = await system1Res.json();
        const system1ModelsList: Model[] = system1Data.map((provider: any) => ({
          name: provider.name,
          provider: provider.name,
          endpoint: 'N/A',
          enabled: provider.enabled,
          priority: provider.priority,
          size: 'N/A',
          quantization: 'N/A',
          context_length: 0,
          network_scope: 'system1',
          role: 'System 1 Provider',
          healthy: provider.healthy,
          calls: provider.calls,
          successes: provider.successes,
          errors: provider.errors,
          latency: provider.latency,
        }));
        setSystem1Models(system1ModelsList);

        // Fetch System 2 models
        const system2Res = await fetch('http://127.0.0.1:8102/api/system2/models');
        if (!system2Res.ok) {
          throw new Error('Failed to fetch System 2 models');
        }
        const system2Data = await system2Res.json();
        const system2ModelsList: Model[] = system2Data.map((model: any) => ({
          name: model.name,
          provider: model.provider,
          endpoint: model.endpoint,
          enabled: model.enabled,
          priority: model.priority,
          size: model.size,
          quantization: model.quantization,
          context_length: model.context_length,
          network_scope: model.network_scope,
          role: 'System 2 Model',
        }));
        setSystem2Models(system2ModelsList);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };
    fetchModels();
  }, []);

  // Toggle model enabled status
  const toggleModel = async (model: Model, isSystem1: boolean) => {
    try {
      const endpoint = isSystem1 ? 'enable' : 'activate';
      const baseUrl = isSystem1 ? 'http://127.0.0.1:8101/api/system1/providers' : 'http://127.0.0.1:8102/api/system2/models';
      const response = await fetch(`${baseUrl}/${model.name}/${model.enabled ? 'disable' : endpoint}`, {
        method: 'POST',
      });
      if (!response.ok) {
        throw new Error(`Failed to ${model.enabled ? 'disable' : 'enable'} model`);
      }
      // Refresh models
      await fetchModels();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  // Discover new models (System 2 only)
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
      const system2Res = await fetch('http://127.0.0.1:8102/api/system2/models');
      if (system2Res.ok) {
        const system2Data = await system2Res.json();
        setSystem2Models(system2Data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  const fetchModels = async () => {
    try {
      const [system1Res, system2Res] = await Promise.all([
        fetch('http://127.0.0.1:8101/api/system1/providers'),
        fetch('http://127.0.0.1:8102/api/system2/models'),
      ]);
      if (!system1Res.ok || !system2Res.ok) {
        throw new Error('Failed to fetch models');
      }
      const system1Data = await system1Res.json();
      const system2Data = await system2Res.json();
      setSystem1Models(system1Data);
      setSystem2Models(system2Data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  if (loading) {
    return (
      <div className="page models-page">
        <h1>Models</h1>
        <p>Loading models...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page models-page">
        <h1>Models</h1>
        <StatusBadge status="error">Error: {error}</StatusBadge>
      </div>
    );
  }

  return (
    <div className="page models-page">
      <h1>Models</h1>
      <p>
        Manage System 1 providers and System 2 local models.
        System 1 models are <StatusBadge status="success">authoritative</StatusBadge>.
        System 2 models are <StatusBadge status="info">loopback-only</StatusBadge>.
      </p>

      {/* System 1 Models */}
      <GlassCard title="System 1 Providers">
        <div className="models-actions">
          <button className="ghost" onClick={fetchModels}>Refresh</button>
        </div>
        <div className="models-grid">
          {system1Models.map((model) => (
            <ModelCard
              key={model.name}
              name={model.name}
              provider={model.provider}
              size={model.size}
              quantization={model.quantization}
              contextLength={model.context_length}
              enabled={model.enabled}
            >
              <div className="model-actions">
                <button onClick={() => toggleModel(model, true)}>
                  {model.enabled ? 'Disable' : 'Enable'}
                </button>
              </div>
              {model.healthy !== undefined && (
                <div>
                  <strong>Health:</strong> <HealthIndicator status={model.healthy ? 'healthy' : 'unhealthy'} />
                </div>
              )}
              {model.calls !== undefined && (
                <div>
                  <strong>Calls:</strong> {model.calls}
                </div>
              )}
              {model.successes !== undefined && (
                <div>
                  <strong>Successes:</strong> {model.successes}
                </div>
              )}
              {model.errors !== undefined && (
                <div>
                  <strong>Errors:</strong> {model.errors}
                </div>
              )}
              {model.latency !== undefined && (
                <div>
                  <strong>Latency:</strong> {model.latency.toFixed(2)}ms
                </div>
              )}
            </ModelCard>
          ))}
        </div>
      </GlassCard>

      {/* System 2 Models */}
      <GlassCard title="System 2 Local Models">
        <div className="models-actions">
          <button onClick={discoverModels}>Discover Models</button>
          <button className="ghost" onClick={fetchModels}>Refresh</button>
        </div>
        <div className="models-grid">
          {system2Models.map((model) => (
            <ModelCard
              key={model.name}
              name={model.name}
              provider={model.provider}
              size={model.size}
              quantization={model.quantization}
              contextLength={model.context_length}
              enabled={model.enabled}
            >
              <div className="model-actions">
                <button onClick={() => toggleModel(model, false)}>
                  {model.enabled ? 'Deactivate' : 'Activate'}
                </button>
              </div>
              <div>
                <strong>Endpoint:</strong> {model.endpoint}
              </div>
              <div>
                <strong>Network Scope:</strong> <StatusBadge status={model.network_scope === 'loopback' ? 'success' : 'danger'}>{model.network_scope}</StatusBadge>
              </div>
            </ModelCard>
          ))}
        </div>
      </GlassCard>

      {/* Model Rules */}
      <GlassCard title="Model Rules">
        <div className="model-rules">
          <h3>System 1 Models:</h3>
          <ul>
            <li>✓ <strong>Authoritative</strong>: System 1 models are part of the control plane.</li>
            <li>✓ <strong>Remote Allowed</strong>: Can connect to remote providers (OpenAI, Gemini, etc.).</li>
            <li>✓ <strong>Health Monitored</strong>: System 1 tracks provider health and latency.</li>
          </ul>
          <h3>System 2 Models:</h3>
          <ul>
            <li>✓ <strong>Loopback-Only</strong>: System 2 models must run locally.</li>
            <li>✓ <strong>Non-Authoritative</strong>: System 2 models can only propose, not authorize.</li>
            <li>✓ <strong>Replaceable</strong>: System 2 models can be swapped or updated.</li>
          </ul>
        </div>
      </GlassCard>
    </div>
  );
};

export default ModelsPage;
