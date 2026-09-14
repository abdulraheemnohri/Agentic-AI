import React, { useState, useEffect } from 'react';
import { GlassCard, StatusBadge, HealthIndicator } from '../components';

interface ProviderStatus {
  name: string;
  enabled: boolean;
  healthy: boolean;
  calls: number;
  successes: number;
  errors: number;
  latency: number;
  last_status: string;
  last_error: string | null;
}

interface System1Health {
  status: string;
  service: string;
  version: string;
  uptime: string;
  components: {
    council: any;
    security: any;
    providers: any;
  };
  authority: boolean;
  always_on: boolean;
  can_be_stopped: boolean;
}

const System1Page: React.FC = () => {
  const [health, setHealth] = useState<System1Health | null>(null);
  const [providers, setProviders] = useState<ProviderStatus[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch System 1 health and providers
  useEffect(() => {
    const fetchSystem1Data = async () => {
      try {
        const [healthRes, providersRes] = await Promise.all([
          fetch('http://127.0.0.1:8101/api/system1/health'),
          fetch('http://127.0.0.1:8101/api/system1/providers'),
        ]);
        if (!healthRes.ok || !providersRes.ok) {
          throw new Error('Failed to fetch System 1 data');
        }
        const healthData = await healthRes.json();
        const providersData = await providersRes.json();
        setHealth(healthData);
        setProviders(providersData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };
    fetchSystem1Data();
  }, []);

  // Toggle provider enabled status
  const toggleProvider = async (providerName: string, enabled: boolean) => {
    try {
      const endpoint = enabled ? 'disable' : 'enable';
      const response = await fetch(`http://127.0.0.1:8101/api/system1/providers/${providerName}/${endpoint}`, {
        method: 'POST',
      });
      if (!response.ok) {
        throw new Error(`Failed to ${endpoint} provider`);
      }
      // Refresh providers
      const providersRes = await fetch('http://127.0.0.1:8101/api/system1/providers');
      if (providersRes.ok) {
        setProviders(await providersRes.json());
      }
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  if (loading) {
    return (
      <div className="page system1-page">
        <h1>System 1 Authority</h1>
        <p>Loading System 1 data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page system1-page">
        <h1>System 1 Authority</h1>
        <StatusBadge status="error">Error: {error}</StatusBadge>
      </div>
    );
  }

  return (
    <div className="page system1-page">
      <h1>System 1 Authority</h1>
      <p>
        System 1 is the <StatusBadge status="success">authoritative control plane</StatusBadge> for Agentic-AI.
        It manages security, permissions, Council, and provider health.
      </p>

      {/* System 1 Status */}
      <GlassCard title="System 1 Status">
        <div className="system1-status">
          <div>
            <strong>Status:</strong> <StatusBadge status={health?.status === 'HEALTHY' ? 'success' : 'danger'}>{health?.status}</StatusBadge>
          </div>
          <div>
            <strong>Service:</strong> {health?.service}
          </div>
          <div>
            <strong>Version:</strong> {health?.version}
          </div>
          <div>
            <strong>Uptime:</strong> {health?.uptime}
          </div>
          <div>
            <strong>Authority:</strong> {health?.authority ? '✓ ACTIVE' : '✗ INACTIVE'}
          </div>
          <div>
            <strong>Always On:</strong> {health?.always_on ? '✓ TRUE' : '✗ FALSE'}
          </div>
          <div>
            <strong>Can Be Stopped:</strong> {health?.can_be_stopped ? '✗ YES (SECURITY RISK)' : '✓ NO'}
          </div>
        </div>
      </GlassCard>

      {/* Provider Health */}
      <GlassCard title="Provider Health">
        <div className="providers-grid">
          {providers.map((provider) => (
            <div key={provider.name} className="provider-card">
              <h3>{provider.name}</h3>
              <div>
                <strong>Status:</strong> 
                <HealthIndicator status={provider.healthy ? 'healthy' : 'unhealthy'} />
              </div>
              <div>
                <strong>Enabled:</strong> 
                <StatusBadge status={provider.enabled ? 'success' : 'warning'}>
                  {provider.enabled ? 'YES' : 'NO'}
                </StatusBadge>
              </div>
              <div>
                <strong>Calls:</strong> {provider.calls}
              </div>
              <div>
                <strong>Successes:</strong> {provider.successes}
              </div>
              <div>
                <strong>Errors:</strong> {provider.errors}
              </div>
              <div>
                <strong>Latency:</strong> {provider.latency.toFixed(2)}ms
              </div>
              <div className="provider-actions">
                <button onClick={() => toggleProvider(provider.name, provider.enabled)}>
                  {provider.enabled ? 'Disable' : 'Enable'}
                </button>
              </div>
            </div>
          ))}
        </div>
      </GlassCard>

      {/* Security Rules */}
      <GlassCard title="Security Rules">
        <div className="security-rules">
          <h3>System 1 Authority Rules:</h3>
          <ul>
            <li>✓ System 1 is <strong>always authoritative</strong>.</li>
            <li>✓ System 1 <strong>cannot be stopped</strong> by System 2 or frontend.</li>
            <li>✓ System 2 <strong>cannot modify System 1</strong>.</li>
            <li>✓ System 2 <strong>cannot authorize execution</strong>.</li>
            <li>✓ All security violations are <strong>audited</strong>.</li>
          </ul>
        </div>
      </GlassCard>

      {/* Component Health */}
      <GlassCard title="Component Health">
        <div className="component-health">
          <h3>System 1 Components:</h3>
          <div className="health-grid">
            <div className="health-card">
              <strong>Council:</strong> 
              <HealthIndicator status={health?.components?.council?.status || 'healthy'} />
            </div>
            <div className="health-card">
              <strong>Security:</strong> 
              <HealthIndicator status={health?.components?.security?.status || 'healthy'} />
            </div>
            <div className="health-card">
              <strong>Providers:</strong> 
              <HealthIndicator status={health?.components?.providers?.status || 'healthy'} />
            </div>
          </div>
        </div>
      </GlassCard>
    </div>
  );
};

export default System1Page;
