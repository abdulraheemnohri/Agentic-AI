import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './style.css';
import { GlassCard, StatusBadge, HealthIndicator } from './components';
import System1Page from './pages/System1';
import System2Page from './pages/System2';
import CouncilPage from './pages/Council';

const API = 'http://localhost:8000/api';

type Any = Record<string, any>;

type LiveData = {
  run: Any | null;
  trace: Any | null;
  task: Any | null;
};

const json = async (url: string, opt?: RequestInit) => {
  const response = await fetch(url, opt);
  if (!response.ok) throw new Error(await response.text());
  return response.json();
};

const tone = (value: string) => {
  const v = String(value || '').toLowerCase();
  if (['completed', 'passed', 'allow', 'ok', 'running'].includes(v)) return 'good';
  if (['failed', 'deny', 'error', 'blocked'].includes(v)) return 'bad';
  if (['escalated', 'escalate', 'cancelled', 'cancel_requested'].includes(v)) return 'warn';
  return 'neutral';
};

const pct = (value: number | undefined) => `${Math.round(Math.max(0, Math.min(1, Number(value || 0))) * 100)}%`;

function StatusDot({ value }: { value: string }) {
  return <span className={`status-dot ${tone(value)}`} />;
}

function Stat({ label, value, detail }: { label: string; value: React.ReactNode; detail?: string }) {
  return <div className="stat card">
    <span className="label">{label}</span>
    <strong>{value}</strong>
    {detail && <small>{detail}</small>}
  </div>;
}

function App() {
  const [goal, setGoal] = useState('');
  const [tasks, setTasks] = useState<Any[]>([]);
  const [runs, setRuns] = useState<Any[]>([]);
  const [brain, setBrain] = useState<Any | null>(null);
  const [policy, setPolicy] = useState<Any>({ mode: 'consensus', minimum_confidence: .5, minimum_reviews: 1, fail_closed_on_disagreement: true });
  const [discover, setDiscover] = useState<Any[]>([]);
  const [tab, setTab] = useState('Dashboard');
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [model, setModel] = useState('');
  const [localUrl, setLocalUrl] = useState('http://127.0.0.1:1234');
  const [localName, setLocalName] = useState('local-model');
  const [selectedRunId, setSelectedRunId] = useState('');
  const [live, setLive] = useState<LiveData>({ run: null, trace: null, task: null });
  const pollRef = useRef<number | null>(null);

  const load = useCallback(async () => {
    try {
      const [status, taskList, runList] = await Promise.all([
        json(`${API}/brain/status`),
        json(`${API}/tasks`),
        json(`${API}/agent/runs`),
      ]);
      setBrain(status);
      setTasks(taskList);
      setRuns(runList.runs || []);
      setPolicy(status.system1_policy || policy);
      setModel(status.runtime?.active_system2 || '');
    } catch {
      setMessage('Backend offline — start FastAPI on port 8000.');
    }
  }, []);

  const refreshLive = useCallback(async (runId: string) => {
    if (!runId) return;
    try {
      const [runData, trace] = await Promise.all([
        json(`${API}/agent/${runId}`),
        json(`${API}/agent/${runId}/trace`),
      ]);
      setLive({ run: runData.run, task: runData.task, trace });
      setRuns(current => {
        const next = current.filter(x => x.run_id !== runId);
        return [runData.run, ...next];
      });
      return runData.run;
    } catch (error: any) {
      setMessage(error.message || 'Unable to read live run.');
      return null;
    }
  }, []);

  const stopPolling = useCallback(() => {
    if (pollRef.current !== null) window.clearInterval(pollRef.current);
    pollRef.current = null;
  }, []);

  const watchRun = useCallback((runId: string) => {
    stopPolling();
    setSelectedRunId(runId);
    refreshLive(runId);
    pollRef.current = window.setInterval(async () => {
      const current = await refreshLive(runId);
      if (current && ['completed', 'failed', 'escalated', 'cancelled'].includes(current.status)) stopPolling();
    }, 900);
  }, [refreshLive, stopPolling]);

  useEffect(() => {
    load();
    return stopPolling;
  }, [load, stopPolling]);

  const runAgent = async () => {
    if (!goal.trim()) return;
    setBusy(true);
    setMessage('Starting guarded agent run…');
    try {
      const result = await json(`${API}/agent/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ goal, autonomy: 1, max_iterations: 5, max_retries: 2, confidence_threshold: .7 }),
      });
      setGoal('');
      setLive({ run: result.run, task: result.task, trace: { stream: result.run.stream || [], events: [] } });
      setSelectedRunId(result.run.run_id);
      setMessage(result.run.status === 'completed' ? 'Agent completed and verified.' : `Agent finished: ${result.run.status}`);
      await load();
      setTab('Agent');
    } catch (error: any) {
      setMessage(error.message || 'Agent run failed.');
    } finally {
      setBusy(false);
    }
  };

  const cancelRun = async () => {
    if (!selectedRunId) return;
    try {
      await json(`${API}/agent/${selectedRunId}/cancel`, { method: 'POST' });
      await refreshLive(selectedRunId);
      setMessage('Cancellation requested.');
    } catch (error: any) { setMessage(error.message); }
  };

  const discoverModels = async () => {
    try {
      const result = await json(`${API}/brain/system2/discover`);
      setDiscover(result.servers || []);
      setMessage('Local model discovery completed.');
    } catch (error: any) { setMessage(error.message); }
  };

  const register = async () => {
    try {
      await json(`${API}/brain/system2/local`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_id: localName, base_url: localUrl, model_name: localName, provider: 'local-openai-compatible' }),
      });
      setMessage('Local System 2 model registered.');
      await load();
    } catch (error: any) { setMessage(error.message); }
  };

  const activate = async (id: string) => {
    try {
      await json(`${API}/brain/models/active`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ model_id: id }) });
      setModel(id); setMessage(`Active System 2: ${id}`); await load();
    } catch (error: any) { setMessage(error.message); }
  };

  const savePolicy = async () => {
    try {
      const result = await json(`${API}/brain/system1/policy`, {
        method: 'PUT', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(policy),
      });
      setPolicy(result); setMessage('System 1 Council policy saved.');
    } catch (error: any) { setMessage(error.message); }
  };

  const selected = live.run;
  const stream = live.trace?.stream || selected?.stream || [];
  const reviews = selected?.system1_reviews?.flatMap((x: Any) => x.reviews || []) || [];
  const latestCouncil = selected?.council_decisions?.at(-1);
  const providerStats = brain?.runtime?.system1_provider_stats || {};
  const phases = useMemo(() => ['understanding', 'memory_retrieval', 'reasoning', 'planning', 'dry_run', 'system1_review', 'permission', 'executing', 'observing', 'verifying', 'evaluating', 'recovering', 'learning'], []);

  // Navigation with new pages
  const nav = ['Dashboard', 'Agent', 'System 1', 'System 2', 'Council', 'Tasks', 'Memory', 'Evaluations', 'Tools', 'Logs', 'Settings'];

  // Render the appropriate page based on the tab
  const renderPage = () => {
    switch (tab) {
      case 'System 1':
        return <System1Page />;
      case 'System 2':
        return <System2Page />;
      case 'Council':
        return <CouncilPage />;
      case 'Dashboard':
        return (
          <>
            <section className="hero">
              <div className="hero-copy"><span className="kicker">EXECUTION OBSERVATORY</span><h2>Run work. Watch every decision.</h2><p>Local System 2 proposes. System 1 reviews and authorizes. Permissions, tools, verification, evaluation and recovery remain visible in one audit surface.</p></div>
              <div className="composer"><textarea value={goal} onChange={e => setGoal(e.target.value)} placeholder="Describe a goal for the agent…"/><button onClick={runAgent} disabled={busy}>{busy ? 'Running…' : 'Run Agent →'}</button></div>
            </section>
            <section className="stats-grid">
              <Stat label="AGENT RUNS" value={runs.length} detail="Persisted execution history"/>
              <Stat label="COMPLETED" value={runs.filter(x => x.status === 'completed').length} detail="Verified successful runs"/>
              <Stat label="SYSTEM 1" value={`${brain?.system1?.filter((x: Any) => x.configured).length || 0} ready`} detail="Council providers"/>
              <Stat label="SYSTEM 2" value={brain?.system2?.length || 0} detail="Loopback/local models"/>
            </section>
            <section className="panel boundary"><div className="panel-head"><div><span className="kicker">CONTROL BOUNDARY</span><h3>Runtime architecture</h3></div></div><div className="boundary-grid"><div className="boundary-node"><span className="node-icon s2">S2</span><div><b>{model || 'local-deterministic-v2.2'}</b><small>Local reasoning / proposal only</small></div><span className="tag good">LOCAL</span></div><div className="arrow">→</div><div className="boundary-node"><span className="node-icon s1">S1</span><div><b>System 1 Council</b><small>Review + permission + risk gate</small></div><span className="tag good">AUTHORITY</span></div><div className="arrow">→</div><div className="boundary-node"><span className="node-icon ex">EX</span><div><b>Executor</b><small>Tools + observer + verifier</small></div><span className="tag">GUARDED</span></div></div></section>
          </>
        );
      case 'Agent':
        return (
          <section className="observatory-layout">
            <div className="panel run-list"><div className="panel-head"><div><span className="kicker">RUN CONTROL</span><h3>Execution sessions</h3></div><button className="ghost" onClick={load}>Refresh</button></div>{runs.length ? runs.map(run => <button className={`run-row ${selectedRunId === run.run_id ? 'selected' : ''}`} key={run.run_id} onClick={() => watchRun(run.run_id)}><div className="run-main"><StatusDot value={run.status}/><div><b>{run.goal}</b><small>{run.run_id.slice(0, 8)} · {run.phase} · iteration {run.iteration}/{run.max_iterations}</small></div></div><span className={`tag ${tone(run.status)}`}>{run.status}</span></button>) : <div className="empty">No agent runs yet.</div>}</div>
            <div className="panel observatory"><div className="panel-head"><div><span className="kicker">LIVE TRACE</span><h3>{selected?.goal || 'Select a run'}</h3></div>{selected && <div className="live-actions"><span className={`tag ${tone(selected.status)}`}>{selected.status}</span><button className="danger ghost" onClick={cancelRun} disabled={['completed','failed','escalated','cancelled'].includes(selected.status)}>Cancel</button></div>}</div>
              {selected ? <>
                <div className="phase-strip">{phases.map(phase => <div className={`phase ${selected.phase === phase ? 'current' : phases.indexOf(phase) < phases.indexOf(selected.phase) ? 'done' : ''}`} key={phase}><i/><span>{phase.replace('_', ' ')}</span></div>)}</div>
                <div className="trace-grid">
                  <section className="trace-card wide"><div className="trace-title"><b>System 2 proposal</b><span className="tag good">LOCAL ONLY</span></div>{selected.decisions?.at(-1) ? <><div className="decision-action">{selected.decisions.at(-1).action}</div><p>{selected.decisions.at(-1).reason}</p><div className="meter"><span style={{ width: pct(selected.decisions.at(-1).confidence) }}/></div><small>Confidence {pct(selected.decisions.at(-1).confidence)} · model {selected.decisions.at(-1).model_id}</small></> : <div className="empty">Waiting for reasoning.</div>}</section>
                  <section className="trace-card"><div className="trace-title"><b>Council gate</b><span className={`tag ${tone(latestCouncil?.decision)}`}>{latestCouncil?.decision || 'pending'}</span></div><div className="vote-list">{Object.entries(latestCouncil?.votes || {}).map(([key, value]: any) => <div className="vote" key={key}><span>{key}</span><strong>{value}</strong></div>)}</div><small>{latestCouncil?.disagreement ? 'Disagreement detected — fail-closed policy applies.' : 'No disagreement recorded.'}</small></section>
                  <section className="trace-card"><div className="trace-title"><b>Permission gate</b><span className={`tag ${selected.council_decisions?.length && latestCouncil?.allowed ? 'good' : 'warn'}`}>{latestCouncil?.allowed ? 'AUTHORIZED' : 'HELD'}</span></div><p>{latestCouncil?.allowed ? 'System 1 authorized the guarded execution boundary.' : 'Execution remains blocked until the System 1 gate allows it.'}</p>{live.task?.steps?.map((step: Any) => <div className="mini-row" key={step.id}><span>{step.tool}</span><span className={`tag ${tone(step.status)}`}>{step.status}</span></div>)}</section>
                  <section className="trace-card"><div className="trace-title"><b>Verification</b><span className={`tag ${tone(live.task?.verification?.passed ? 'passed' : 'pending')}`}>{live.task?.verification?.passed ? 'PASSED' : 'PENDING'}</span></div><pre>{JSON.stringify(live.task?.verification || {}, null, 2)}</pre></section>
                  <section className="trace-card"><div className="trace-title"><b>Evaluation</b><span className={`tag ${tone(live.task?.evaluation?.overall_status)}`}>{live.task?.evaluation?.overall_status || 'pending'}</span></div><div className="score">{live.task?.evaluation ? Math.round((live.task.evaluation.overall_score || 0) * 100) : 0}<small>/100</small></div><p>{live.task?.evaluation?.summary || 'Evaluation will appear after verification.'}</p></section>
                  <section className="trace-card wide"><div className="trace-title"><b>Event stream</b><span>{stream.length} events</span></div><div className="event-stream">{stream.slice(-80).reverse().map((event: Any) => <div className="event" key={`${event.sequence}-${event.at}`}><span className="event-seq">#{event.sequence}</span><span className="event-name">{event.event}</span><small>{event.at}</small><code>{JSON.stringify(event).slice(0, 360)}</code></div>)}</div></section>
                </div>
              </> : <div className="empty big">Select an agent run to open the live execution observatory.</div>}
            </div>
          </section>
        );
      case 'Tasks':
        return (
          <section className="panel"><div className="panel-head"><div><span className="kicker">HISTORY</span><h3>Task audit</h3></div><button className="ghost" onClick={load}>Refresh</button></div>{tasks.length ? tasks.slice(0, 50).map(task => <div className="audit-row" key={task.id}><div><StatusDot value={task.status}/><b>{task.goal}</b><small>{new Date(task.updated_at).toLocaleString()} · plan v{task.plan_version}</small></div><span className={`tag ${tone(task.status)}`}>{task.status}</span></div>) : <div className="empty">No tasks yet.</div>}</section>
        );
      case 'Memory':
      case 'Evaluations':
      case 'Tools':
      case 'Logs':
      case 'Settings':
        return (
          <section className="panel placeholder"><span className="kicker">CONTROL SURFACE</span><h3>{tab}</h3><p>Backend controls for this surface remain available. V2.8 keeps the execution observatory as the primary live audit view while preserving the existing API contracts.</p><div className="api-list"><code>GET /api/agent/{'{run_id}'}</code><code>GET /api/agent/{'{run_id}'}/trace</code><code>GET /api/brain/system1/providers</code><code>GET /api/brain/system2/discover</code></div></section>
        );
      default:
        return <div className="empty big">Page not found.</div>;
    }
  };

  return <div className="app">
    <aside>
      <div className="brand"><span className="brand-mark">◈</span> Agentic<span>-AI</span></div>
      <div className="kernel-chip"><StatusDot value="ok"/><div><b>SYSTEM 1</b><small>Authoritative kernel</small></div></div>
      <nav>{nav.map(item => <button className={tab === item ? 'nav active' : 'nav'} onClick={() => setTab(item)} key={item}>{item}</button>)}</nav>
      <div className="sidebar-foot"><span className="pulse"/> Local-first security boundary<br/><small>System 2 remote fallback: prohibited</small></div>
    </aside>

    <main>
      <header>
        <div><p className="eyebrow">GUARDED AGENT KERNEL • V3.2 OBSERVATORY</p><h1>{tab}</h1></div>
        <div className="header-actions"><span className="pill">{brain?.runtime?.system2_network_policy || 'LOOPBACK ONLY'}</span><button className="icon-button" onClick={load}>↻</button></div>
      </header>

      {message && <div className="notice"><span>●</span>{message}<button onClick={() => setMessage('')}>×</button></div>}

      {renderPage()}
    </main>
  </div>;
}

createRoot(document.getElementById('root')!).render(<App />);
