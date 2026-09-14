import React, { useState, useEffect } from 'react';
import { GlassCard, StatusBadge, HealthIndicator } from '../components';

interface RecoverableJob {
  job_id: string;
  run_id: string;
  task_id: string;
  status: string;
  priority: number;
  queued_at: string;
  started_at?: string;
  completed_at?: string;
  worker?: string;
  retry_count: number;
  error?: string;
}

interface RecoveryStatus {
  status: string;
  recoverable_jobs: number;
  interrupted_jobs: number;
  recoverable_job_ids: string[];
  interrupted_job_ids: string[];
}

const RecoveryPage: React.FC = () => {
  const [recoveryStatus, setRecoveryStatus] = useState<RecoveryStatus | null>(null);
  const [jobs, setJobs] = useState<RecoverableJob[]>([]);
  const [selectedJob, setSelectedJob] = useState<RecoverableJob | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch recovery status and jobs
  useEffect(() => {
    const fetchRecoveryData = async () => {
      try {
        const [statusRes, jobsRes] = await Promise.all([
          fetch('http://127.0.0.1:8000/api/recovery/status'),
          fetch('http://127.0.0.1:8000/api/recovery/jobs'),
        ]);
        if (!statusRes.ok || !jobsRes.ok) {
          throw new Error('Failed to fetch recovery data');
        }
        const statusData = await statusRes.json();
        const jobsData = await jobsRes.json();
        setRecoveryStatus(statusData);
        setJobs(jobsData.jobs || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };
    fetchRecoveryData();
  }, []);

  // Requeue a job
  const requeueJob = async (runId: string) => {
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/recovery/requeue/${runId}`, {
        method: 'POST',
      });
      if (!response.ok) {
        throw new Error('Failed to requeue job');
      }
      const result = await response.json();
      setError(null);
      // Refresh jobs
      const jobsRes = await fetch('http://127.0.0.1:8000/api/recovery/jobs');
      if (jobsRes.ok) {
        const jobsData = await jobsRes.json();
        setJobs(jobsData.jobs || []);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  // Resume a job
  const resumeJob = async (runId: string) => {
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/recovery/resume/${runId}`, {
        method: 'POST',
      });
      if (!response.ok) {
        throw new Error('Failed to resume job');
      }
      const result = await response.json();
      setError(null);
      // Refresh jobs
      const jobsRes = await fetch('http://127.0.0.1:8000/api/recovery/jobs');
      if (jobsRes.ok) {
        const jobsData = await jobsRes.json();
        setJobs(jobsData.jobs || []);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  // Cancel a job
  const cancelJob = async (runId: string) => {
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/recovery/cancel/${runId}`, {
        method: 'POST',
      });
      if (!response.ok) {
        throw new Error('Failed to cancel job');
      }
      const result = await response.json();
      setError(null);
      // Refresh jobs
      const jobsRes = await fetch('http://127.0.0.1:8000/api/recovery/jobs');
      if (jobsRes.ok) {
        const jobsData = await jobsRes.json();
        setJobs(jobsData.jobs || []);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  if (loading) {
    return (
      <div className="page recovery-page">
        <h1>Recovery Console</h1>
        <p>Loading recovery data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page recovery-page">
        <h1>Recovery Console</h1>
        <StatusBadge status="error">Error: {error}</StatusBadge>
      </div>
    );
  }

  return (
    <div className="page recovery-page">
      <h1>Recovery Console</h1>
      <p>
        Manage recoverable jobs, interrupted executions, and system recovery.
      </p>

      {/* Recovery Status */}
      <GlassCard title="Recovery Status">
        <div className="recovery-status">
          <div>
            <strong>Status:</strong> <StatusBadge status={recoveryStatus?.status === 'healthy' ? 'success' : 'danger'}>{recoveryStatus?.status}</StatusBadge>
          </div>
          <div>
            <strong>Recoverable Jobs:</strong> {recoveryStatus?.recoverable_jobs || 0}
          </div>
          <div>
            <strong>Interrupted Jobs:</strong> {recoveryStatus?.interrupted_jobs || 0}
          </div>
        </div>
      </GlassCard>

      {/* Recoverable Jobs Table */}
      <GlassCard title="Recoverable Jobs">
        {jobs.length ? (
          <table className="jobs-table">
            <thead>
              <tr>
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
              {jobs.map((job) => (
                <tr key={job.job_id} onClick={() => setSelectedJob(job)}>
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
                        <button onClick={(e) => { e.stopPropagation(); requeueJob(job.run_id); }}>Requeue</button>
                      )}
                      {job.status === 'paused' && (
                        <button onClick={(e) => { e.stopPropagation(); resumeJob(job.run_id); }}>Resume</button>
                      )}
                      {['queued', 'paused'].includes(job.status) && (
                        <button onClick={(e) => { e.stopPropagation(); cancelJob(job.run_id); }}>Cancel</button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p>No recoverable jobs.</p>
        )}
      </GlassCard>

      {/* Job Details */}
      {selectedJob && (
        <GlassCard title="Job Details">
          <div className="job-details">
            <div>
              <strong>Job ID:</strong> {selectedJob.job_id}
            </div>
            <div>
              <strong>Run ID:</strong> {selectedJob.run_id}
            </div>
            <div>
              <strong>Task ID:</strong> {selectedJob.task_id}
            </div>
            <div>
              <strong>Status:</strong> <StatusBadge status={getStatusColor(selectedJob.status)}>{selectedJob.status}</StatusBadge>
            </div>
            <div>
              <strong>Priority:</strong> {selectedJob.priority}
            </div>
            <div>
              <strong>Queued At:</strong> {new Date(selectedJob.queued_at).toLocaleString()}
            </div>
            {selectedJob.started_at && (
              <div>
                <strong>Started At:</strong> {new Date(selectedJob.started_at).toLocaleString()}
              </div>
            )}
            {selectedJob.completed_at && (
              <div>
                <strong>Completed At:</strong> {new Date(selectedJob.completed_at).toLocaleString()}
              </div>
            )}
            <div>
              <strong>Retry Count:</strong> {selectedJob.retry_count}
            </div>
            {selectedJob.error && (
              <div>
                <strong>Error:</strong> {selectedJob.error}
              </div>
            )}
            {selectedJob.worker && (
              <div>
                <strong>Worker:</strong> {selectedJob.worker}
              </div>
            )}
          </div>
          <div className="job-actions">
            {selectedJob.status === 'queued' && (
              <button onClick={() => requeueJob(selectedJob.run_id)}>Requeue Job</button>
            )}
            {selectedJob.status === 'paused' && (
              <button onClick={() => resumeJob(selectedJob.run_id)}>Resume Job</button>
            )}
            {['queued', 'paused'].includes(selectedJob.status) && (
              <button onClick={() => cancelJob(selectedJob.run_id)}>Cancel Job</button>
            )}
          </div>
        </GlassCard>
      )}

      {/* Recovery Rules */}
      <GlassCard title="Recovery Rules">
        <div className="recovery-rules">
          <h3>Recovery System Rules:</h3>
          <ul>
            <li>✓ Only jobs in <strong>safe states</strong> can be recovered.</li>
            <li>✓ Requeue: For <StatusBadge status="info">queued</StatusBadge> or <StatusBadge status="danger">failed</StatusBadge> jobs.</li>
            <li>✓ Resume: For <StatusBadge status="warning">paused</StatusBadge> or <StatusBadge status="danger">interrupted</StatusBadge> jobs.</li>
            <li>✓ Cancel: For <StatusBadge status="info">queued</StatusBadge> or <StatusBadge status="warning">paused</StatusBadge> jobs.</li>
            <li>✓ All recovery actions are <strong>audited</strong>.</li>
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

export default RecoveryPage;
