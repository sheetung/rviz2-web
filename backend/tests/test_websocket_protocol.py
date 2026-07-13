from unittest.mock import AsyncMock

import pytest

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
