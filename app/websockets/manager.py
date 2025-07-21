from typing import Dict, Set, Any, Optional, List
import json
import asyncio
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger
from pydantic import BaseModel
from enum import Enum

from app.auth.dependencies import get_current_user_optional


class ConnectionType(str, Enum):
    JOB_UPDATES = "job_updates"
    SYSTEM_STATUS = "system_status"
    GENERAL = "general"


class WebSocketMessage(BaseModel):
    type: str
    data: Any
    timestamp: str = None
    
    def __init__(self, **data):
        if 'timestamp' not in data:
            data['timestamp'] = datetime.utcnow().isoformat()
        super().__init__(**data)


class WebSocketConnection:
    """Represents a WebSocket connection with metadata."""
    
    def __init__(self, websocket: WebSocket, user_id: str = None, connection_type: ConnectionType = ConnectionType.GENERAL):
        self.websocket = websocket
        self.user_id = user_id
        self.connection_type = connection_type
        self.connected_at = datetime.utcnow()
        self.last_ping = datetime.utcnow()
        self.subscriptions: Set[str] = set()  # Topics this connection is subscribed to
    
    async def send_message(self, message: WebSocketMessage):
        """Send a message to this connection."""
        try:
            await self.websocket.send_text(message.json())
            self.last_ping = datetime.utcnow()
        except Exception as e:
            logger.error(f"Failed to send WebSocket message: {e}")
            raise
    
    async def send_json(self, data: Dict[str, Any], message_type: str = "data"):
        """Send JSON data as a WebSocket message."""
        message = WebSocketMessage(type=message_type, data=data)
        await self.send_message(message)
    
    def subscribe(self, topic: str):
        """Subscribe to a topic."""
        self.subscriptions.add(topic)
    
    def unsubscribe(self, topic: str):
        """Unsubscribe from a topic."""
        self.subscriptions.discard(topic)
    
    def is_subscribed(self, topic: str) -> bool:
        """Check if subscribed to a topic."""
        return topic in self.subscriptions


class WebSocketManager:
    """Manages WebSocket connections and broadcasting."""
    
    def __init__(self):
        # Connection management
        self.connections: Dict[str, WebSocketConnection] = {}  # connection_id -> connection
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> set of connection_ids
        self.topic_connections: Dict[str, Set[str]] = {}  # topic -> set of connection_ids
        
        # Statistics
        self.total_connections = 0
        self.message_count = 0
        
        # Background tasks
        self._cleanup_task = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start the periodic cleanup task."""
        async def cleanup_stale_connections():
            while True:
                try:
                    await asyncio.sleep(60)  # Run every minute
                    await self._cleanup_stale_connections()
                except Exception as e:
                    logger.error(f"Error in cleanup task: {e}")
        
        self._cleanup_task = asyncio.create_task(cleanup_stale_connections())
    
    async def _cleanup_stale_connections(self):
        """Remove stale connections."""
        current_time = datetime.utcnow()
        stale_connections = []
        
        for conn_id, connection in self.connections.items():
            # Consider connections stale if no ping for 5 minutes
            if (current_time - connection.last_ping).seconds > 300:
                stale_connections.append(conn_id)
        
        for conn_id in stale_connections:
            await self.disconnect(conn_id)
            logger.info(f"Cleaned up stale WebSocket connection: {conn_id}")
    
    async def connect(self, websocket: WebSocket, user_id: str = None, connection_type: ConnectionType = ConnectionType.GENERAL) -> str:
        """Accept a new WebSocket connection."""
        await websocket.accept()
        
        # Generate connection ID
        connection_id = f"conn_{self.total_connections}_{datetime.utcnow().timestamp()}"
        
        # Create connection object
        connection = WebSocketConnection(
            websocket=websocket,
            user_id=user_id,
            connection_type=connection_type
        )
        
        # Store connection
        self.connections[connection_id] = connection
        self.total_connections += 1
        
        # Track user connections
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)
        
        logger.info(f"WebSocket connected: {connection_id} (user: {user_id}, type: {connection_type})")
        
        # Send welcome message
        await connection.send_json({
            "connection_id": connection_id,
            "message": "Connected to WebSet Miner",
            "server_time": datetime.utcnow().isoformat()
        }, "welcome")
        
        return connection_id
    
    async def disconnect(self, connection_id: str):
        """Disconnect a WebSocket connection."""
        if connection_id not in self.connections:
            return
        
        connection = self.connections[connection_id]
        
        # Remove from user connections
        if connection.user_id and connection.user_id in self.user_connections:
            self.user_connections[connection.user_id].discard(connection_id)
            if not self.user_connections[connection.user_id]:
                del self.user_connections[connection.user_id]
        
        # Remove from topic subscriptions
        for topic in list(connection.subscriptions):
            await self.unsubscribe_from_topic(connection_id, topic)
        
        # Remove connection
        del self.connections[connection_id]
        
        logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def send_to_connection(self, connection_id: str, data: Dict[str, Any], message_type: str = "data") -> bool:
        """Send data to a specific connection."""
        if connection_id not in self.connections:
            return False
        
        try:
            await self.connections[connection_id].send_json(data, message_type)
            self.message_count += 1
            return True
        except Exception as e:
            logger.error(f"Failed to send to connection {connection_id}: {e}")
            await self.disconnect(connection_id)
            return False
    
    async def send_to_user(self, user_id: str, data: Dict[str, Any], message_type: str = "data") -> int:
        """Send data to all connections for a specific user."""
        if user_id not in self.user_connections:
            return 0
        
        sent_count = 0
        for connection_id in list(self.user_connections[user_id]):
            if await self.send_to_connection(connection_id, data, message_type):
                sent_count += 1
        
        return sent_count
    
    async def broadcast_to_topic(self, topic: str, data: Dict[str, Any], message_type: str = "data") -> int:
        """Broadcast data to all connections subscribed to a topic."""
        if topic not in self.topic_connections:
            return 0
        
        sent_count = 0
        for connection_id in list(self.topic_connections[topic]):
            if await self.send_to_connection(connection_id, data, message_type):
                sent_count += 1
        
        return sent_count
    
    async def broadcast_to_all(self, data: Dict[str, Any], message_type: str = "broadcast") -> int:
        """Broadcast data to all connections."""
        sent_count = 0
        for connection_id in list(self.connections.keys()):
            if await self.send_to_connection(connection_id, data, message_type):
                sent_count += 1
        
        return sent_count
    
    async def subscribe_to_topic(self, connection_id: str, topic: str) -> bool:
        """Subscribe a connection to a topic."""
        if connection_id not in self.connections:
            return False
        
        connection = self.connections[connection_id]
        connection.subscribe(topic)
        
        # Add to topic connections
        if topic not in self.topic_connections:
            self.topic_connections[topic] = set()
        self.topic_connections[topic].add(connection_id)
        
        logger.debug(f"Connection {connection_id} subscribed to topic: {topic}")
        return True
    
    async def unsubscribe_from_topic(self, connection_id: str, topic: str) -> bool:
        """Unsubscribe a connection from a topic."""
        if connection_id not in self.connections:
            return False
        
        connection = self.connections[connection_id]
        connection.unsubscribe(topic)
        
        # Remove from topic connections
        if topic in self.topic_connections:
            self.topic_connections[topic].discard(connection_id)
            if not self.topic_connections[topic]:
                del self.topic_connections[topic]
        
        logger.debug(f"Connection {connection_id} unsubscribed from topic: {topic}")
        return True
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        return {
            "active_connections": len(self.connections),
            "total_connections": self.total_connections,
            "messages_sent": self.message_count,
            "active_users": len(self.user_connections),
            "active_topics": len(self.topic_connections),
            "connections_by_type": {
                conn_type.value: len([
                    conn for conn in self.connections.values() 
                    if conn.connection_type == conn_type
                ])
                for conn_type in ConnectionType
            }
        }
    
    def get_topics(self) -> List[str]:
        """Get list of active topics."""
        return list(self.topic_connections.keys())
    
    async def handle_websocket(self, websocket: WebSocket, connection_type: ConnectionType = ConnectionType.GENERAL, user_id: str = None):
        """Handle a WebSocket connection lifecycle."""
        connection_id = None
        try:
            # Connect
            connection_id = await self.connect(websocket, user_id, connection_type)
            
            # Handle messages
            while True:
                try:
                    # Receive message
                    message = await websocket.receive_text()
                    data = json.loads(message)
                    
                    # Handle different message types
                    await self._handle_message(connection_id, data)
                    
                except WebSocketDisconnect:
                    break
                except json.JSONDecodeError:
                    await self.send_to_connection(connection_id, {
                        "error": "Invalid JSON message"
                    }, "error")
                except Exception as e:
                    logger.error(f"Error handling WebSocket message: {e}")
                    await self.send_to_connection(connection_id, {
                        "error": str(e)
                    }, "error")
        
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
        
        finally:
            if connection_id:
                await self.disconnect(connection_id)
    
    async def _handle_message(self, connection_id: str, data: Dict[str, Any]):
        """Handle incoming WebSocket messages."""
        message_type = data.get("type", "unknown")
        
        if message_type == "subscribe":
            topic = data.get("topic")
            if topic:
                await self.subscribe_to_topic(connection_id, topic)
                await self.send_to_connection(connection_id, {
                    "message": f"Subscribed to topic: {topic}",
                    "topic": topic
                }, "subscription_confirmed")
        
        elif message_type == "unsubscribe":
            topic = data.get("topic")
            if topic:
                await self.unsubscribe_from_topic(connection_id, topic)
                await self.send_to_connection(connection_id, {
                    "message": f"Unsubscribed from topic: {topic}",
                    "topic": topic
                }, "unsubscription_confirmed")
        
        elif message_type == "ping":
            await self.send_to_connection(connection_id, {
                "message": "pong",
                "server_time": datetime.utcnow().isoformat()
            }, "pong")
        
        elif message_type == "get_stats":
            stats = self.get_connection_stats()
            await self.send_to_connection(connection_id, stats, "stats")
        
        elif message_type == "get_topics":
            topics = self.get_topics()
            await self.send_to_connection(connection_id, {
                "topics": topics
            }, "topics")
        
        else:
            logger.warning(f"Unknown WebSocket message type: {message_type}")


# Global WebSocket manager instance
_websocket_manager = None

def get_websocket_manager() -> WebSocketManager:
    """Get the global WebSocket manager instance."""
    global _websocket_manager
    if _websocket_manager is None:
        _websocket_manager = WebSocketManager()
    return _websocket_manager