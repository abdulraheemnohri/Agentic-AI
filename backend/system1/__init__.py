"""
System 1 Authority Module
- Hosts the authoritative backend for Agentic-AI.
- Runs on 127.0.0.1:8101.
- Never modifiable by System 2 or frontend.
"""

from .service import System1Service, System1AutomaticBackend

__all__ = ["System1Service", "System1AutomaticBackend"]
