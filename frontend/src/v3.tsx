import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './v3.css';

type Any = Record<string, any>;
const API = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api').replace(/\/$/, '');
const terminal = new Set(['completed','failed','escalated','cancelled']);

async function api(path:string, options:RequestInit={}) {
  const r = await fetch(`${API}${path}`, { ...options, headers:{'Content-Type':'application/json', ...(options.headers||{})} });
  const text = await r.text(); let data:Any = {}; try { data = text ? JSON.parse(text) : {}; } catch { data = {raw:text}; }
  if (!r.ok) throw new Error(data.detail || data.message || data.raw || `HTTP ${r.status}`);
  return data;
}
const post=(p:string,b:Any={})=>api(p,{method:'POST',body:JSON.stringify(b)});
const put=(p:string,b:Any)=>api(p,{method:'PUT',body:JSON.stringify(b)});

function Card({title,children,wide=false}:any){return <section className={`card ${wide?'wide':''}`}><div className="cardTitle">{title}</div>{children}</section>}
function Pill({children,tone='info'}:any){return <span className={`pill ${tone}`}>{children}</span>}
function Json({value}:any){return <pre className="json">{JSON.stringify(value,null,2)}</pre>}

function App(){
 const [tab,setTab]=useState('Dashboard'); const [goal,setGoal]=useState('Return the current time and verify the output.');
 const [run,setRun]=useState<Any|null>(null); const [trace,setTrace]=useState<Any[]>([]); const [backends,setBackends]=useState<Any|null>(null);
 const [runtime,setRuntime]=useState<Any|null>(null); const [runs,setRuns]=useState<Any[]>([]); const [tasks,setTasks]=useState<Any[]>([]);
 const [models,setModels]=useState<Any|null>(null); const [memory,setMemory]=useState<Any[]>([]); const [tools,setTools]=useState<Any|null>(null);
 const [error,setError]=useState(''); const [busy,setBusy]=useState(false); const [config,setConfig]=useState({max_concurrency:2,queue_limit:20,poll_interval_ms:500});
 const nav=['Dashboard','Agent','System 1','System 2','Tasks','Memory','Evaluations','Tools','Logs','Settings'];
 const refresh=async()=>{try{setError(''); const [b,r,rs,ts,m,t,mm]=await Promise.all([api('/backends/status'),api('/runtime/status'),api('/agent/runs'),api('/tasks'),api('/memory?limit=20'),api('/tools'),api('/brain/models')]); setBackends(b);setRuntime(r);setRuns(rs.runs||[]);setTasks(ts);setMemory(m.memories||[]);setTools(t);setModels(mm);}catch(e:any){setError(e.message)}};
 useEffect(()=>{refresh(); const id=setInterval(refresh,2500); return()=>clearInterval(id)},[]);
 useEffect(()=>{if(!run?.run_id)return; let stop=false; const tick=async()=>{try{const [s,t]=await Promise.all([api(`/agent/${run.run_id}/async-status`),api(`/agent/${run.run_id}/trace`)]);if(!stop){setRun(s.run);setTrace(t.events||t.stream||[]);if(terminal.has(s.status)) return;}}catch(e:any){if(!stop)setError(e.message)}}; tick(); const id=setInterval(tick,700); return()=>{stop=true;clearInterval(id)}},[run?.run_id]);
 const launch=async()=>{try{setBusy(true);setError('');const x=await post('/agent/run',{goal,autonomy:1,max_iterations:5,max_retries:2,confidence_threshold:.7});setRun(x.run);setTrace([]);setTab('Agent');await refresh()}catch(e:any){setError(e.message)}finally{setBusy(false)}};
 const cancel=async()=>{if(!run)return;try{await post(`/agent/${run.run_id}/cancel`);await refresh()}catch(e:any){setError(e.message)}};
 const backend=async(action:string,body:Any={})=>{try{await post(`/backends/system2/${action}`,body);await refresh()}catch(e:any){setError(e.message)}};
 const saveConfig=async()=>{try{await put('/runtime/config',config);await refresh()}catch(e:any){setError(e.message)}};
 const active=useMemo(()=>runs.filter(r=>!terminal.has(r.status)).length,[runs]);
 return <div className="shell">
  <aside><div className="logo"><span>◈</span> AGENTIC<span className="accent">AI</span></div><div className="sub">V3.0 CONTROL PLANE</div><nav>{nav.map(n=><button key={n} className={tab===n?'selected':''} onClick={()=>setTab(n)}>{n}</button>)}</nav><div className="sideFoot"><Pill tone={backends?.system1?.running?'ok':'bad'}>S1 {backends?.system1?.running?'ONLINE':'OFFLINE'}</Pill><Pill tone={runtime?'ok':'bad'}>RUNTIME {runtime?'ONLINE':'OFFLINE'}</Pill></div></aside>
  <main><header><div><h1>{tab}</h1><p>Local-first agent runtime · System 1 authoritative · System 2 local-only</p></div><div className="headerActions"><button onClick={refresh}>↻</button><Pill tone={error?'bad':'ok'}>{error?'ERROR':'CONNECTED'}</Pill></div></header>{error&&<div className="error">{error}</div>}
  {tab==='Dashboard'&&<div className="grid"><Card title="Runtime"><div className="stats"><div><b>{runtime?.active_jobs??0}</b><small>ACTIVE</small></div><div><b>{runtime?.queued_jobs??0}</b><small>QUEUED</small></div><div><b>{active}</b><small>LIVE RUNS</small></div><div><b>{runtime?.completed??0}</b><small>COMPLETED</small></div></div><Json value={runtime}/></Card><Card title="Backend authority"><Json value={backends}/></Card><Card title="Quick launch" wide><textarea value={goal} onChange={e=>setGoal(e.target.value)}/><div className="actions"><button className="primary" disabled={busy} onClick={launch}>{busy?'Starting…':'▶ Start Agent'}</button>{run&&<button className="danger" onClick={cancel}>■ Cancel current</button>}</div></Card><Card title="Recent runs" wide><Table rows={runs.slice(0,8)} cols={['run_id','status','phase','goal']}/></Card></div>}
  {tab==='Agent'&&<div className="grid"><Card title="Agent composer"><textarea value={goal} onChange={e=>setGoal(e.target.value)}/><div className="actions"><button className="primary" onClick={launch}>▶ Start asynchronous run</button>{run&&<button className="danger" onClick={cancel}>Cancel</button>}</div></Card><Card title="Live state"><div className="heroStatus"><Pill tone={run&&terminal.has(run.status)?'info':'ok'}>{run?.status||'IDLE'}</Pill><strong>{run?.phase||'—'}</strong></div><Json value={run||{message:'Select or launch a run'}}/></Card><Card title="System 2 reasoning / proposal" wide><Json value={run?.system2_proposal||run?.proposal||{message:'Proposal appears here during execution'}}/></Card><Card title="Live event stream" wide><div className="events">{trace.length?trace.slice(-80).reverse().map((e,i)=><div key={i}><span>{e.at||e.timestamp||''}</span>{e.type||e.event||'event'} <em>{JSON.stringify(e).slice(0,240)}</em></div>):'Waiting for events…'}</div></Card></div>}
  {tab==='System 1'&&<div className="grid"><Card title="Authoritative control plane"><div className="authority"><span className="orb"/><div><h2>ALWAYS ON</h2><p>System 1 cannot be stopped by the frontend or System 2.</p></div></div><Json value={backends?.system1||{}}/></Card><Card title="Provider health"><Json value={models?.system1||models?.system1_providers||{}}/></Card><Card title="Council security"><p>Execution requires System 1 Council authorization <b>AND</b> tool permission checks.</p><p>System 2 may propose/reason, but never authorize, execute, or modify System 1.</p></Card></div>}
  {tab==='System 2'&&<div className="grid"><Card title="Local reasoning backend"><Json value={backends?.system2||{}}/><div className="actions"><button onClick={()=>backend('start')}>Start</button><button onClick={()=>backend('stop')}>Stop</button><button onClick={()=>backend('restart')}>Restart</button><button onClick={()=>backend('update')}>Update</button></div></Card><Card title="Model registry"><Json value={models?.system2||models||{}}/></Card><Card title="Security boundary" wide><Pill tone="ok">LOOPBACK ONLY</Pill><p>Remote System 2 URLs are denied. System 2 has no authority. All execution remains behind System 1.</p></Card></div>}
  {tab==='Tasks'&&<Card title={`Tasks · ${tasks.length}`} wide><Table rows={tasks} cols={['id','status','goal','updated_at']}/></Card>}
  {tab==='Memory'&&<Card title="Persistent memory" wide><Table rows={memory} cols={['memory_id','kind','importance','content','created_at']}/></Card>}
  {tab==='Evaluations'&&<Card title="Evaluation history" wide><Table rows={runs.map(r=>({run_id:r.run_id,status:r.status,phase:r.phase,evaluation:r.evaluation}))} cols={['run_id','status','phase','evaluation']}/></Card>}
  {tab==='Tools'&&<Card title="Tool registry" wide><Json value={tools||{}}/></Card>}
  {tab==='Logs'&&<Card title="Runtime logs" wide><div className="events">{trace.map((e,i)=><div key={i}>{JSON.stringify(e)}</div>)}</div></Card>}
  {tab==='Settings'&&<div className="grid"><Card title="Execution runtime"><label>Maximum concurrency<input type="number" min="1" max="16" value={config.max_concurrency} onChange={e=>setConfig({...config,max_concurrency:+e.target.value})}/></label><label>Queue limit<input type="number" min="1" max="500" value={config.queue_limit} onChange={e=>setConfig({...config,queue_limit:+e.target.value})}/></label><label>Event poll interval (ms)<input type="number" min="100" max="5000" value={config.poll_interval_ms} onChange={e=>setConfig({...config,poll_interval_ms:+e.target.value})}/></label><button className="primary" onClick={saveConfig}>Save runtime settings</button></Card><Card title="API"><p>{API}</p><p className="muted">Configure with <code>VITE_API_URL</code>.</p></Card></div>}
  </main></div>
}
function Table({rows,cols}:{rows:Any[],cols:string[]}){return <div className="tableWrap"><table><thead><tr>{cols.map(c=><th key={c}>{c}</th>)}</tr></thead><tbody>{rows.map((r,i)=><tr key={i}>{cols.map(c=><td key={c}>{typeof r?.[c]==='object'?JSON.stringify(r[c]):String(r?.[c]??'—')}</td>)}</tr>)}</tbody></table></div>}

createRoot(document.getElementById('root')!).render(<App/>);
