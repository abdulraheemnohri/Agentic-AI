import React, { useState, useEffect } from 'react';
import { GlassCard, StatusBadge, HealthIndicator } from '../components';

interface Event {
  event_id: string;
  timestamp: string;
  event_type: string;
  task_id?: string;
  run_id?: string;
  [key: string]: any;
}

interface AgentRun {
  run_id: string;
  task_id: string;
  goal: string;
  status: string;
  phase: string;
  iteration: number;
  max_iterations: number;
  confidence: number;
  confidence_threshold: number;
  created_at: string;
  started_at?: string;
  updated_at: string;
  completed_at?: string;
  model?: string;
  system2_proposal?: any;
  plan?: any;
  council_decisions?: any[];
  tool_permissions?: any[];
  events?: Event[];
  result?: any;
  error?: any;
  recovery_state?: string;
}

interface Task {
  id: string;
  goal: string;
  autonomy: number;
  status: string;
  created_at: string;
  updated_at: string;
  plan_version: number;
  steps: any[];
  events: Event[];
  verification?: any;
  evaluation?: any;
  human_review?: any;
  result?: any;
}

const ObservatoryPage: React.FC = () => {
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [selectedRun, setSelectedRun] = useState<AgentRun | null>(null);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [eventSource, setEventSource] = useState<EventSource | null>(null);

  // Fetch agent runs on load
  useEffect(() => {
    const fetchRuns = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8000/api/agent/runs');
        if (!response.ok) {
          throw new Error('Failed to fetch agent runs');
        }
        const data = await response.json();
        setRuns(data.runs || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };
    fetchRuns();

    // Set up SSE for live events
    const setupSSE = () => {
      const es = new EventSource('http://127.0.0.1:8000/api/observability/events');
      es.onmessage = (e) => {
        const event = JSON.parse(e.data);
        setEvents((prev) => [event, ...prev].slice(0, 100));
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

  // Fetch run and task details when selected
  useEffect(() => {
    if (!selectedRun) return;
    const fetchRunDetails = async () => {
      try {
        const [runRes, taskRes] = await Promise.all([
          fetch(`http://127.0.0.1:8000/api/agent/${selectedRun.run_id}`),
          fetch(`http://127.0.0.1:8000/api/tasks/${selectedRun.task_id}`),
        ]);
        if (!runRes.ok || !taskRes.ok) {
          throw new Error('Failed to fetch run/task details');
        }
        const runData = await runRes.json();
        const taskData = await taskRes.json();
        setSelectedRun(runData.run);
        setSelectedTask(taskData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      }
    };
    fetchRunDetails();
  }, [selectedRun]);

  // Poll for run updates
  useEffect(() => {
    if (!selectedRun) return;
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`http://127.0.0.1:8000/api/agent/${selectedRun.run_id}`);
        if (response.ok) {
          const data = await response.json();
          setSelectedRun(data.run);
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 2000); // Poll every 2 seconds
    return () => clearInterval(interval);
  }, [selectedRun]);

  if (loading) {
    return (
      <div className="page observatory-page">
        <h1>Live Observatory</h1>
        <p>Loading agent runs...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page observatory-page">
        <h1>Live Observatory</h1>
        <StatusBadge status="error">Error: {error}</StatusBadge>
      </div>
    );
  }

  return (
    <div className="page observatory-page">
      <h1>Live Observatory</h1>
      <p>
        Real-time execution cockpit. Watch every decision as it happens.
      </p>

      <div className="observatory-layout">
        {/* Left: Run List */}
        <div className="panel run-list">
          <div className="panel-head">
            <div>
              <span className="kicker">RUN CONTROL</span>
              <h3>Execution Sessions</h3>
            </div>
            <button className="ghost" onClick={() => window.location.reload()}>Refresh</button>
          </div>
          {runs.length ? (
            runs.map((run) => (
              <button
                key={run.run_id}
                className={`run-row ${selectedRun?.run_id === run.run_id ? 'selected' : ''}`}
                onClick={() => setSelectedRun(run)}
              >
                <div className="run-main">
                  <span className={`status-dot ${getStatusColor(run.status)}`} />
                  <div>
                    <b>{run.goal}</b>
                    <small>
                      {run.run_id.slice(0, 8)} · {run.phase} · iteration {run.iteration}/{run.max_iterations}
                    </small>
                  </div>
                </div>
                <StatusBadge status={getStatusColor(run.status)}>{run.status}</StatusBadge>
              </button>
            ))
          ) : (
            <div className="empty">No agent runs yet.</div>
          )}
        </div>

        {/* Right: Live Trace */}
        <div className="panel observatory">
          <div className="panel-head">
            <div>
              <span className="kicker">LIVE TRACE</span>
              <h3>{selectedRun?.goal || selectedTask?.goal || 'Select a run'}</h3>
            </div>
            {selectedRun && (
              <div className="live-actions">
                <StatusBadge status={getStatusColor(selectedRun.status)}>{selectedRun.status}</StatusBadge>
                <button className="danger ghost" onClick={async () => {
                  try {
                    await fetch(`http://127.0.0.1:8000/api/agent/${selectedRun.run_id}/cancel`, {
                      method: 'POST',
                    });
                  } catch (err) {
                    console.error('Cancel error:', err);
                  }
                }} disabled={['completed', 'failed', 'escalated', 'cancelled'].includes(selectedRun.status)}>
                  Cancel
                </button>
              </div>
            )}
          </div>

          {selectedRun ? (
            <>
              {/* Phase Strip */}
              <div className="phase-strip">
                {['understanding', 'memory_retrieval', 'reasoning', 'planning', 'dry_run', 'system1_review', 'permission', 'executing', 'observing', 'verifying', 'evaluating', 'recovering', 'learning'].map((phase) => (
                  <div
                    key={phase}
                    className={`phase ${selectedRun.phase === phase ? 'current' : getPhaseStatus(phase, selectedRun.phase)}`}
                  >
                    <i />
                    <span>{phase.replace('_', ' ')}</span>
                  </div>
                ))}
              </div>

              {/* Trace Grid */}
              <div className="trace-grid">
                {/* System 2 Proposal */}
                <GlassCard title="System 2 Proposal">
                  {selectedRun.system2_proposal ? (
                    <>
                      <div className="decision-action">{selectedRun.system2_proposal.action}</div>
                      <p>{selectedRun.system2_proposal.reason}</p>
                      <div className="meter">
                        <span style={{ width: `${Math.round((selectedRun.system2_proposal.confidence || 0) * 100)}%` }} />
                      </div>
                      <small>
                        Confidence {Math.round((selectedRun.system2_proposal.confidence || 0) * 100)}% · model {selectedRun.model || 'N/A'}
                      </small>
                    </>
                  ) : (
                    <div className="empty">Waiting for reasoning.</div>
                  )}
                </GlassCard>

                {/* Council Gate */}
                <GlassCard title="Council Gate">
                  {selectedRun.council_decisions?.length ? (
                    <>
                      <StatusBadge status={getDecisionColor(selectedRun.council_decisions[0].decision)}>
                        {selectedRun.council_decisions[0].decision || 'pending'}
                      </StatusBadge>
                      <div className="vote-list">
                        {Object.entries(selectedRun.council_decisions[0].votes || {}).map(([key, value]) => (
                          <div key={key} className="vote">
                            <span>{key}</span>
                            <strong>{value}</strong>
                          </div>
                        ))}
                      </div>
                      <small>
                        {selectedRun.council_decisions[0].disagreement ? 'Disagreement detected — fail-closed policy applies.' : 'No disagreement recorded.'}
                      </small>
                    </>
                  ) : (
                    <div className="empty">Waiting for Council decision.</div>
                  )}
                </GlassCard>

                {/* Permission Gate */}
                <GlassCard title="Permission Gate">
                  {selectedRun.council_decisions?.length && selectedRun.council_decisions[0].allowed ? (
                    <>
                      <StatusBadge status="success">AUTHORIZED</StatusBadge>
                      <p>System 1 authorized the guarded execution boundary.</p>
                      {selectedTask?.steps?.map((step: any) => (
                        <div key={step.id} className="mini-row">
                          <span>{step.tool}</span>
                          <StatusBadge status={step.status === 'completed' ? 'success' : step.status === 'failed' ? 'danger' : 'info'}>
                            {step.status}
                          </StatusBadge>
                        </div>
                      ))}
                    </>
                  ) : (
                    <>
                      <StatusBadge status="warning">HELD</StatusBadge>
                      <p>Execution remains blocked until the System 1 gate allows it.</p>
                    </>
                  )}
                </GlassCard>

                {/* Verification */}
                <GlassCard title="Verification">
                  {selectedTask?.verification ? (
                    <>
                      <StatusBadge status={selectedTask.verification.passed ? 'success' : 'danger'}>
                        {selectedTask.verification.passed ? 'PASSED' : 'FAILED'}
                      </StatusBadge>
                      <pre>{JSON.stringify(selectedTask.verification, null, 2)}</pre>
                    </>
                  ) : (
                    <div className="empty">Waiting for verification.</div>
                  )}
                </GlassCard>

                {/* Evaluation */}
                <GlassCard title="Evaluation">
                  {selectedTask?.evaluation ? (
                    <>
                      <StatusBadge status={getEvaluationColor(selectedTask.evaluation.overall_status)}>
                        {selectedTask.evaluation.overall_status || 'pending'}
                      </StatusBadge>
                      <div className="score">
                        {Math.round((selectedTask.evaluation.overall_score || 0) * 100)}
                        <small>/100</small>
                      </div>
                      <p>{selectedTask.evaluation.summary || 'Evaluation will appear after verification.'}</p>
                    </>
                  ) : (
                    <div className="empty">Waiting for evaluation.</div>
                  )}
                </GlassCard>

                {/* Event Stream */}
                <GlassCard title="Event Stream" className="wide">
                  <div className="event-stream">
                    {events.length ? (
                      events.map((event) => (
                        <div key={event.event_id} className="event">
                          <span className="event-seq">#{event.event_id.slice(0, 8)}</span>
                          <span className="event-name">{event.event_type}</span>
                          {event.task_id && <span className="event-task-id">Task: {event.task_id.slice(0, 8)}</span>}
                          {event.run_id && <span className="event-run-id">Run: {event.run_id.slice(0, 8)}</span>}
                          <small>{new Date(event.timestamp).toLocaleTimeString()}</small>
                        </div>
                      ))
                    ) : (
                      <div className="empty">No events yet.</div>
                    )}
                  </div>
                </GlassCard>
              </div>
            </>
          ) : (
            <div className="empty big">Select an agent run to open the live execution observatory.</div>
          )}
        </div>
      </div>
    </div>
  );
};

// Helper functions
function getStatusColor(status: string): string {
  switch (status.toLowerCase()) {
    case 'completed':
    case 'passed':
    case 'allow':
    case 'ok':
    case 'running':
      return 'good';
    case 'failed':
    case 'deny':
    case 'error':
    case 'blocked':
      return 'bad';
    case 'escalated':
    case 'escalate':
    case 'cancelled':
    case 'cancel_requested':
      return 'warn';
    default:
      return 'neutral';
  }
}

function getDecisionColor(decision: string): string {
  switch (decision.toLowerCase()) {
    case 'allow':
      return 'success';
    case 'deny':
      return 'danger';
    case 'escalate':
      return 'warning';
    default:
      return 'info';
  }
}

function getEvaluationColor(status: string): string {
  switch (status.toLowerCase()) {
    case 'passed':
      return 'success';
    case 'failed':
      return 'danger';
    default:
      return 'info';
  }
}

function getPhaseStatus(phase: string, currentPhase: string): string {
  const phases = ['understanding', 'memory_retrieval', 'reasoning', 'planning', 'dry_run', 'system1_review', 'permission', 'executing', 'observing', 'verifying', 'evaluating', 'recovering', 'learning'];
  const currentIndex = phases.indexOf(currentPhase);
  const phaseIndex = phases.indexOf(phase);
  if (phaseIndex < currentIndex) return 'done';
  if (phaseIndex === currentIndex) return 'current';
  return '';
}

export default ObservatoryPage;
