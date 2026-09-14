import React, { useState, useEffect } from 'react';
import { GlassCard, StatusBadge } from '../components';

interface Settings {
  // General
  application_name: string;
  timezone: string;
  language: string;
  ui_density: 'compact' | 'default' | 'comfortable';
  theme: 'dark' | 'light' | 'system';

  // Agent
  autonomy: number;
  max_iterations: number;
  max_retries: number;
  confidence_threshold: number;

  // Runtime
  max_concurrency: number;
  queue_limit: number;
  polling_interval: number;
  timeout: number;
  retry_policy: 'exponential' | 'linear' | 'none';

  // System 1
  council_mode: 'Any' | 'All' | 'Consensus';
  minimum_confidence: number;
  minimum_reviews: number;
  fail_closed_on_disagreement: boolean;

  // System 2
  endpoint: string;
  model: string;
  lifecycle: 'start' | 'stop' | 'restart' | 'update' | 'upgrade';
  discovery: boolean;
  resource_limits: {
    cpu: number;
    memory: number;
  };

  // Security
  permission_mode: 'strict' | 'lenient' | 'custom';
  approval_rules: 'auto' | 'confirm' | 'deny';
  critical_tool_policy: 'block' | 'confirm' | 'allow';
  audit_retention: number; // days

  // Memory
  enable_learning: boolean;
  recall_limit: number;
  importance_threshold: number;
  retention: number; // days

  // Observability
  sse_enabled: boolean;
  websocket_enabled: boolean;
  polling_fallback: boolean;
  heartbeat_interval: number;
  event_retention: number; // days
}

const SettingsPage: React.FC = () => {
  const [settings, setSettings] = useState<Settings>({
    // General
    application_name: 'Agentic-AI',
    timezone: 'UTC',
    language: 'en',
    ui_density: 'default',
    theme: 'dark',

    // Agent
    autonomy: 1,
    max_iterations: 5,
    max_retries: 2,
    confidence_threshold: 0.7,

    // Runtime
    max_concurrency: 4,
    queue_limit: 100,
    polling_interval: 1,
    timeout: 30,
    retry_policy: 'exponential',

    // System 1
    council_mode: 'Consensus',
    minimum_confidence: 0.7,
    minimum_reviews: 2,
    fail_closed_on_disagreement: true,

    // System 2
    endpoint: 'http://127.0.0.1:8102',
    model: 'local-deterministic-v2.2',
    lifecycle: 'start',
    discovery: true,
    resource_limits: {
      cpu: 80,
      memory: 50,
    },

    // Security
    permission_mode: 'strict',
    approval_rules: 'confirm',
    critical_tool_policy: 'block',
    audit_retention: 30,

    // Memory
    enable_learning: true,
    recall_limit: 100,
    importance_threshold: 0.5,
    retention: 30,

    // Observability
    sse_enabled: true,
    websocket_enabled: false,
    polling_fallback: true,
    heartbeat_interval: 10,
    event_retention: 7,
  });
  const [activeTab, setActiveTab] = useState<'general' | 'agent' | 'runtime' | 'system1' | 'system2' | 'security' | 'memory' | 'observability'>('general');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  // Save settings
  const saveSettings = async () => {
    setLoading(true);
    setError(null);
    try {
      // Placeholder: In a real implementation, this would call backend endpoints
      // For now, just show a success message
      setMessage('Settings saved successfully!');
      setTimeout(() => setMessage(null), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  // Reset settings to defaults
  const resetSettings = () => {
    setSettings({
      // General
      application_name: 'Agentic-AI',
      timezone: 'UTC',
      language: 'en',
      ui_density: 'default',
      theme: 'dark',

      // Agent
      autonomy: 1,
      max_iterations: 5,
      max_retries: 2,
      confidence_threshold: 0.7,

      // Runtime
      max_concurrency: 4,
      queue_limit: 100,
      polling_interval: 1,
      timeout: 30,
      retry_policy: 'exponential',

      // System 1
      council_mode: 'Consensus',
      minimum_confidence: 0.7,
      minimum_reviews: 2,
      fail_closed_on_disagreement: true,

      // System 2
      endpoint: 'http://127.0.0.1:8102',
      model: 'local-deterministic-v2.2',
      lifecycle: 'start',
      discovery: true,
      resource_limits: {
        cpu: 80,
        memory: 50,
      },

      // Security
      permission_mode: 'strict',
      approval_rules: 'confirm',
      critical_tool_policy: 'block',
      audit_retention: 30,

      // Memory
      enable_learning: true,
      recall_limit: 100,
      importance_threshold: 0.5,
      retention: 30,

      // Observability
      sse_enabled: true,
      websocket_enabled: false,
      polling_fallback: true,
      heartbeat_interval: 10,
      event_retention: 7,
    });
    setMessage('Settings reset to defaults.');
    setTimeout(() => setMessage(null), 3000);
  };

  // Handle input changes
  const handleInputChange = (field: keyof Settings, value: any) => {
    setSettings((prev) => ({ ...prev, [field]: value }));
  };

  // Handle nested input changes (e.g., resource_limits.cpu)
  const handleNestedInputChange = (parent: keyof Settings, child: string, value: any) => {
    setSettings((prev) => ({
      ...prev,
      [parent]: { ...(prev[parent] as any), [child]: value },
    }));
  };

  return (
    <div className="page settings-page">
      <h1>Settings</h1>
      <p>Configure Agentic-AI behavior, appearance, and policies.</p>

      {/* Tabs */}
      <GlassCard title="">
        <div className="settings-tabs">
          {[
            { id: 'general', label: 'General' },
            { id: 'agent', label: 'Agent' },
            { id: 'runtime', label: 'Runtime' },
            { id: 'system1', label: 'System 1' },
            { id: 'system2', label: 'System 2' },
            { id: 'security', label: 'Security' },
            { id: 'memory', label: 'Memory' },
            { id: 'observability', label: 'Observability' },
          ].map((tab) => (
            <button
              key={tab.id}
              className={activeTab === tab.id ? 'active' : ''}
              onClick={() => setActiveTab(tab.id as any)}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </GlassCard>

      {/* Settings Form */}
      <GlassCard title="">
        {message && (
          <div className="settings-message">
            <StatusBadge status="success">{message}</StatusBadge>
          </div>
        )}
        {error && (
          <div className="settings-message">
            <StatusBadge status="error">{error}</StatusBadge>
          </div>
        )}

        <form onSubmit={(e) => { e.preventDefault(); saveSettings(); }}>
          {/* General Settings */}
          {activeTab === 'general' && (
            <div className="settings-section">
              <h2>General Settings</h2>
              <div className="settings-grid">
                <div className="settings-item">
                  <label>Application Name:</label>
                  <input
                    type="text"
                    value={settings.application_name}
                    onChange={(e) => handleInputChange('application_name', e.target.value)}
                  />
                </div>
                <div className="settings-item">
                  <label>Timezone:</label>
                  <select
                    value={settings.timezone}
                    onChange={(e) => handleInputChange('timezone', e.target.value)}
                  >
                    <option value="UTC">UTC</option>
                    <option value="America/New_York">America/New_York</option>
                    <option value="Europe/London">Europe/London</option>
                    <option value="Asia/Karachi">Asia/Karachi</option>
                  </select>
                </div>
                <div className="settings-item">
                  <label>Language:</label>
                  <select
                    value={settings.language}
                    onChange={(e) => handleInputChange('language', e.target.value)}
                  >
                    <option value="en">English</option>
                    <option value="ur">Urdu</option>
                  </select>
                </div>
                <div className="settings-item">
                  <label>UI Density:</label>
                  <select
                    value={settings.ui_density}
                    onChange={(e) => handleInputChange('ui_density', e.target.value as any)}
                  >
                    <option value="compact">Compact</option>
                    <option value="default">Default</option>
                    <option value="comfortable">Comfortable</option>
                  </select>
                </div>
                <div className="settings-item">
                  <label>Theme:</label>
                  <select
                    value={settings.theme}
                    onChange={(e) => handleInputChange('theme', e.target.value as any)}
                  >
                    <option value="dark">Dark</option>
                    <option value="light">Light</option>
                    <option value="system">System</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* Agent Settings */}
          {activeTab === 'agent' && (
            <div className="settings-section">
              <h2>Agent Settings</h2>
              <div className="settings-grid">
                <div className="settings-item">
                  <label>Autonomy Level (0-5):</label>
                  <input
                    type="number"
                    min="0"
                    max="5"
                    value={settings.autonomy}
                    onChange={(e) => handleInputChange('autonomy', Number(e.target.value))}
                  />
                  <small>Higher = more independent agent behavior</small>
                </div>
                <div className="settings-item">
                  <label>Max Iterations:</label>
                  <input
                    type="number"
                    min="1"
                    max="20"
                    value={settings.max_iterations}
                    onChange={(e) => handleInputChange('max_iterations', Number(e.target.value))}
                  />
                  <small>Maximum number of agent iterations per run</small>
                </div>
                <div className="settings-item">
                  <label>Max Retries:</label>
                  <input
                    type="number"
                    min="0"
                    max="10"
                    value={settings.max_retries}
                    onChange={(e) => handleInputChange('max_retries', Number(e.target.value))}
                  />
                  <small>Maximum number of retries for failed steps</small>
                </div>
                <div className="settings-item">
                  <label>Confidence Threshold (0-1):</label>
                  <input
                    type="number"
                    min="0"
                    max="1"
                    step="0.01"
                    value={settings.confidence_threshold}
                    onChange={(e) => handleInputChange('confidence_threshold', Number(e.target.value))}
                  />
                  <small>Minimum confidence score for agent decisions</small>
                </div>
              </div>
            </div>
          )}

          {/* Runtime Settings */}
          {activeTab === 'runtime' && (
            <div className="settings-section">
              <h2>Runtime Settings</h2>
              <div className="settings-grid">
                <div className="settings-item">
                  <label>Max Concurrency:</label>
                  <input
                    type="number"
                    min="1"
                    max="20"
                    value={settings.max_concurrency}
                    onChange={(e) => handleInputChange('max_concurrency', Number(e.target.value))}
                  />
                  <small>Maximum number of concurrent jobs</small>
                </div>
                <div className="settings-item">
                  <label>Queue Limit:</label>
                  <input
                    type="number"
                    min="1"
                    max="1000"
                    value={settings.queue_limit}
                    onChange={(e) => handleInputChange('queue_limit', Number(e.target.value))}
                  />
                  <small>Maximum number of jobs in the queue</small>
                </div>
                <div className="settings-item">
                  <label>Polling Interval (s):</label>
                  <input
                    type="number"
                    min="0.1"
                    max="10"
                    step="0.1"
                    value={settings.polling_interval}
                    onChange={(e) => handleInputChange('polling_interval', Number(e.target.value))}
                  />
                  <small>Interval for polling job status (seconds)</small>
                </div>
                <div className="settings-item">
                  <label>Timeout (s):</label>
                  <input
                    type="number"
                    min="1"
                    max="300"
                    value={settings.timeout}
                    onChange={(e) => handleInputChange('timeout', Number(e.target.value))}
                  />
                  <small>Timeout for job execution (seconds)</small>
                </div>
                <div className="settings-item">
                  <label>Retry Policy:</label>
                  <select
                    value={settings.retry_policy}
                    onChange={(e) => handleInputChange('retry_policy', e.target.value as any)}
                  >
                    <option value="exponential">Exponential Backoff</option>
                    <option value="linear">Linear Backoff</option>
                    <option value="none">No Retry</option>
                  </select>
                  <small>Strategy for retrying failed jobs</small>
                </div>
              </div>
            </div>
          )}

          {/* System 1 Settings */}
          {activeTab === 'system1' && (
            <div className="settings-section">
              <h2>System 1 Settings</h2>
              <div className="settings-grid">
                <div className="settings-item">
                  <label>Council Mode:</label>
                  <select
                    value={settings.council_mode}
                    onChange={(e) => handleInputChange('council_mode', e.target.value as any)}
                  >
                    <option value="Any">Any (One approval sufficient)</option>
                    <option value="All">All (All must approve)</option>
                    <option value="Consensus">Consensus (Majority wins)</option>
                  </select>
                  <small>Voting mode for the Council</small>
                </div>
                <div className="settings-item">
                  <label>Minimum Confidence (0-1):</label>
                  <input
                    type="number"
                    min="0"
                    max="1"
                    step="0.01"
                    value={settings.minimum_confidence}
                    onChange={(e) => handleInputChange('minimum_confidence', Number(e.target.value))}
                  />
                  <small>Minimum confidence score for Council decisions</small>
                </div>
                <div className="settings-item">
                  <label>Minimum Reviews:</label>
                  <input
                    type="number"
                    min="1"
                    max="10"
                    value={settings.minimum_reviews}
                    onChange={(e) => handleInputChange('minimum_reviews', Number(e.target.value))}
                  />
                  <small>Minimum number of Council reviews required</small>
                </div>
                <div className="settings-item">
                  <label>Fail Closed on Disagreement:</label>
                  <input
                    type="checkbox"
                    checked={settings.fail_closed_on_disagreement}
                    onChange={(e) => handleInputChange('fail_closed_on_disagreement', e.target.checked)}
                  />
                  <small>If Council disagrees, default to DENY</small>
                </div>
              </div>
            </div>
          )}

          {/* System 2 Settings */}
          {activeTab === 'system2' && (
            <div className="settings-section">
              <h2>System 2 Settings</h2>
              <div className="settings-grid">
                <div className="settings-item">
                  <label>Endpoint:</label>
                  <input
                    type="text"
                    value={settings.endpoint}
                    onChange={(e) => handleInputChange('endpoint', e.target.value)}
                  />
                  <small>System 2 backend endpoint (must be loopback)</small>
                </div>
                <div className="settings-item">
                  <label>Active Model:</label>
                  <input
                    type="text"
                    value={settings.model}
                    onChange={(e) => handleInputChange('model', e.target.value)}
                  />
                  <small>Currently active System 2 model</small>
                </div>
                <div className="settings-item">
                  <label>Lifecycle:</label>
                  <select
                    value={settings.lifecycle}
                    onChange={(e) => handleInputChange('lifecycle', e.target.value as any)}
                  >
                    <option value="start">Start</option>
                    <option value="stop">Stop</option>
                    <option value="restart">Restart</option>
                    <option value="update">Update</option>
                    <option value="upgrade">Upgrade</option>
                  </select>
                  <small>System 2 lifecycle control</small>
                </div>
                <div className="settings-item">
                  <label>Enable Discovery:</label>
                  <input
                    type="checkbox"
                    checked={settings.discovery}
                    onChange={(e) => handleInputChange('discovery', e.target.checked)}
                  />
                  <small>Automatically discover local models</small>
                </div>
                <div className="settings-item">
                  <label>CPU Limit (%):</label>
                  <input
                    type="number"
                    min="1"
                    max="100"
                    value={settings.resource_limits.cpu}
                    onChange={(e) => handleNestedInputChange('resource_limits', 'cpu', Number(e.target.value))}
                  />
                  <small>Maximum CPU usage for System 2</small>
                </div>
                <div className="settings-item">
                  <label>Memory Limit (%):</label>
                  <input
                    type="number"
                    min="1"
                    max="100"
                    value={settings.resource_limits.memory}
                    onChange={(e) => handleNestedInputChange('resource_limits', 'memory', Number(e.target.value))}
                  />
                  <small>Maximum memory usage for System 2</small>
                </div>
              </div>
            </div>
          )}

          {/* Security Settings */}
          {activeTab === 'security' && (
            <div className="settings-section">
              <h2>Security Settings</h2>
              <div className="settings-grid">
                <div className="settings-item">
                  <label>Permission Mode:</label>
                  <select
                    value={settings.permission_mode}
                    onChange={(e) => handleInputChange('permission_mode', e.target.value as any)}
                  >
                    <option value="strict">Strict (Deny by default)</option>
                    <option value="lenient">Lenient (Allow by default)</option>
                    <option value="custom">Custom (Configure per-tool)</option>
                  </select>
                  <small>Default permission mode for tools</small>
                </div>
                <div className="settings-item">
                  <label>Approval Rules:</label>
                  <select
                    value={settings.approval_rules}
                    onChange={(e) => handleInputChange('approval_rules', e.target.value as any)}
                  >
                    <option value="auto">Auto (No approval required)</option>
                    <option value="confirm">Confirm (User approval required)</option>
                    <option value="deny">Deny (Always blocked)</option>
                  </select>
                  <small>Default approval rule for tools</small>
                </div>
                <div className="settings-item">
                  <label>Critical Tool Policy:</label>
                  <select
                    value={settings.critical_tool_policy}
                    onChange={(e) => handleInputChange('critical_tool_policy', e.target.value as any)}
                  >
                    <option value="block">Block (Always denied)</option>
                    <option value="confirm">Confirm (User approval required)</option>
                    <option value="allow">Allow (No restrictions)</option>
                  </select>
                  <small>Policy for CRITICAL risk tools</small>
                </div>
                <div className="settings-item">
                  <label>Audit Retention (days):</label>
                  <input
                    type="number"
                    min="1"
                    max="365"
                    value={settings.audit_retention}
                    onChange={(e) => handleInputChange('audit_retention', Number(e.target.value))}
                  />
                  <small>Number of days to retain audit logs</small>
                </div>
              </div>
            </div>
          )}

          {/* Memory Settings */}
          {activeTab === 'memory' && (
            <div className="settings-section">
              <h2>Memory Settings</h2>
              <div className="settings-grid">
                <div className="settings-item">
                  <label>Enable Learning:</label>
                  <input
                    type="checkbox"
                    checked={settings.enable_learning}
                    onChange={(e) => handleInputChange('enable_learning', e.target.checked)}
                  />
                  <small>Allow the agent to learn from past experiences</small>
                </div>
                <div className="settings-item">
                  <label>Recall Limit:</label>
                  <input
                    type="number"
                    min="1"
                    max="1000"
                    value={settings.recall_limit}
                    onChange={(e) => handleInputChange('recall_limit', Number(e.target.value))}
                  />
                  <small>Maximum number of memories to recall</small>
                </div>
                <div className="settings-item">
                  <label>Importance Threshold (0-1):</label>
                  <input
                    type="number"
                    min="0"
                    max="1"
                    step="0.01"
                    value={settings.importance_threshold}
                    onChange={(e) => handleInputChange('importance_threshold', Number(e.target.value))}
                  />
                  <small>Minimum importance score for memories</small>
                </div>
                <div className="settings-item">
                  <label>Retention (days):</label>
                  <input
                    type="number"
                    min="1"
                    max="365"
                    value={settings.retention}
                    onChange={(e) => handleInputChange('retention', Number(e.target.value))}
                  />
                  <small>Number of days to retain memories</small>
                </div>
              </div>
            </div>
          )}

          {/* Observability Settings */}
          {activeTab === 'observability' && (
            <div className="settings-section">
              <h2>Observability Settings</h2>
              <div className="settings-grid">
                <div className="settings-item">
                  <label>Enable SSE:</label>
                  <input
                    type="checkbox"
                    checked={settings.sse_enabled}
                    onChange={(e) => handleInputChange('sse_enabled', e.target.checked)}
                  />
                  <small>Enable Server-Sent Events for real-time updates</small>
                </div>
                <div className="settings-item">
                  <label>Enable WebSocket:</label>
                  <input
                    type="checkbox"
                    checked={settings.websocket_enabled}
                    onChange={(e) => handleInputChange('websocket_enabled', e.target.checked)}
                  />
                  <small>Enable WebSocket for real-time updates</small>
                </div>
                <div className="settings-item">
                  <label>Polling Fallback:</label>
                  <input
                    type="checkbox"
                    checked={settings.polling_fallback}
                    onChange={(e) => handleInputChange('polling_fallback', e.target.checked)}
                  />
                  <small>Fallback to polling if SSE/WebSocket fails</small>
                </div>
                <div className="settings-item">
                  <label>Heartbeat Interval (s):</label>
                  <input
                    type="number"
                    min="1"
                    max="60"
                    value={settings.heartbeat_interval}
                    onChange={(e) => handleInputChange('heartbeat_interval', Number(e.target.value))}
                  />
                  <small>Interval for sending heartbeat events (seconds)</small>
                </div>
                <div className="settings-item">
                  <label>Event Retention (days):</label>
                  <input
                    type="number"
                    min="1"
                    max="365"
                    value={settings.event_retention}
                    onChange={(e) => handleInputChange('event_retention', Number(e.target.value))}
                  />
                  <small>Number of days to retain events</small>
                </div>
              </div>
            </div>
          )}

          {/* Save/Reset Buttons */}
          <div className="settings-actions">
            <button type="button" className="ghost" onClick={resetSettings} disabled={loading}>
              Reset to Defaults
            </button>
            <button type="submit" disabled={loading}>
              {loading ? 'Saving...' : 'Save Settings'}
            </button>
          </div>
        </form>
      </GlassCard>

      {/* Settings Rules */}
      <GlassCard title="Settings Rules">
        <div className="settings-rules">
          <h3>🔧 Configuration Notes:</h3>
          <ul>
            <li>✓ Settings are <strong>persisted in SQLite</strong>.</li>
            <li>✓ Changes take effect <strong>immediately</strong>.</li>
            <li>✓ Some settings require a <strong>restart</strong> to take effect.</li>
            <li>✓ System 1 settings <strong>cannot be modified by System 2</strong>.</li>
            <li>✓ Security settings are <strong>audited</strong>.</li>
          </ul>
        </div>
      </GlassCard>
    </div>
  );
};

export default SettingsPage;
