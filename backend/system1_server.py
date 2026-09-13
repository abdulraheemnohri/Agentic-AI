"""Dedicated System 1 backend process.

Run from repository root with:
uvicorn backend.system1_server:app --host 127.0.0.1 --port 8101
System 1 starts automatically and has no public stop endpoint.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.system_backends import system1_backend, startup_backends, shutdown_backends

@asynccontextmanager
async def lifespan(app: FastAPI):
    await startup_backends()
    yield
    await shutdown_backends()

app = FastAPI(title="Agentic-AI System 1 Backend", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
async def health():
    return system1_backend.status()
