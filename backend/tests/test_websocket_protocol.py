from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from app.models.ros import SystemStatus
from app.services.rosbridge import RosbridgeService


@pytest.mark.asyncio
async def test_ping_returns_matching_pong(settings):
    service = RosbridgeService(settings)
    service.connection_manager.send_to_client = AsyncMock()

    await service._handle_message("client-1", {"op": "ping", "id": "ping-42"})

    service.connection_manager.send_to_client.assert_awaited_once_with(
        "client-1",
        {"op": "pong", "id": "ping-42"},
    )


@pytest.mark.asyncio
async def test_system_status_returns_over_websocket(settings):
    service = RosbridgeService(settings)
    service.connection_manager.send_to_client = AsyncMock()
    service.get_system_status = AsyncMock(return_value=SystemStatus(
        ros_domain_id=0,
        active_nodes=3,
        active_topics=12,
        active_connections=1,
        system_time=datetime(2026, 7, 14, 9, 0, tzinfo=timezone.utc),
        uptime=120.0,
        memory_usage=42.5,
        cpu_usage=17.25,
        cpu_temperature=51.0,
    ))

    await service._handle_message(
        "client-1",
        {"op": "get_system_status", "id": "status-7"},
    )

    service.connection_manager.send_to_client.assert_awaited_once_with(
        "client-1",
        {
            "op": "get_system_status_result",
            "status": {
                "ros_domain_id": 0,
                "active_nodes": 3,
                "active_topics": 12,
                "active_connections": 1,
                "system_time": "2026-07-14T09:00:00Z",
                "uptime": 120.0,
                "memory_usage": 42.5,
                "cpu_usage": 17.25,
                "cpu_temperature": 51.0,
            },
            "id": "status-7",
        },
    )
