"""
ROS2 相关 API 端点
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
import logging

from pydantic import BaseModel, Field

from ...models.ros import (
    TopicInfo, NodeInfo, SystemStatus
)
from ...services.rosbridge import RosbridgeService
from ...services.dependencies import get_rosbridge_service

router = APIRouter()
logger = logging.getLogger(__name__)


class TopicSubscriptionRequest(BaseModel):
    topic: str = Field(..., description="ROS2 topic name")
    message_type: Optional[str] = Field(None, description="ROS2 message type")


class TopicPublishRequest(BaseModel):
    topic: str = Field(..., description="ROS2 topic name")
    message_type: str = Field(..., description="ROS2 message type")
    msg: Dict[str, Any] = Field(..., description="ROS message payload")


@router.get("/topics", response_model=List[TopicInfo])
async def get_topics(
    service: RosbridgeService = Depends(get_rosbridge_service)
):
    """获取所有 ROS2 主题列表"""
    try:
        topics = await service.get_topics()
        return topics
    except Exception as e:
        logger.error(f"Failed to get topics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/topics/frequencies", response_model=Dict[str, Optional[float]])
async def get_topic_frequencies(
    service: RosbridgeService = Depends(get_rosbridge_service)
):
    """获取后端已观察主题的频率；未订阅或样本不足时返回 null。"""
    try:
        frequencies = await service.get_topic_frequencies()
        return frequencies
    except Exception as e:
        logger.error(f"Failed to get topic frequencies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/topic-info", response_model=TopicInfo)
async def get_topic_info_by_query(
    topic_name: str,
    service: RosbridgeService = Depends(get_rosbridge_service)
):
    """通过 query 参数获取主题信息，支持包含 / 的 ROS topic 名。"""
    try:
        topic_info = await service.get_topic_info(topic_name)
        if not topic_info:
            raise HTTPException(status_code=404, detail=f"Topic {topic_name} not found")
        return topic_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get topic info for {topic_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/topics/subscribe")
async def subscribe_topic_by_body(
    payload: TopicSubscriptionRequest,
    service: RosbridgeService = Depends(get_rosbridge_service)
):
    """通过请求体订阅主题，支持包含 / 的 ROS topic 名。"""
    try:
        success = await service.subscribe_topic(payload.topic, payload.message_type)
        return {"success": success, "topic": payload.topic, "action": "subscribed"}
    except Exception as e:
        logger.error(f"Failed to subscribe to {payload.topic}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/topics/unsubscribe")
async def unsubscribe_topic_by_body(
    payload: TopicSubscriptionRequest,
    service: RosbridgeService = Depends(get_rosbridge_service)
):
    """通过请求体取消订阅主题，支持包含 / 的 ROS topic 名。"""
    try:
        success = await service.unsubscribe_topic(payload.topic)
        return {"success": success, "topic": payload.topic, "action": "unsubscribed"}
    except Exception as e:
        logger.error(f"Failed to unsubscribe from {payload.topic}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/topics/publish")
async def publish_message_by_body(
    payload: TopicPublishRequest,
    service: RosbridgeService = Depends(get_rosbridge_service)
):
    """通过请求体发布消息，支持包含 / 的 ROS topic 名。"""
    try:
        success = await service.publish_message(
            payload.topic,
            payload.msg,
            payload.message_type,
        )
        return {"success": success, "topic": payload.topic, "action": "published"}
    except Exception as e:
        logger.error(f"Failed to publish to {payload.topic}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/nodes", response_model=List[NodeInfo])
async def get_nodes(
    service: RosbridgeService = Depends(get_rosbridge_service)
):
    """获取所有 ROS2 节点列表"""
    try:
        nodes = await service.get_nodes()
        return nodes
    except Exception as e:
        logger.error(f"Failed to get nodes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/nodes/{node_name}", response_model=NodeInfo)
async def get_node_info(
    node_name: str,
    service: RosbridgeService = Depends(get_rosbridge_service)
):
    """获取特定节点信息"""
    try:
        node_info = await service.get_node_info(node_name)
        if not node_info:
            raise HTTPException(status_code=404, detail=f"Node {node_name} not found")
        return node_info
    except Exception as e:
        logger.error(f"Failed to get node info for {node_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status", response_model=SystemStatus)
async def get_system_status(
    service: RosbridgeService = Depends(get_rosbridge_service)
):
    """获取系统状态"""
    try:
        status = await service.get_system_status()
        return status
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
