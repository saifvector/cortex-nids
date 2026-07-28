"""
WebSocket Server module for NIDS.
Streams real-time threat predictions and alerts to connected frontend clients.
"""
import asyncio
import json
import logging
from typing import Any, Dict, Set

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages active WebSocket client connections and broadcasts live threat telemetry events.
    """

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        """Accepts new WebSocket connection and adds to broadcast pool."""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info("WebSocket Client connected. Active connections: %d", len(self.active_connections))

    def disconnect(self, websocket: WebSocket) -> None:
        """Removes disconnected WebSocket client."""
        self.active_connections.discard(websocket)
        logger.info("WebSocket Client disconnected. Remaining connections: %d", len(self.active_connections))

    async def broadcast(self, message: Dict[str, Any]) -> None:
        """Broadcasts JSON payload to all active WebSocket clients."""
        if not self.active_connections:
            return

        payload = json.dumps(message)
        disconnected = set()

        for connection in self.active_connections:
            try:
                await connection.send_text(payload)
            except Exception as e:
                logger.warning("Error sending WebSocket message: %s", e)
                disconnected.add(connection)

        for dead_conn in disconnected:
            self.disconnect(dead_conn)


# Shared ConnectionManager singleton
ws_manager = ConnectionManager()
