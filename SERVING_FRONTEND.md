# Agentic-AI — Complete Control & Frontend Serving

## Architecture

```text
                         ┌──────────────────────────────┐
                         │ React/Vite Frontend :5173    │
                         │ Observatory + Control Center │
                         └──────────────┬───────────────┘
                                        │
                         ┌──────────────▼───────────────┐
                         │ Agentic-AI API :8000         │
                         │ backend.app.server:app       │
                         └──────────────┬───────────────┘
                                        │
              ┌─────────────────────────┴─────────────────────────┐
              │                                                   │
   ┌──────────▼──────────┐                            ┌───────────▼─────────┐
   │ System 1 Backend    │                            │ System 2 Backend    │
   │ always-on           │                            │ local-only          │
   │ authoritative       │                            │ frontend controlled  │
   │ council/permission  │                            │ start/stop/update    │
   └─────────────────────┘                            └─────────────────────┘
```

The recommended integrated server exposes the existing Agentic-AI API plus `/api/backends/*`. System 1 starts automatically during application startup. System 2 remains local and can be started/stopped/restarted/updated/upgraded through the control API.

## 1. Backend setup

From repository root:

```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell
# .venv\Scripts\Activate.ps1

pip install -r backend/requirements.txt
```

## 2. Start the complete integrated backend

```bash
python -m backend.app.server
```

It listens on:

```text
http://127.0.0.1:8000
```

Health:

```text
GET http://127.0.0.1:8000/api/health
GET http://127.0.0.1:8000/api/backends/status
GET http://127.0.0.1:8000/api/backends/system1
GET http://127.0.0.1:8000/api/backends/system2
```

### System 1 behavior

- Starts automatically with the integrated application.
- Has no frontend stop endpoint.
- Remains the authoritative control plane.
- System 2 cannot authorize execution or change System 1 policy.
- Process shutdown is the only normal shutdown path.

### System 2 controls

```text
POST /api/backends/system2/start
POST /api/backends/system2/stop
POST /api/backends/system2/restart
POST /api/backends/system2/update
POST /api/backends/system2/upgrade
```

System 2 update/upgrade operations are local package/runtime operations. Remote update URLs are rejected by the lifecycle backend.

## 3. Start the React/Vite frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

The existing Agentic-AI Observatory is the main frontend. The backend lifecycle control surface is also available at:

```text
http://127.0.0.1:5173/backend-control.html
```

## 4. Backend Control Center

The control page provides:

- System 1 live status
- System 1 cycle counter
- System 1 last-cycle time
- System 1 authority/always-on indicator
- No System 1 stop control
- System 2 status/version
- System 2 start
- System 2 stop
- System 2 restart
- System 2 update
- System 2 local upgrade
- optional System 2 runtime module
- unified API detection
- dedicated-service fallback detection
- endpoint configuration stored in browser localStorage
- live JSON/audit state
- automatic 2-second refresh
- mobile responsive UI

## 5. Optional dedicated backend mode

For debugging or process isolation, the two backend services can still be run separately:

```bash
python -m backend.run_backends
```

This exposes:

```text
System 1: http://127.0.0.1:8101
System 2: http://127.0.0.1:8102
```

Do not run both the integrated server and dedicated System 1 service simultaneously if you want exactly one System 1 supervisor instance.

## 6. Frontend configuration

Copy:

```bash
cp frontend/.env.example frontend/.env
```

Available variables:

```text
VITE_API_BASE
VITE_SYSTEM1_URL
VITE_SYSTEM2_URL
```

The standalone backend-control page also allows endpoint configuration directly and stores it locally in the browser.

## 7. Production preview

Build:

```bash
cd frontend
npm run build
npm run preview
```

Preview server:

```text
http://127.0.0.1:4173
```

## 8. Security boundary

The architecture deliberately enforces:

```text
System 2 → proposal/reasoning only
System 1 → review + authorization
Tool Registry → permission/risk checks
Executor → execution
Observer → telemetry
Verifier → deterministic verification
Evaluator → quality decision
Memory → learning/history
```

Never expose the System 2 lifecycle endpoints to an untrusted public network. Keep the backend on loopback or place an authenticated reverse proxy in front of it before any LAN deployment.
