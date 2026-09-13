# Agentic-AI

Self-Evaluating Agentic Architecture.

## V1 Foundation

The `v1-foundation` branch is being built as a guarded, self-evaluating agent runtime. System 1 owns permissions, execution, verification, evaluation, and recovery; future model/brain components must operate through those controls.

### Implemented V1.4

- FastAPI backend
- Task creation/list/detail
- Autonomy levels 0–5
- Editable DAG planner with dry-run and replanning
- Tool registry with SAFE/LOW/MEDIUM/HIGH/CRITICAL risk levels
- AUTO/CONFIRM/DENY permission policies
- Local deterministic `echo` and `clock` tools
- Async executor abstraction
- Per-step execution context and results
- Retry handling
- Timeout handling
- Cancellation requests
- Structured execution observations
- Per-step duration, attempt count, output and error capture
- Task execution trace endpoint
- Retry-failed-steps endpoint
- React + Vite dark control-center UI
- Execution timeline, step status, outputs, errors, retry and cancel controls
- Deterministic evaluation lifecycle placeholder

## Run backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Run frontend

```bash
cd frontend
npm install
npm run dev
```

## V1.4 execution APIs

- `POST /api/tasks/{task_id}/approve` — approve and execute the current plan
- `POST /api/tasks/{task_id}/cancel` — request cancellation
- `POST /api/tasks/{task_id}/retry` — retry a failed/cancelled task
- `GET /api/tasks/{task_id}/trace` — retrieve structured execution observations
- `GET /api/tasks/{task_id}` — retrieve current step outputs/errors/status

The V1 executor intentionally exposes only local deterministic tools. Shell, filesystem, network, browser, device-control and model-backed tools are not enabled until their own risk, sandboxing, verification and approval layers are implemented.

## Roadmap

1. Agent kernel + task state machine
2. Planner and editable plan preview
3. Tool registry + risk/permission engine
4. Executor + observation pipeline **(implemented)**
5. Deterministic verification
6. LLM-as-judge evaluation
7. Golden dataset + regression testing
8. Memory and skills
9. Human review
10. Production telemetry and continuous improvement
