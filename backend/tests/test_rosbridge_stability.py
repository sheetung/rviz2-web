from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest

from app.models.ros import ConnectionInfo
from app.services.rosbridge import RosbridgeService


def test_client_ids_are_unique_under_connection_bursts(settings):
    service = RosbridgeService(settings)

    client_ids = {service._new_client_id() for _ in range(10_000)}

    assert len(client_ids) == 10_000
    assert all(client_id.startswith("client_") for client_id in client_ids)


@pytest.mark.asyncio
async def test_message_cache_does_not_retain_serialized_payloads(settings):
    service = RosbridgeService(settings)
    service.connection_manager.connection_info["client-1"] = ConnectionInfo(
        client_id="client-1",
        connected_at=datetime.now(),
        subscribed_topics=["/large_points"],
        message_count=0,
    )
    large_payload = {"data": "x" * 1_000_000, "data_encoding": "base64"}
    service._converter.to_dict = Mock(return_value=large_payload)
    service.connection_manager.broadcast = AsyncMock(return_value=True)

    await service._on_message_received("/large_points", object())

    service.connection_manager.broadcast.assert_awaited_once()
    assert len(service.message_cache) == 1
    assert service.message_cache[0]["topic"] == "/large_points"
    assert "message" not in service.message_cache[0]
