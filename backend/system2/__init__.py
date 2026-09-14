"""
System 2 Intelligence Module
- Hosts the local reasoning backend for Agentic-AI.
- Runs on 127.0.0.1:8102.
- Loopback-only, non-authoritative, and replaceable.
"""

from .service import System2Service, System2LifecycleBackend

__all__ = ["System2Service", "System2LifecycleBackend"]
