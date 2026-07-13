from collections import deque
from datetime import timezone
from types import SimpleNamespace

import pytest

from app.models.ros import TopicInfo
from app.services.rosbridge import RosbridgeService


class FakeGraphNode:
    def get_topic_names_and_types(self):
        return [
            ("/idle", ["std_msgs/msg/String"]),
            ("/points", ["sensor_msgs/msg/PointCloud2"]),
            ("/unknown", ["std_msgs/msg/String"]),
        ]

    def get_publishers_info_by_topic(self, topic_name):
        if topic_name != "/points":
            return []
        return [SimpleNamespace(node_name="driver", node_namespace="/camera")]

    def get_subscriptions_info_by_topic(self, topic_name):
        if topic_name != "/points":
            return []
        return [SimpleNamespace(node_name="viewer", node_namespace="/")]


@pytest.mark.asyncio
async def test_topics_include_graph_and_observed_message_metadata(settings, monkeypatch):
    service = RosbridgeService(settings)
    service.node = FakeGraphNode()
    monkeypatch.setattr(service, "_get_topics_from_cli_sync", lambda: [TopicInfo(
        name="/points",
        message_type="sensor_msgs/msg/PointCloud2",
    )])
    monkeypatch.setattr("app.services.rosbridge.time.time", lambda: 1000.0)
    service.subscribers["/points"] = object()
    service._topic_observation_started_at["/points"] = 990.0
    service._topic_message_times["/points"] = deque([999.8, 999.9, 1000.0])
    service._topic_last_message_times["/points"] = 1000.0

    topics = await service.get_topics()

    assert len(topics) == 1
    assert topics[0].publishers == ["/camera/driver"]
    assert topics[0].subscribers == ["/viewer"]
    assert topics[0].frequency == pytest.approx(10.0)
    assert topics[0].last_message_time.tzinfo == timezone.utc
    assert topics[0].last_message_time.timestamp() == 1000.0


@pytest.mark.asyncio
async def test_frequencies_distinguish_measured_zero_from_unobserved(settings, monkeypatch):
    service = RosbridgeService(settings)
    service.node = FakeGraphNode()
    monkeypatch.setattr("app.services.rosbridge.time.time", lambda: 1000.0)
    service.subscribers["/idle"] = object()
    service._topic_observation_started_at["/idle"] = 990.0
    service.subscribers["/points"] = object()
    service._topic_observation_started_at["/points"] = 990.0
    service._topic_message_times["/points"] = deque([999.8, 999.9, 1000.0])

    frequencies = await service.get_topic_frequencies()

    assert frequencies["/points"] == pytest.approx(10.0)
    assert frequencies["/idle"] == 0.0
    assert frequencies["/unknown"] is None
