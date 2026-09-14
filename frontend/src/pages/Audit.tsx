import React, { useState, useEffect } from 'react';
import { GlassCard, StatusBadge } from '../components';

interface AuditEvent {
  event_id: string;
  timestamp: string;
  actor: string;
  action: string;
  run_id?: string;
  task_id?: string;
  result: string;
  risk: string;
  metadata?: any;
}

const AuditPage: React.FC = () => {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [filteredEvents, setFilteredEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState({
    actor: '',
    action: '',
    run_id: '',
    task_id: '',
    risk: '',
    startDate: '',
    endDate: '',
  });
  const [eventSource, setEventSource] = useState<EventSource | null>(null);

  // Fetch audit events
  useEffect(() => {
    const fetchAuditEvents = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8101/api/system1/audit?limit=100');
        if (!response.ok) {
          throw new Error('Failed to fetch audit events');
        }
        const data = await response.json();
        setEvents(data.events || []);
        setFilteredEvents(data.events || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };
    fetchAuditEvents();

    // Set up SSE for live audit events
    const setupSSE = () => {
      const es = new EventSource('http://127.0.0.1:8000/api/observability/events');
      es.onmessage = (e) => {
        const event = JSON.parse(e.data);
        if (event.event_type === 'security_violation' || event.event_type.includes('audit')) {
          setEvents((prev) => [event, ...prev].slice(0, 100));
          applyFilters([event, ...events].slice(0, 100));
        }
      };
      es.onerror = () => {
        es.close();
        setTimeout(setupSSE, 5000); // Reconnect after 5 seconds
      };
      setEventSource(es);
    };
    setupSSE();

    return () => {
      if (eventSource) {
        eventSource.close();
      }
    };
  }, []);

  // Apply filters
  const applyFilters = (eventsToFilter: AuditEvent[] = events) => {
    let filtered = [...eventsToFilter];

    if (filters.actor) {
      filtered = filtered.filter((event) => event.actor.includes(filters.actor));
    }
    if (filters.action) {
      filtered = filtered.filter((event) => event.action.includes(filters.action));
    }
    if (filters.run_id) {
      filtered = filtered.filter((event) => event.run_id?.includes(filters.run_id));
    }
    if (filters.task_id) {
      filtered = filtered.filter((event) => event.task_id?.includes(filters.task_id));
    }
    if (filters.risk) {
      filtered = filtered.filter((event) => event.risk === filters.risk);
    }
    if (filters.startDate) {
      filtered = filtered.filter((event) => new Date(event.timestamp) >= new Date(filters.startDate));
    }
    if (filters.endDate) {
      filtered = filtered.filter((event) => new Date(event.timestamp) <= new Date(filters.endDate));
    }

    setFilteredEvents(filtered);
  };

  // Handle filter changes
  const handleFilterChange = (field: keyof typeof filters, value: string) => {
    setFilters((prev) => ({ ...prev, [field]: value }));
  };

  // Apply filters when they change
  useEffect(() => {
    applyFilters();
  }, [filters]);

  // Export events as JSON
  const exportEvents = () => {
    const dataStr = JSON.stringify(filteredEvents, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'audit_events.json';
    link.click();
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="page audit-page">
        <h1>Audit</h1>
        <p>Loading audit events...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page audit-page">
        <h1>Audit</h1>
        <StatusBadge status="error">Error: {error}</StatusBadge>
      </div>
    );
  }

  return (
    <div className="page audit-page">
      <h1>Audit</h1>
      <p>
        Searchable audit log of all security-sensitive events.
        Events are logged by System 1 and include Council decisions, tool permissions, and security violations.
      </p>

      {/* Filters */}
      <GlassCard title="Filters">
        <div className="audit-filters">
          <div className="filter-group">
            <label>Actor:</label>
            <input
              type="text"
              placeholder="e.g., System2, Council"
              value={filters.actor}
              onChange={(e) => handleFilterChange('actor', e.target.value)}
            />
          </div>
          <div className="filter-group">
            <label>Action:</label>
            <input
              type="text"
              placeholder="e.g., council_decision, permission_denied"
              value={filters.action}
              onChange={(e) => handleFilterChange('action', e.target.value)}
            />
          </div>
          <div className="filter-group">
            <label>Run ID:</label>
            <input
              type="text"
              placeholder="e.g., run_12345678"
              value={filters.run_id}
              onChange={(e) => handleFilterChange('run_id', e.target.value)}
            />
          </div>
          <div className="filter-group">
            <label>Task ID:</label>
            <input
              type="text"
              placeholder="e.g., task_12345678"
              value={filters.task_id}
              onChange={(e) => handleFilterChange('task_id', e.target.value)}
            />
          </div>
          <div className="filter-group">
            <label>Risk:</label>
            <select
              value={filters.risk}
              onChange={(e) => handleFilterChange('risk', e.target.value)}
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
            <label>Start Date:</label>
            <input
              type="datetime-local"
              value={filters.startDate}
              onChange={(e) => handleFilterChange('startDate', e.target.value)}
            />
          </div>
          <div className="filter-group">
            <label>End Date:</label>
            <input
              type="datetime-local"
              value={filters.endDate}
              onChange={(e) => handleFilterChange('endDate', e.target.value)}
            />
          </div>
          <div className="filter-actions">
            <button className="ghost" onClick={() => setFilters({
              actor: '',
              action: '',
              run_id: '',
              task_id: '',
              risk: '',
              startDate: '',
              endDate: '',
            })}>
              Clear Filters
            </button>
            <button onClick={exportEvents}>Export JSON</button>
          </div>
        </div>
      </GlassCard>

      {/* Audit Events Table */}
      <GlassCard title="Audit Events">
        <div className="audit-table-container">
          {filteredEvents.length ? (
            <table className="audit-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Actor</th>
                  <th>Action</th>
                  <th>Run ID</th>
                  <th>Task ID</th>
                  <th>Result</th>
                  <th>Risk</th>
                  <th>Metadata</th>
                </tr>
              </thead>
              <tbody>
                {filteredEvents.map((event) => (
                  <tr key={event.event_id} className={event.risk === 'CRITICAL' ? 'critical-row' : event.risk === 'HIGH' ? 'high-row' : ''}>
                    <td>{new Date(event.timestamp).toLocaleString()}</td>
                    <td>{event.actor}</td>
                    <td>{event.action}</td>
                    <td>{event.run_id?.slice(0, 8) || 'N/A'}</td>
                    <td>{event.task_id?.slice(0, 8) || 'N/A'}</td>
                    <td>
                      <StatusBadge status={getResultColor(event.result)}>{event.result}</StatusBadge>
                    </td>
                    <td>
                      <StatusBadge status={getRiskColor(event.risk)}>{event.risk}</StatusBadge>
                    </td>
                    <td>
                      {event.metadata && (
                        <details>
                          <summary>View</summary>
                          <pre>{JSON.stringify(event.metadata, null, 2)}</pre>
                        </details>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p>No audit events match the filters.</p>
          )}
        </div>
      </GlassCard>

      {/* Audit Rules */}
      <GlassCard title="Audit Rules">
        <div className="audit-rules">
          <h3>What is Audited:</h3>
          <ul>
            <li>✓ <strong>Council Decisions</strong>: All votes and final decisions.</li>
            <li>✓ <strong>Tool Permissions</strong>: Granted/denied tool executions.</li>
            <li>✓ <strong>Security Violations</strong>: Any attempt to bypass System 1.</li>
            <li>✓ <strong>Provider Changes</strong>: Enabling/disabling System 1 providers.</li>
            <li>✓ <strong>Model Changes</strong>: Activating/deactivating System 2 models.</li>
            <li>✓ <strong>Recovery Actions</strong>: Requeue, resume, cancel jobs.</li>
          </ul>
          <h3>Risk Levels:</h3>
          <ul>
            <li><StatusBadge status="success">SAFE</StatusBadge>: Non-sensitive actions (e.g., model discovery).</li>
            <li><StatusBadge status="info">LOW</StatusBadge>: Routine actions (e.g., task creation).</li>
            <li><StatusBadge status="warning">MEDIUM</StatusBadge>: Important actions (e.g., provider disable).</li>
            <li><StatusBadge status="danger">HIGH</StatusBadge>: Critical actions (e.g., Council override).</li>
            <li><StatusBadge status="error">CRITICAL</StatusBadge>: Security violations (e.g., System 2 stop attempt).</li>
          </ul>
        </div>
      </GlassCard>
    </div>
  );
};

// Helper functions
function getResultColor(result: string): string {
  switch (result.toLowerCase()) {
    case 'allow':
    case 'success':
    case 'passed':
      return 'success';
    case 'deny':
    case 'failed':
    case 'blocked':
      return 'danger';
    case 'escalate':
      return 'warning';
    default:
      return 'info';
  }
}

function getRiskColor(risk: string): string {
  switch (risk.toLowerCase()) {
    case 'critical':
      return 'error';
    case 'high':
      return 'danger';
    case 'medium':
      return 'warning';
    case 'low':
      return 'info';
    case 'safe':
      return 'success';
    default:
      return 'neutral';
  }
}

export default AuditPage;
