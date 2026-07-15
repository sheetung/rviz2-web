"""
WebSocket 连接管理器
管理客户端连接、消息路由和广播
"""

import json
import logging
from datetime import datetime
from typing import Dict

from fastapi import WebSocket

from ..models.ros import ConnectionInfo

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self, max_connections: int = 100):
        self.max_connections = max_connections
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_info: Dict[str, ConnectionInfo] = {}

    async def connect(self, websocket: WebSocket, client_id: str) -> bool:
        """连接客户端"""
        if len(self.active_connections) >= self.max_connections:
            await websocket.close(code=1008, reason="Max connections reached")
            return False

        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.connection_info[client_id] = ConnectionInfo(
            client_id=client_id,
            connected_at=datetime.now(),
            subscribed_topics=[],
            message_count=0
        )
        logger.info(f"Client {client_id} connected")
        return True

    def disconnect(self, client_id: str):
        """断开客户端"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.connection_info:
            del self.connection_info[client_id]
        logger.info(f"Client {client_id} disconnected")

    async def send_to_client(self, client_id: str, message: dict):
        """发送消息给指定客户端"""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(json.dumps(message))
                self.connection_info[client_id].message_count += 1
            except Exception as e:
                logger.error(f"Failed to send message to {client_id}: {e}")
                self.disconnect(client_id)

    async def broadcast(self, message: dict):
        """广播消息给所有客户端"""
        if not self.active_connections:
            logger.debug("📭 No active connections for broadcast")
            return False

        message_text = json.dumps(message)
        disconnected_clients = []
        sent_count = 0

        # 如果是主题消息，只发送给订阅了该主题的客户端
        if message.get('op') == 'publish' and 'topic' in message:
            topic = message['topic']
            for client_id, websocket in self.active_connections.items():
                if client_id in self.connection_info:
                    client_info = self.connection_info[client_id]
                    if topic in client_info.subscribed_topics:
                        try:
                            await websocket.send_text(message_text)
                            client_info.message_count += 1
                            sent_count += 1
                            logger.debug(f"📤 Sent message to {client_id} for topic {topic}")
                        except Exception as e:
                            logger.error(f"Failed to send to {client_id}: {e}")
                            disconnected_clients.append(client_id)
        else:
            # 非主题消息广播给所有客户端
            for client_id, websocket in self.active_connections.items():
                try:
                    await websocket.send_text(message_text)
                    self.connection_info[client_id].message_count += 1
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Failed to broadcast to {client_id}: {e}")
                    disconnected_clients.append(client_id)

        # 清理断开的连接
        for client_id in disconnected_clients:
            self.disconnect(client_id)

        logger.debug(f"📊 Broadcast sent to {sent_count} clients, {len(disconnected_clients)} disconnected")
        return sent_count > 0
