# Agentic-AI — Two Backends / One Frontend

## Architecture

```text
                         FRONTEND
                 React/Vite Control Center
                          │
             ┌────────────┴────────────┐
             │                         │
             ▼                         ▼
     SYSTEM 1 BACKEND           SYSTEM 2 BACKEND
       127.0.0.1:8101             127.0.0.1:8102
       ALWAYS AUTOMATIC            LOCAL ONLY
       AUTHORITY                   FRONTEND CONTROL
             │                         │
             │                         ├─ Start
             │                         ├─ Stop
             │                         ├─ Restart
             │                         ├─ Update
             │                         └─ Upgrade
             │
             └──── authorization / policy / safety
                         │
                         ▼
                    Agent Executor
```

## System 1 Backend

Location: `backend/system1/` and `backend/system1_server.py`.

Rules:
- starts automatically with its backend process;
- continuously runs its supervisor cycle;
- cannot be stopped by the frontend;
- owns authority, policy, risk and authorization;
- System 2 never receives authority from System 1;
- remote provider failure can fall back to the built-in System 1 guard;
- frontend is read-only for System 1 runtime lifecycle.

Endpoint:
- `GET http://127.0.0.1:8101/health`

## System 2 Backend

Location: `backend/system2/` and `backend/system2_server.py`.

Rules:
- local/loopback runtime only;
- frontend controls lifecycle;
- start, stop, restart, update and upgrade are exposed;
- remote update URLs are rejected;
- upgrade paths must remain inside the backend root;
- System 2 is reasoning/proposal only;
- System 2 cannot authorize or execute tools.

Endpoints:
- `GET /health`
- `POST /control/start`
- `POST /control/stop`
- `POST /control/restart`
- `POST /control/update`
- `POST /control/upgrade`

## Frontend

The existing Agentic-AI frontend remains the primary application UI. A unified backend-management surface is also available at:

`/backend-control.html`

It provides:
- System 1 live health/cycle status;
- System 1 automatic/authority indicator;
- System 2 status;
- System 2 Start/Stop/Restart;
- System 2 Update;
- System 2 version upgrade;
- live 2-second status refresh;
- explicit security boundary information.

## Start

From repository root:

```bash
python -m pip install -r backend/requirements.txt
python backend/run_backends.py
```

Start the frontend separately with the existing Vite commands.

System 1: `8101`
System 2: `8102`
Main Agentic-AI API: `8000`

## Security boundary

The split does **not** create a second authority. System 1 remains the authoritative control plane. System 2 can be stopped or upgraded from the frontend, but a stopped System 2 cannot cause System 1 to stop. The main executor must continue to enforce System 1 council decisions and tool permissions.
