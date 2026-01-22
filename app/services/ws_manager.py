"""
WebSocket Connection Manager for Pose Detection.

Manages WebSocket connections for real-time pose detection streaming.
Provides connection lifecycle management, broadcasting, and cleanup.

Author: MEMOTION Team
Version: 1.0.0
"""

import logging
import asyncio
import time
from typing import Dict, Set, Optional, Any, Callable
from dataclasses import dataclass, field
from fastapi import WebSocket, WebSocketDisconnect
import json

logger = logging.getLogger(__name__)


@dataclass
class WebSocketConnection:
    """
    Represents a single WebSocket connection.
    
    Attributes:
        websocket: The WebSocket instance
        session_id: Associated pose detection session ID
        user_id: Optional user identifier
        connected_at: Connection timestamp
        last_activity: Last activity timestamp
        is_active: Whether connection is active
        frame_count: Number of frames processed
        error_count: Number of errors encountered
    """
    websocket: WebSocket
    session_id: str
    user_id: Optional[str] = None
    connected_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    is_active: bool = True
    frame_count: int = 0
    error_count: int = 0
    
    def __hash__(self) -> int:
        """Make hashable using id of websocket and session_id."""
        return hash((id(self.websocket), self.session_id))
    
    def __eq__(self, other: object) -> bool:
        """Compare by websocket identity and session_id."""
        if not isinstance(other, WebSocketConnection):
            return False
        return id(self.websocket) == id(other.websocket) and self.session_id == other.session_id
    
    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = time.time()
    
    def increment_frame(self) -> None:
        """Increment frame count."""
        self.frame_count += 1
        self.update_activity()
    
    def increment_error(self) -> None:
        """Increment error count."""
        self.error_count += 1


class WebSocketConnectionManager:
    """
    Manages WebSocket connections for pose detection sessions.
    
    Features:
        - Connection lifecycle management (connect, disconnect, cleanup)
        - Session-based connection grouping
        - Broadcasting to session connections
        - Connection health monitoring
        - Automatic cleanup of stale connections
    
    Usage:
        manager = WebSocketConnectionManager()
        
        # In WebSocket endpoint
        await manager.connect(websocket, session_id)
        try:
            while True:
                data = await websocket.receive_json()
                result = process_frame(data)
                await manager.send_to_session(session_id, result)
        except WebSocketDisconnect:
            await manager.disconnect(websocket, session_id)
    """
    
    def __init__(self, max_connections_per_session: int = 5):
        """
        Initialize WebSocket Connection Manager.
        
        Args:
            max_connections_per_session: Maximum connections per session
        """
        # session_id -> set of WebSocketConnection
        self._connections: Dict[str, Set[WebSocketConnection]] = {}
        # websocket -> WebSocketConnection (for fast lookup)
        self._websocket_map: Dict[WebSocket, WebSocketConnection] = {}
        self._max_per_session = max_connections_per_session
        self._lock = asyncio.Lock()
        
        logger.info(
            f"WebSocketConnectionManager initialized: "
            f"max_per_session={max_connections_per_session}"
        )
    
    async def connect(
        self, 
        websocket: WebSocket, 
        session_id: str,
        user_id: Optional[str] = None
    ) -> WebSocketConnection:
        """
        Accept and register a new WebSocket connection.
        
        Args:
            websocket: WebSocket instance
            session_id: Pose detection session ID
            user_id: Optional user identifier
        
        Returns:
            WebSocketConnection: The registered connection
        
        Raises:
            Exception: If max connections reached
        """
        async with self._lock:
            # Initialize session set if needed
            if session_id not in self._connections:
                self._connections[session_id] = set()
            
            # Check max connections
            if len(self._connections[session_id]) >= self._max_per_session:
                logger.warning(
                    f"Max connections reached for session: {session_id}"
                )
                await websocket.close(code=4003, reason="Max connections reached")
                raise Exception(f"Max connections ({self._max_per_session}) reached")
            
            # Accept connection
            await websocket.accept()
            
            # Create connection object
            connection = WebSocketConnection(
                websocket=websocket,
                session_id=session_id,
                user_id=user_id
            )
            
            # Register connection
            self._connections[session_id].add(connection)
            self._websocket_map[websocket] = connection
            
            logger.info(
                f"WebSocket connected: session_id={session_id}, "
                f"user_id={user_id}, total={len(self._connections[session_id])}"
            )
            
            return connection
    
    async def disconnect(self, websocket: WebSocket, session_id: str) -> None:
        """
        Disconnect and unregister a WebSocket connection.
        
        Args:
            websocket: WebSocket instance
            session_id: Pose detection session ID
        """
        async with self._lock:
            # Get connection
            connection = self._websocket_map.get(websocket)
            if not connection:
                return
            
            # Mark as inactive
            connection.is_active = False
            
            # Remove from session set
            if session_id in self._connections:
                self._connections[session_id].discard(connection)
                
                # Cleanup empty session
                if not self._connections[session_id]:
                    del self._connections[session_id]
            
            # Remove from websocket map
            del self._websocket_map[websocket]
            
            logger.info(
                f"WebSocket disconnected: session_id={session_id}, "
                f"frames={connection.frame_count}, errors={connection.error_count}"
            )
    
    async def send_to_connection(
        self, 
        websocket: WebSocket, 
        data: Dict[str, Any]
    ) -> bool:
        """
        Send data to a specific WebSocket connection.
        
        Args:
            websocket: WebSocket instance
            data: Data to send (will be JSON encoded)
        
        Returns:
            bool: True if sent successfully
        """
        connection = self._websocket_map.get(websocket)
        if not connection or not connection.is_active:
            return False
        
        try:
            await websocket.send_json(data)
            connection.increment_frame()
            return True
        except Exception as e:
            connection.increment_error()
            logger.error(f"Failed to send to WebSocket: {e}")
            return False
    
    async def send_to_session(
        self, 
        session_id: str, 
        data: Dict[str, Any]
    ) -> int:
        """
        Broadcast data to all connections in a session.
        
        Args:
            session_id: Pose detection session ID
            data: Data to broadcast
        
        Returns:
            int: Number of connections that received the data
        """
        if session_id not in self._connections:
            return 0
        
        sent_count = 0
        dead_connections = []
        
        for connection in self._connections[session_id]:
            try:
                if connection.is_active:
                    await connection.websocket.send_json(data)
                    connection.increment_frame()
                    sent_count += 1
            except Exception as e:
                connection.increment_error()
                dead_connections.append(connection)
                logger.warning(f"Failed to send to connection: {e}")
        
        # Cleanup dead connections
        for conn in dead_connections:
            await self.disconnect(conn.websocket, session_id)
        
        return sent_count
    
    def get_connection(self, websocket: WebSocket) -> Optional[WebSocketConnection]:
        """Get connection object for a WebSocket."""
        return self._websocket_map.get(websocket)
    
    def get_session_connections(self, session_id: str) -> Set[WebSocketConnection]:
        """Get all connections for a session."""
        return self._connections.get(session_id, set())
    
    def get_session_count(self, session_id: str) -> int:
        """Get connection count for a session."""
        return len(self._connections.get(session_id, set()))
    
    def get_total_connections(self) -> int:
        """Get total connection count across all sessions."""
        return len(self._websocket_map)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        return {
            "total_connections": self.get_total_connections(),
            "sessions_with_connections": len(self._connections),
            "connections_per_session": {
                sid: len(conns) for sid, conns in self._connections.items()
            }
        }
    
    async def cleanup_session(self, session_id: str) -> int:
        """
        Cleanup all connections for a session.
        
        Args:
            session_id: Session ID to cleanup
        
        Returns:
            int: Number of connections closed
        """
        if session_id not in self._connections:
            return 0
        
        connections = list(self._connections[session_id])
        count = 0
        
        for connection in connections:
            try:
                connection.is_active = False
                await connection.websocket.close(code=1000, reason="Session ended")
                count += 1
            except Exception as e:
                logger.warning(f"Error closing WebSocket: {e}")
            finally:
                await self.disconnect(connection.websocket, session_id)
        
        logger.info(f"Cleaned up {count} connections for session: {session_id}")
        return count
    
    async def cleanup_all(self) -> int:
        """
        Cleanup all connections.
        
        Returns:
            int: Number of connections closed
        """
        session_ids = list(self._connections.keys())
        total = 0
        
        for session_id in session_ids:
            total += await self.cleanup_session(session_id)
        
        return total


# ==================== GLOBAL INSTANCE ====================

ws_connection_manager = WebSocketConnectionManager()
