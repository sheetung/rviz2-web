from datetime import datetime
from unittest.mock import AsyncMock

import asyncio
import pytest

from app.models.ros import ConnectionInfo
from app.services.connection_manager import ConnectionManager


@pytest.mark.asyncio
async def test_slow_client_close_preserves_ownership_until_service_cleanup():
    manager = ConnectionManager(outbound_queue_size=1, send_timeout=0.01)
    websocket = AsyncMock()
    manager.active_connections["client-1"] = websocket
    manager.connection_info["client-1"] = ConnectionInfo(
        client_id="client-1",
        connected_at=datetime.now(),
        subscribed_topics=["/scan"],
        advertised_topics={"/goal_pose": "geometry_msgs/msg/PoseStamped"},
    )
    queue = asyncio.Queue(maxsize=1)
    queue.put_nowait("already full")
    manager._send_queues["client-1"] = queue

    assert not await manager.send_to_client("client-1", {"op": "pong"})

    websocket.close.assert_awaited_once_with(
        code=1011,
        reason="Outbound queue timeout",
    )
    assert "client-1" in manager.connection_info
    assert manager.connection_info["client-1"].subscribed_topics == ["/scan"]
