# Agentic-AI

Self-Evaluating Agentic Architecture.

## V1 Foundation

This branch contains the first runnable foundation for the Agentic-AI platform:

- FastAPI backend
- Task creation and task listing
- Guarded autonomy level (0–5)
- Evaluation lifecycle placeholder
- React + Vite dashboard
- Modern dark control-center UI
- Clear separation between agent control and frontend

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

The V1 execution architecture is intentionally guarded: planning, verification, evaluation, permissions, and recovery are separate modules to be implemented incrementally rather than allowing the model to directly control the system.

## Roadmap

1. Agent kernel + task state machine
2. Planner and editable plan preview
3. Tool registry + risk/permission engine
4. Executor + observation pipeline
5. Deterministic verification
6. LLM-as-judge evaluation
7. Golden dataset + regression testing
8. Memory and skills
9. Human review
10. Production telemetry and continuous improvement
