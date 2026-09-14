import React, { useState, useEffect } from 'react';
import { GlassCard, StatusBadge, PermissionGate } from '../components';

interface Tool {
  name: string;
  description: string;
  category: string;
  risk: 'SAFE' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  policy: 'AUTO' | 'CONFIRM' | 'DENY';
  enabled: boolean;
  requires_permission: boolean;
  default_permission: boolean;
}

interface ToolStats {
  total: number;
  safe: number;
  low: number;
  medium: number;
  high: number;
  critical: number;
  auto: number;
  confirm: number;
  deny: number;
  enabled: number;
  disabled: number;
}

const ToolsPage: React.FC = () => {
  const [tools, setTools] = useState<Tool[]>([]);
  const [filteredTools, setFilteredTools] = useState<Tool[]>([]);
  const [stats, setStats] = useState<ToolStats | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState({
    category: '',
    risk: '',
    policy: '',
    enabled: '',
    search: '',
  });

  // Fetch tools
  useEffect(() => {
    const fetchTools = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8000/api/tools');
        if (!response.ok) {
          throw new Error('Failed to fetch tools');
        }
        const data = await response.json();
        const toolsList: Tool[] = Object.entries(data).map(([name, tool]: [string, any]) => ({
          name,
          description: tool.description || 'No description',
          category: tool.category || 'other',
          risk: tool.risk || 'LOW',
          policy: tool.policy || 'CONFIRM',
          enabled: tool.enabled !== false,
          requires_permission: tool.requires_permission !== false,
          default_permission: tool.default_permission || false,
        }));
        setTools(toolsList);
        setFilteredTools(toolsList);

        // Calculate stats
        const safe = toolsList.filter((t) => t.risk === 'SAFE').length;
        const low = toolsList.filter((t) => t.risk === 'LOW').length;
        const medium = toolsList.filter((t) => t.risk === 'MEDIUM').length;
        const high = toolsList.filter((t) => t.risk === 'HIGH').length;
        const critical = toolsList.filter((t) => t.risk === 'CRITICAL').length;
        const auto = toolsList.filter((t) => t.policy === 'AUTO').length;
        const confirm = toolsList.filter((t) => t.policy === 'CONFIRM').length;
        const deny = toolsList.filter((t) => t.policy === 'DENY').length;
        const enabled = toolsList.filter((t) => t.enabled).length;
        const disabled = toolsList.filter((t) => !t.enabled).length;

        setStats({
          total: toolsList.length,
          safe,
          low,
          medium,
          high,
          critical,
          auto,
          confirm,
          deny,
          enabled,
          disabled,
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };
    fetchTools();
  }, []);

  // Apply filters
  useEffect(() => {
    let filtered = [...tools];

    if (filters.category) {
      filtered = filtered.filter((t) => t.category === filters.category);
    }

    if (filters.risk) {
      filtered = filtered.filter((t) => t.risk === filters.risk);
    }

    if (filters.policy) {
      filtered = filtered.filter((t) => t.policy === filters.policy);
    }

    if (filters.enabled) {
      filtered = filtered.filter((t) => t.enabled === (filters.enabled === 'enabled'));
    }

    if (filters.search) {
      filtered = filtered.filter((t) =>
        t.name.toLowerCase().includes(filters.search.toLowerCase()) ||
        t.description.toLowerCase().includes(filters.search.toLowerCase())
      );
    }

    setFilteredTools(filtered);
  }, [filters, tools]);

  // Update tool policy
  const updateToolPolicy = async (toolName: string, policy: 'AUTO' | 'CONFIRM' | 'DENY') => {
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/tools/${toolName}/policy`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ policy }),
      });
      if (!response.ok) {
        throw new Error('Failed to update tool policy');
      }
      // Refresh tools
      const toolsRes = await fetch('http://127.0.0.1:8000/api/tools');
      if (toolsRes.ok) {
        const toolsData = await toolsRes.json();
        const toolsList: Tool[] = Object.entries(toolsData).map(([name, tool]: [string, any]) => ({
          name,
          description: tool.description || 'No description',
          category: tool.category || 'other',
          risk: tool.risk || 'LOW',
          policy: tool.policy || 'CONFIRM',
          enabled: tool.enabled !== false,
          requires_permission: tool.requires_permission !== false,
          default_permission: tool.default_permission || false,
        }));
        setTools(toolsList);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  // Toggle tool enabled status
  const toggleToolEnabled = async (toolName: string, enabled: boolean) => {
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/tools/${toolName}/policy`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled }),
      });
      if (!response.ok) {
        throw new Error('Failed to toggle tool enabled status');
      }
      // Refresh tools
      const toolsRes = await fetch('http://127.0.0.1:8000/api/tools');
      if (toolsRes.ok) {
        const toolsData = await toolsRes.json();
        const toolsList: Tool[] = Object.entries(toolsData).map(([name, tool]: [string, any]) => ({
          name,
          description: tool.description || 'No description',
          category: tool.category || 'other',
          risk: tool.risk || 'LOW',
          policy: tool.policy || 'CONFIRM',
          enabled: tool.enabled !== false,
          requires_permission: tool.requires_permission !== false,
          default_permission: tool.default_permission || false,
        }));
        setTools(toolsList);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  if (loading) {
    return (
      <div className="page tools-page">
        <h1>Tools</h1>
        <p>Loading tools...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page tools-page">
        <h1>Tools</h1>
        <StatusBadge status="error">Error: {error}</StatusBadge>
      </div>
    );
  }

  return (
    <div className="page tools-page">
      <h1>Tools</h1>
      <p>
        Tool registry and permissions. System 1 enforces tool permissions for all executions.
      </p>

      {/* Tool Stats */}
      <GlassCard title="Tool Stats">
        <div className="tool-stats-grid">
          <div className="tool-stat">
            <strong>Total Tools:</strong> {stats?.total || 0}
          </div>
          <div className="tool-stat">
            <strong>Enabled:</strong> {stats?.enabled || 0}
          </div>
          <div className="tool-stat">
            <strong>Disabled:</strong> {stats?.disabled || 0}
          </div>
          <div className="tool-stat">
            <strong>Risk Levels:</strong>
            <ul>
              <li><StatusBadge status="success">SAFE</StatusBadge>: {stats?.safe || 0}</li>
              <li><StatusBadge status="info">LOW</StatusBadge>: {stats?.low || 0}</li>
              <li><StatusBadge status="warning">MEDIUM</StatusBadge>: {stats?.medium || 0}</li>
              <li><StatusBadge status="danger">HIGH</StatusBadge>: {stats?.high || 0}</li>
              <li><StatusBadge status="error">CRITICAL</StatusBadge>: {stats?.critical || 0}</li>
            </ul>
          </div>
          <div className="tool-stat">
            <strong>Policies:</strong>
            <ul>
              <li><StatusBadge status="success">AUTO</StatusBadge>: {stats?.auto || 0}</li>
              <li><StatusBadge status="warning">CONFIRM</StatusBadge>: {stats?.confirm || 0}</li>
              <li><StatusBadge status="danger">DENY</StatusBadge>: {stats?.deny || 0}</li>
            </ul>
          </div>
        </div>
      </GlassCard>

      {/* Filters */}
      <GlassCard title="Filters">
        <div className="tool-filters">
          <div className="filter-group">
            <label>Category:</label>
            <select
              value={filters.category}
              onChange={(e) => setFilters({ ...filters, category: e.target.value })}
            >
              <option value="">All</option>
              <option value="filesystem">Filesystem</option>
              <option value="network">Network</option>
              <option value="process">Process</option>
              <option value="utility">Utility</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div className="filter-group">
            <label>Risk:</label>
            <select
              value={filters.risk}
              onChange={(e) => setFilters({ ...filters, risk: e.target.value as any })}
            >
              <option value="">All</option>
              <option value="SAFE">SAFE</option>
              <option value="LOW">LOW</option>
              <option value="MEDIUM">MEDIUM</option>
              <option value="HIGH">HIGH</option>
              <option value="CRITICAL">CRITICAL</option>
            </select>
          </div>
          <div className="filter-group">
            <label>Policy:</label>
            <select
              value={filters.policy}
              onChange={(e) => setFilters({ ...filters, policy: e.target.value as any })}
            >
              <option value="">All</option>
              <option value="AUTO">AUTO</option>
              <option value="CONFIRM">CONFIRM</option>
              <option value="DENY">DENY</option>
            </select>
          </div>
          <div className="filter-group">
            <label>Enabled:</label>
            <select
              value={filters.enabled}
              onChange={(e) => setFilters({ ...filters, enabled: e.target.value })}
            >
              <option value="">All</option>
              <option value="enabled">Enabled</option>
              <option value="disabled">Disabled</option>
            </select>
          </div>
          <div className="filter-group">
            <label>Search:</label>
            <input
              type="text"
              placeholder="Search tools..."
              value={filters.search}
              onChange={(e) => setFilters({ ...filters, search: e.target.value })}
            />
          </div>
          <div className="filter-actions">
            <button className="ghost" onClick={() => setFilters({
              category: '',
              risk: '',
              policy: '',
              enabled: '',
              search: '',
            })}>
              Clear Filters
            </button>
          </div>
        </div>
      </GlassCard>

      {/* Tools List */}
      <GlassCard title="Tools">
        <div className="tools-list">
          {filteredTools.length ? (
            <table className="tools-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Category</th>
                  <th>Risk</th>
                  <th>Policy</th>
                  <th>Enabled</th>
                  <th>Description</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredTools.map((tool) => (
                  <tr key={tool.name} className={tool.risk === 'CRITICAL' ? 'critical-row' : tool.risk === 'HIGH' ? 'high-row' : ''}>
                    <td>{tool.name}</td>
                    <td>{tool.category}</td>
                    <td>
                      <StatusBadge status={getRiskColor(tool.risk)}>{tool.risk}</StatusBadge>
                    </td>
                    <td>
                      <StatusBadge status={getPolicyColor(tool.policy)}>{tool.policy}</StatusBadge>
                    </td>
                    <td>
                      <StatusBadge status={tool.enabled ? 'success' : 'warning'}>
                        {tool.enabled ? '✓' : '✗'}
                      </StatusBadge>
                    </td>
                    <td>{tool.description}</td>
                    <td>
                      <div className="tool-actions">
                        <select
                          value={tool.policy}
                          onChange={(e) => updateToolPolicy(tool.name, e.target.value as any)}
                        >
                          <option value="AUTO">AUTO</option>
                          <option value="CONFIRM">CONFIRM</option>
                          <option value="DENY">DENY</option>
                        </select>
                        <button onClick={() => toggleToolEnabled(tool.name, !tool.enabled)}>
                          {tool.enabled ? 'Disable' : 'Enable'}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p>No tools match the filters.</p>
          )}
        </div>
      </GlassCard>

      {/* Tool Rules */}
      <GlassCard title="Tool Rules">
        <div className="tool-rules">
          <h3>🔧 Tool Permissions:</h3>
          <ul>
            <li>
              <strong>System 1 enforces tool permissions.</strong>
              <p>No tool can execute without explicit <code>ALLOW</code> permission from System 1.</p>
            </li>
            <li>
              <strong>Policies:</strong>
              <ul>
                <li><StatusBadge status="success">AUTO</StatusBadge>: Tool can execute without confirmation.</li>
                <li><StatusBadge status="warning">CONFIRM</StatusBadge>: User must confirm before execution.</li>
                <li><StatusBadge status="danger">DENY</StatusBadge>: Tool is blocked from execution.</li>
              </ul>
            </li>
            <li>
              <strong>Risk Levels:</strong>
              <ul>
                <li><StatusBadge status="success">SAFE</StatusBadge>: No restrictions (e.g., read-only tools).</li>
                <li><StatusBadge status="info">LOW</StatusBadge>: Minimal restrictions (e.g., network requests).</li>
                <li><StatusBadge status="warning">MEDIUM</StatusBadge>: Moderate restrictions (e.g., file writes).</li>
                <li><StatusBadge status="danger">HIGH</StatusBadge>: Strict restrictions (e.g., process management).</li>
                <li><StatusBadge status="error">CRITICAL</StatusBadge>: Blocked by default (e.g., shell commands).</li>
              </ul>
            </li>
          </ul>

          <h3>🛡️ Security:</h3>
          <ul>
            <li>✓ <strong>Critical tools are blocked by default.</strong></li>
            <li>✓ <strong>All tool executions are audited.</strong></li>
            <li>✓ <strong>System 2 cannot bypass tool permissions.</strong></li>
            <li>✓ <strong>Unknown tools fail closed.</strong></li>
          </ul>
        </div>
      </GlassCard>
    </div>
  );
};

// Helper functions
function getRiskColor(risk: string): string {
  switch (risk) {
    case 'SAFE':
      return 'success';
    case 'LOW':
      return 'info';
    case 'MEDIUM':
      return 'warning';
    case 'HIGH':
      return 'danger';
    case 'CRITICAL':
      return 'error';
    default:
      return 'neutral';
  }
}

function getPolicyColor(policy: string): string {
  switch (policy) {
    case 'AUTO':
      return 'success';
    case 'CONFIRM':
      return 'warning';
    case 'DENY':
      return 'danger';
    default:
      return 'neutral';
  }
}

export default ToolsPage;
