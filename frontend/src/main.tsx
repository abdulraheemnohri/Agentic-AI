import React, {useEffect, useState} from 'react';
import {createRoot} from 'react-dom/client';
import './style.css';

type Task = {id:string; goal:string; status:string; autonomy:number; created_at:string};
const API = 'http://localhost:8000/api';

function App(){
 const [goal,setGoal]=useState(''); const [tasks,setTasks]=useState<Task[]>([]); const [busy,setBusy]=useState(false);
 const load=()=>fetch(`${API}/tasks`).then(r=>r.json()).then(setTasks).catch(()=>{});
 useEffect(()=>{load()},[]);
 const create=async()=>{if(!goal.trim())return;setBusy(true);await fetch(`${API}/tasks`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({goal,autonomy:1})});setGoal('');await load();setBusy(false)};
 return <div className="app"><aside><div className="brand">◈ Agentic<span>-AI</span></div><nav>{['Dashboard','Agent','Planner','Tasks','Tools','Memory','Skills','Evaluations','Models','Experiments','Logs','Settings'].map((x,i)=><div className={i===0?'active':''} key={x}>{x}</div>)}</nav><div className="health">● Core online</div></aside><main><header><div><p className="eyebrow">SELF-EVALUATING AGENT</p><h1>Control Center</h1></div><div className="pill">V1 Foundation</div></header><section className="hero"><div><h2>What should the agent do?</h2><p>Describe a goal. The agent will create a plan before execution.</p><div className="composer"><textarea value={goal} onChange={e=>setGoal(e.target.value)} placeholder="e.g. Analyze my project and identify the three highest-priority improvements..."/><button onClick={create} disabled={busy}>{busy?'Creating…':'Generate Plan →'}</button></div></div></section><section className="grid"><div className="card"><label>ACTIVE TASKS</label><strong>{tasks.filter(t=>t.status==='running').length}</strong></div><div className="card"><label>TOTAL TASKS</label><strong>{tasks.length}</strong></div><div className="card"><label>EVALUATION</label><strong>—</strong></div><div className="card"><label>CONTROL MODE</label><strong>Guarded</strong></div></section><section className="panel"><div className="panelhead"><h3>Recent Tasks</h3><button className="ghost" onClick={load}>Refresh</button></div>{tasks.length===0?<div className="empty">No tasks yet. Create your first agent task above.</div>:tasks.map(t=><div className="task" key={t.id}><div><b>{t.goal}</b><small>{new Date(t.created_at).toLocaleString()}</small></div><span>{t.status}</span></div>)}</section></main></div>
}
createRoot(document.getElementById('root')!).render(<App/>);
