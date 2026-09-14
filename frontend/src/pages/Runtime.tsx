import React, { useState, useEffect } from 'react';
import { GlassCard, StatusBadge, HealthIndicator, MetricCard } from '../components';

interface QueueJob {
  job_id: string;
  run_id: string;
  task_id: string;
  priority: number;
  status: string;
  queued_at: string;
  started_at?: string;
  completed_at?: string;
  worker?: string;
  retry_count: number;
  error?: string;
}

interface RuntimeMetrics {
  workers: number;
  concurrency: number;
  queue_limit: number;
  queued: number;
  running: number;
  completed: number;
  failed: number;
  cancelled: number;
}

interface RuntimeConfig {
  max_concurrency: number;
  queue_limit: number;
  polling_interval: number;
}

const RuntimePage: React.FC = () => {
  const [queue, setQueue] = useState<QueueJob[]>([]);
  const [metrics, setMetrics] = useState<RuntimeMetrics | null>(null);
  const [config, setConfig] = useState<RuntimeConfig | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch queue, metrics, and config
  useEffect(() => {
    const fetchRuntimeData = async () => {
      try {
        // Fetch queue
        const queueRes = await fetch('http://127.0.0.1:8000/api/runtime/queue');
        if (!queueRes.ok) {
          throw new Error('Failed to fetch queue');
        }
        const queueData = await queueRes.json();
        setQueue(queueData.jobs || []);

        // Fetch metrics (placeholder: use queue data for now)
        const queued = queueData.jobs.filter((job: QueueJob) => job.status === 'queued').length;
        const running = queueData.jobs.filter((job: QueueJob) => job.status === 'running').length;
        const completed = queueData.jobs.filter((job: QueueJob) => job.status === 'completed').length;
        const failed = queueData.jobs.filter((job: QueueJob) => job.status === 'failed').length;
        const cancelled = queueData.jobs.filter((job: QueueJob) => job.status === 'cancelled').length;

        setMetrics({
          workers: 4, // Placeholder
          concurrency: 2, // Placeholder
          queue_limit: 100, // Placeholder
          queued,
          running,
          completed,
          failed,
          cancelled,
        });

        // Fetch config (placeholder)
        setConfig({
          max_concurrency: 4,
          queue_limit: 100,
          polling_interval: 1,
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };
    fetchRuntimeData();
  }, []);

  // Update runtime config
  const updateConfig = async (field: keyof RuntimeConfig, value: number) => {
    try {
      // Placeholder: In a real implementation, this would call a backend endpoint
      setConfig((prev) => prev ? { ...prev, [field]: value } : null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  if (loading) {
    return (
      <div className="page runtime-page">
        <h1>Runtime</h1>
        <p>Loading runtime data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page runtime-page">
        <h1>Runtime</h1>
        <StatusBadge status="error">Error: {error}</StatusBadge>
      </div>
    );
  }

  return (
    <div className="page runtime-page">
      <h1>Runtime</h1>
      <p>
        Manage the job queue, concurrency, and runtime configuration.
        All jobs are persisted in SQLite for recovery.
      </p>

      {/* Runtime Metrics */}
      <GlassCard title="Runtime Metrics">
        <div className="metrics-grid">
          <MetricCard
            title="Queued Jobs"
            value={metrics?.queued || 0}
            subtitle="Jobs waiting in queue"
          />
          <MetricCard
            title="Running Jobs"
            value={metrics?.running || 0}
            subtitle="Jobs currently executing"
          />
          <MetricCard
            title="Completed Jobs"
            value={metrics?.completed || 0}
            subtitle="Jobs finished successfully"
          />
          <MetricCard
            title="Failed Jobs"
            value={metrics?.failed || 0}
            subtitle="Jobs that failed"
          />
          <MetricCard
            title="Cancelled Jobs"
            value={metrics?.cancelled || 0}
            subtitle="Jobs that were cancelled"
          />
          <MetricCard
            title="Workers"
            value={metrics?.workers || 0}
            subtitle="Active worker threads"
          />
          <MetricCard
            title="Concurrency"
            value={metrics?.concurrency || 0}
            subtitle="Max concurrent jobs"
          />
          <MetricCard
            title="Queue Limit"
            value={metrics?.queue_limit || 0}
            subtitle="Max jobs in queue"
          />
        </div>
      </GlassCard>

      {/* Runtime Configuration */}
      <GlassCard title="Runtime Configuration">
        <div className="runtime-config">
          <div className="config-item">
            <div>
              <strong>Max Concurrency:</strong>
              <input
                type="number"
                min="1"
                max="20"
                value={config?.max_concurrency || 0}
                onChange={(e) => updateConfig('max_concurrency', Number(e.target.value))}
              />
            </div>
            <small>Maximum number of concurrent jobs</small>
          </div>
          <div className="config-item">
            <div>
              <strong>Queue Limit:</strong>
              <input
                type="number"
                min="1"
                max="1000"
                value={config?.queue_limit || 0}
                onChange={(e) => updateConfig('queue_limit', Number(e.target.value))}
              />
            </div>
            <small>Maximum number of jobs in the queue</small>
          </div>
          <div className="config-item">
            <div>
              <strong>Polling Interval (s):</strong>
              <input
                type="number"
                min="0.1"
                max="10"
                step="0.1"
                value={config?.polling_interval || 0}
                onChange={(e) => updateConfig('polling_interval', Number(e.target.value))}
              />
            </div>
            <small>Interval for polling job status (seconds)</small>
          </div>
        </div>
      </GlassCard>

      {/* Job Queue */}
      <GlassCard title="Job Queue">
        <div className="queue-actions">
          <button className="ghost" onClick={() => window.location.reload()}>Refresh</button>
        </div>
        {queue.length ? (
          <table className="queue-table">
            <thead>
              <tr>
                <th>Position</th>
                <th>Job ID</th>
                <th>Run ID</th>
                <th>Task ID</th>
                <th>Status</th>
                <th>Priority</th>
                <th>Queued At</th>
                <th>Retry Count</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {queue.map((job, index) => (
                <tr key={job.job_id}>
                  <td>{index + 1}</td>
                  <td>{job.job_id.slice(0, 8)}</td>
                  <td>{job.run_id.slice(0, 8)}</td>
                  <td>{job.task_id.slice(0, 8)}</td>
                  <td>
                    <StatusBadge status={getStatusColor(job.status)}>{job.status}</StatusBadge>
                  </td>
                  <td>{job.priority}</td>
                  <td>{new Date(job.queued_at).toLocaleString()}</td>
                  <td>{job.retry_count}</td>
                  <td>
                    <div className="job-actions">
                      {job.status === 'queued' && (
                        <button onClick={() => alert(`Requeue job ${job.job_id}`)}>Requeue</button>
                      )}
                      {job.status === 'running' && (
                        <button onClick={() => alert(`Cancel job ${job.job_id}`)}>Cancel</button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p>No jobs in the queue.</p>
        )}
      </GlassCard>

      {/* Runtime Rules */}
      <GlassCard title="Runtime Rules">
        <div className="runtime-rules">
          <h3>Queue Management:</h3>
          <ul>
            <li>✓ Jobs are <strong>persisted in SQLite</strong> for recovery.</li>
            <li>✓ Jobs are <strong>prioritized</strong> by priority score.</li>
            <li>✓ Jobs are <strong>retryable</strong> up to the configured limit.</li>
            <li>✓ Jobs in <StatusBadge status="info">queued</StatusBadge> or <StatusBadge status="danger">failed</StatusBadge> states can be requeued.</li>
            <li>✓ Jobs in <StatusBadge status="warning">paused</StatusBadge> or <StatusBadge status="danger">interrupted</StatusBadge> states can be resumed.</li>
          </ul>
          <h3>Concurrency:</h3>
          <ul>
            <li>✓ Max concurrency is <strong>configurable</strong>.</li>
            <li>✓ Exceeding the queue limit <strong>rejects new jobs</strong>.</li>
            <li>✓ Workers are <strong>non-blocking</strong> (async).</li>
          </ul>
        </div>
      </GlassCard>
    </div>
  );
};

// Helper function
function getStatusColor(status: string): string {
  switch (status.toLowerCase()) {
    case 'queued':
      return 'info';
    case 'running':
      return 'success';
    case 'completed':
      return 'success';
    case 'failed':
      return 'danger';
    case 'paused':
    case 'interrupted':
      return 'warning';
    case 'cancelled':
      return 'danger';
    default:
      return 'neutral';
  }
}

export default RuntimePage;
