"""
WebSocket Routes for Agentic-AI
- Provides real-time event streaming via WebSocket.
- Complements SSE for clients that prefer WebSocket.
"""

import json
from typing import Any, Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from .event_bus import get_event_bus

router = APIRouter(prefix="/api/runtime", tags=["websocket"])

# Global WebSocket connections
_websocket_connections: Set[WebSocket] = set()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time event streaming.
    - Clients can connect to receive live events.
    - Supports heartbeat, reconnect, and graceful disconnect.
    """
    await websocket.accept()
    _websocket_connections.add(websocket)

    try:
        # Send a welcome message with connection info
        welcome_message = {
            "event_type": "websocket_connected",
            "message": "Connected to Agentic-AI WebSocket",
            "timestamp": "2026-09-14T00:00:00Z",
        }
        await websocket.send_json(welcome_message)

        # Keep the connection alive
        while True:
            # Wait for messages (but we don't process them; this is just to keep the connection open)
            try:
                data = await websocket.receive_text()
                # Echo back any messages (for debugging)
                if data:
                    await websocket.send_json({
                        "event_type": "websocket_echo",
                        "message": data,
                    })
            except WebSocketDisconnect:
                break

    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        _websocket_connections.remove(websocket)


# --- EventBus Listener for WebSocket ---
def _broadcast_to_websockets(event: Dict[str, Any]) -> None:
    """Broadcast an event to all connected WebSockets."""
    for websocket in _websocket_connections:
        try:
            # Convert datetime to string for JSON serialization
            event_copy = event.copy()
            if "timestamp" in event_copy:
                event_copy["timestamp"] = str(event_copy["timestamp"])
            websocket.send_json(event_copy)
        except Exception as e:
            print(f"Failed to send WebSocket message: {e}")
            _websocket_connections.remove(websocket)


# Register the WebSocket listener with EventBus
event_bus = get_event_bus()
event_bus.add_listener(_broadcast_to_websockets)


@router.get("/ws/status")
def websocket_status() -> Dict[str, Any]:
    """
    Get the current status of WebSocket connections.
    - Returns the number of active connections.
    """
    return {
        "status": "ok",
        "active_connections": len(_websocket_connections),
    }


@router.get("/ws/test")
def websocket_test() -> HTMLResponse:
    """
    Simple HTML page to test WebSocket connection.
    - Useful for debugging WebSocket issues.
    """
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Agentic-AI WebSocket Test</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f0f0f0; }
            #messages { background: white; padding: 10px; border-radius: 5px; margin-top: 10px; }
            .message { padding: 5px; border-bottom: 1px solid #eee; }
        </style>
    </head>
    <body>
        <h1>Agentic-AI WebSocket Test</h1>
        <p>Status: <span id="status">Disconnected</span></p>
        <div id="messages"></div>
        <script>
            const ws = new WebSocket('ws://127.0.0.1:8000/api/runtime/ws');
            const messages = document.getElementById('messages');
            const status = document.getElementById('status');

            ws.onopen = () => {
                status.textContent = 'Connected';
                status.style.color = 'green';
                addMessage('Connected to WebSocket');
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                addMessage(JSON.stringify(data, null, 2));
            };

            ws.onclose = () => {
                status.textContent = 'Disconnected';
                status.style.color = 'red';
                addMessage('Disconnected from WebSocket');
            };

            ws.onerror = (error) => {
                addMessage('WebSocket error: ' + error.message);
            };

            function addMessage(message) {
                const div = document.createElement('div');
                div.className = 'message';
                div.textContent = message;
                messages.appendChild(div);
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html, status_code=200)
