import React, {useEffect, useState} from 'react';
import {createRoot} from 'react-dom/client';
import './style.css';

type Step={id:string;title:string;tool:string;status:string;risk:string;output?:Record<string,string>};
type Task={id:string;goal:string;status:string;autonomy:number;created_at:string;steps:Step[];verification?:{passed:boolean;method:string};evaluation?:any;result?:string};
const API='http://localhost:8000/api';

function App(){
 const [goal,setGoal]=useState(''); const [tasks,setTasks]=useState<Task[]>([]); const [selected,setSelected]=useState<Task|null>(null); const [busy,setBusy]=useState(false); const [message,setMessage]=useState('');
 const load=()=>fetch(`${API}/tasks`).then(r=>r.json()).then(setTasks).catch(()=>setMessage('Backend offline — start FastAPI on port 8000.'));
 useEffect(()=>{load()},[]);
 const create=async()=>{if(!goal.trim())return;setBusy(true);setMessage('Generating guarded plan…');const r=await fetch(`${API}/tasks`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({goal,autonomy:1})});const t=await r.json();setGoal('');setSelected(t);await load();setBusy(false);setMessage('Plan ready for approval.');};
 const approve=async(ok:boolean)=>{if(!selected)return;setBusy(true);const r=await fetch(`${API}/tasks/${selected.id}/approve`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({approved:ok})});const t=await r.json();setSelected(t);await load();setBusy(false);setMessage(ok?'Execution completed and verified.':'Plan rejected.');};
 const evaluate=async()=>{if(!selected)return;const r=await fetch(`${API}/tasks/${selected.id}/evaluate`,{method:'POST'});const evaluation=await r.json();setSelected({...selected,evaluation});await load();};
 return <div className="app"><aside><div className="brand">◈ Agentic<span>-AI</span></div><nav>{['Dashboard','Agent','Planner','Tasks','Tools','Memory','Skills','Evaluations','Models','Experiments','Logs','Settings'].map((x,i)=><div className={i===0?'active':''} key={x}>{x}</div>)}</nav><div className="health"><i/> Control plane online</div></aside>
 <main><header><div><p className="eyebrow">SELF-EVALUATING AGENT • V1.1</p><h1>Control Center</h1></div><div className="pill">GUARDED MODE</div></header>
 <section className="hero"><div><h2>What should the agent do?</h2><p>Every task follows <b>Plan → Approve → Execute → Verify → Evaluate</b>.</p><div className="composer"><textarea value={goal} onChange={e=>setGoal(e.target.value)} placeholder="Describe a goal for the agent…"/><button onClick={create} disabled={busy}>{busy?'Working…':'Generate Plan →'}</button></div>{message&&<div className="notice">{message}</div>}</div></section>
 <section className="grid"><div className="card"><label>RUNNING</label><strong>{tasks.filter(t=>t.status==='running').length}</strong></div><div className="card"><label>TOTAL TASKS</label><strong>{tasks.length}</strong></div><div className="card"><label>VERIFIED</label><strong>{tasks.filter(t=>t.verification?.passed).length}</strong></div><div className="card"><label>CONTROL</label><strong>Guarded</strong></div></section>
 {selected&&<section className="panel detail"><div className="panelhead"><h3>Plan Preview</h3><button className="ghost" onClick={()=>setSelected(null)}>Close</button></div><div className="goal">{selected.goal}</div><div className="steps">{selected.steps.map((s,i)=><div className="step" key={s.id}><span className="num">{i+1}</span><div><b>{s.title}</b><small>Tool: {s.tool} · Risk: {s.risk} · {s.status}</small>{s.output&&<code>{JSON.stringify(s.output)}</code>}</div></div>)}</div><div className="actions">{selected.status==='planned'?<><button onClick={()=>approve(false)} className="ghost">Reject</button><button onClick={()=>approve(true)} disabled={busy}>Approve & Execute</button></>:<button onClick={evaluate}>Run Self-Evaluation</button>}</div>{selected.verification&&<div className="verification">✓ Verification: {selected.verification.passed?'PASSED':'FAILED'} · {selected.verification.method}</div>}{selected.evaluation&&<div className="evaluation"><b>Deterministic evaluation: {selected.evaluation.deterministic?.status}</b><span>Score: {selected.evaluation.deterministic?.score ?? '—'}</span></div>}</section>}
 <section className="panel"><div className="panelhead"><h3>Recent Tasks</h3><button className="ghost" onClick={load}>Refresh</button></div>{tasks.length===0?<div className="empty">No tasks yet. Create your first agent task above.</div>:tasks.map(t=><button className="task" key={t.id} onClick={()=>setSelected(t)}><div><b>{t.goal}</b><small>{new Date(t.created_at).toLocaleString()}</small></div><span className={t.status}>{t.status}</span></button>)}</section>
 </main></div>
}
createRoot(document.getElementById('root')!).render(<App/>);
