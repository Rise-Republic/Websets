import asyncio
import json
import pytest
from datetime import timedelta
from fastapi import WebSocketDisconnect

from app.websockets.manager import WebSocketManager, ConnectionType

class DummyWebSocket:
    def __init__(self, recv=None):
        self.sent = []
        self.accepted = False
        self.recv_queue = asyncio.Queue()
        if recv:
            for msg in recv:
                self.recv_queue.put_nowait(msg)

    async def accept(self):
        self.accepted = True

    async def send_text(self, text):
        self.sent.append(text)

    async def receive_text(self):
        if self.recv_queue.empty():
            raise WebSocketDisconnect()
        return await self.recv_queue.get()

@pytest.mark.asyncio
async def test_connect_subscribe_broadcast_unsubscribe():
    ws = DummyWebSocket()
    manager = WebSocketManager()
    conn_id = await manager.connect(ws, user_id="u1", connection_type=ConnectionType.GENERAL)
    assert conn_id in manager.connections
    assert "u1" in manager.user_connections

    await manager.subscribe_to_topic(conn_id, "topic")
    await manager.broadcast_to_topic("topic", {"x": 1}, "data")
    assert len(ws.sent) == 2
    data = json.loads(ws.sent[-1])
    assert data["type"] == "data"
    assert data["data"]["x"] == 1

    await manager.unsubscribe_from_topic(conn_id, "topic")
    await manager.broadcast_to_topic("topic", {"y": 2})
    assert len(ws.sent) == 2

    await manager.disconnect(conn_id)
    assert conn_id not in manager.connections
    manager._cleanup_task.cancel()

@pytest.mark.asyncio
async def test_handle_message_ping_and_unknown():
    ws = DummyWebSocket()
    manager = WebSocketManager()
    conn_id = await manager.connect(ws)

    await manager._handle_message(conn_id, {"type": "ping"})
    await manager._handle_message(conn_id, {"type": "unknown"})

    assert any("pong" in s for s in ws.sent)
    manager._cleanup_task.cancel()

@pytest.mark.asyncio
async def test_cleanup_stale_connections():
    ws = DummyWebSocket()
    manager = WebSocketManager()
    conn_id = await manager.connect(ws)
    # make connection stale
    manager.connections[conn_id].last_ping -= timedelta(seconds=301)
    await manager._cleanup_stale_connections()
    assert conn_id not in manager.connections
    manager._cleanup_task.cancel()

@pytest.mark.asyncio
async def test_stats_and_send_to_user():
    ws1 = DummyWebSocket()
    ws2 = DummyWebSocket()
    manager = WebSocketManager()
    id1 = await manager.connect(ws1, user_id="u")
    id2 = await manager.connect(ws2, user_id="u")
    await manager.send_to_user("u", {"hi": "there"}, "notice")
    assert any("notice" in s for s in ws1.sent)
    assert any("notice" in s for s in ws2.sent)
    stats = manager.get_connection_stats()
    assert stats["active_connections"] == 2
    await manager.broadcast_to_all({"b": 1})
    assert len(ws1.sent) >= 2 and len(ws2.sent) >= 2
    await manager.disconnect(id1)
    await manager.disconnect(id2)
    manager._cleanup_task.cancel()

@pytest.mark.asyncio
async def test_handle_message_get_topics_and_stats():
    ws = DummyWebSocket()
    manager = WebSocketManager()
    cid = await manager.connect(ws)
    await manager.subscribe_to_topic(cid, "t")
    await manager._handle_message(cid, {"type": "get_topics"})
    await manager._handle_message(cid, {"type": "get_stats"})
    topics = json.loads(ws.sent[-2])
    assert "t" in topics["data"]["topics"]
    stats = json.loads(ws.sent[-1])
    assert stats["data"]["active_connections"] == 1
    await manager.disconnect(cid)
    manager._cleanup_task.cancel()

@pytest.mark.asyncio
async def test_handle_websocket_flow():
    messages = [
        json.dumps({"type": "subscribe", "topic": "t"}),
        json.dumps({"type": "ping"}),
        json.dumps({"type": "unsubscribe", "topic": "t"})
    ]
    ws = DummyWebSocket(recv=messages)
    manager = WebSocketManager()
    await manager.handle_websocket(ws)
    sent = [json.loads(m)["type"] for m in ws.sent]
    assert "welcome" in sent
    assert "pong" in sent
    manager._cleanup_task.cancel()
