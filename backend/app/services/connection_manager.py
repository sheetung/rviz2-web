"""
WebSocket 连接管理器
管理客户端连接、消息路由和广播
"""

import asyncio
import contextlib
import json
import logging
import math
from datetime import datetime
from typing import Dict

from fastapi import WebSocket

from ..models.ros import ConnectionInfo

logger = logging.getLogger(__name__)


def _replace_non_finite_numbers(value):
    """将 JSON 不支持的 NaN/Infinity 递归替换为 null。"""
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {
            key: _replace_non_finite_numbers(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_replace_non_finite_numbers(item) for item in value]
    return value


def _serialize_json_message(message: dict) -> str:
    """生成浏览器可严格解析的 JSON，并避免正常消息的额外遍历。"""
    try:
        return json.dumps(message, allow_nan=False)
    except ValueError:
        return json.dumps(
            _replace_non_finite_numbers(message),
            allow_nan=False,
        )


class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(
        self,
        max_connections: int = 100,
        outbound_queue_size: int = 8,
        send_timeout: float = 2.0,
        max_outbound_message_bytes: int = 16_777_216,
    ):
        self.max_connections = max_connections
        self.outbound_queue_size = outbound_queue_size
        self.send_timeout = send_timeout
        self.max_outbound_message_bytes = max_outbound_message_bytes
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_info: Dict[str, ConnectionInfo] = {}
        self._send_queues: Dict[str, asyncio.Queue[str]] = {}
        self._sender_tasks: Dict[str, asyncio.Task] = {}
        self._connection_lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, client_id: str) -> bool:
        """连接客户端"""
        async with self._connection_lock:
            if len(self.active_connections) >= self.max_connections:
                await websocket.close(code=1008, reason="Max connections reached")
                return False

            await websocket.accept()
            self.active_connections[client_id] = websocket
            self.connection_info[client_id] = ConnectionInfo(
                client_id=client_id,
                connected_at=datetime.now(),
                subscribed_topics=[],
                message_count=0,
            )
            self._send_queues[client_id] = asyncio.Queue(
                maxsize=self.outbound_queue_size
            )
            self._sender_tasks[client_id] = asyncio.create_task(
                self._sender_loop(client_id),
                name=f"websocket-sender-{client_id}",
            )
        logger.info(f"Client {client_id} connected")
        return True

    def disconnect(self, client_id: str):
        """断开客户端"""
        self.active_connections.pop(client_id, None)
        self.connection_info.pop(client_id, None)
        self._send_queues.pop(client_id, None)
        task = self._sender_tasks.pop(client_id, None)
        if task and task is not asyncio.current_task():
            task.cancel()
        logger.info(f"Client {client_id} disconnected")

    async def _sender_loop(self, client_id: str) -> None:
        try:
            while True:
                queue = self._send_queues.get(client_id)
                websocket = self.active_connections.get(client_id)
                if queue is None or websocket is None:
                    return
                message_text = await queue.get()
                try:
                    await asyncio.wait_for(
                        websocket.send_text(message_text),
                        timeout=self.send_timeout,
                    )
                    info = self.connection_info.get(client_id)
                    if info:
                        info.message_count += 1
                finally:
                    queue.task_done()
        except asyncio.CancelledError:
            raise
        except Exception as error:
            logger.error("Failed to send message to %s: %s", client_id, error)
            # 保留 connection_info，交给 RosbridgeService 的 finally 释放
            # 该客户端持有的 ROS 订阅和发布者。
            await self._close_client_socket(
                client_id,
                code=1011,
                reason="WebSocket send failed",
            )

    async def _close_client_socket(
        self,
        client_id: str,
        *,
        code: int,
        reason: str,
    ) -> None:
        websocket = self.active_connections.get(client_id)
        if websocket is None:
            return
        sender_task = self._sender_tasks.get(client_id)
        if (
            sender_task
            and sender_task is not asyncio.current_task()
            and not sender_task.done()
        ):
            sender_task.cancel()
            await asyncio.gather(sender_task, return_exceptions=True)
        with contextlib.suppress(Exception, asyncio.TimeoutError):
            await asyncio.wait_for(
                websocket.close(code=code, reason=reason),
                timeout=max(self.send_timeout, 0.1),
            )

    async def send_to_client(self, client_id: str, message: dict) -> bool:
        """发送消息给指定客户端"""
        queue = self._send_queues.get(client_id)
        if queue is None:
            return False
        message_text = _serialize_json_message(message)
        if len(message_text.encode("utf-8")) > self.max_outbound_message_bytes:
            logger.warning("Dropping oversized outbound WebSocket response")
            return False
        try:
            await asyncio.wait_for(
                queue.put(message_text),
                timeout=self.send_timeout,
            )
            return True
        except asyncio.TimeoutError:
            logger.warning("Closing slow WebSocket client %s", client_id)
            # 关闭后 receive_text 会退出，再由上层 finally 按正确顺序清理
            # ROS 资源并删除连接元数据。
            await self._close_client_socket(
                client_id,
                code=1011,
                reason="Outbound queue timeout",
            )
            return False

    async def broadcast(self, message: dict):
        """广播消息给所有客户端"""
        if not self.active_connections:
            logger.debug("📭 No active connections for broadcast")
            return False

        message_text = await asyncio.to_thread(_serialize_json_message, message)
        if len(message_text.encode("utf-8")) > self.max_outbound_message_bytes:
            logger.warning("Dropping oversized outbound WebSocket broadcast")
            return False
        sent_count = 0

        # 如果是主题消息，只发送给订阅了该主题的客户端
        if message.get("op") == "publish" and "topic" in message:
            topic = message["topic"]
            recipients = [
                client_id
                for client_id, info in list(self.connection_info.items())
                if topic in info.subscribed_topics
            ]
            for client_id in recipients:
                queue = self._send_queues.get(client_id)
                if queue is None:
                    continue
                try:
                    queue.put_nowait(message_text)
                    sent_count += 1
                except asyncio.QueueFull:
                    logger.debug(
                        "Dropping topic update for slow client %s (%s)",
                        client_id,
                        topic,
                    )
        else:
            # 非主题消息广播给所有客户端
            results = await asyncio.gather(
                *(
                    self.send_to_client(client_id, message)
                    for client_id in list(self.active_connections)
                ),
                return_exceptions=True,
            )
            sent_count = sum(result is True for result in results)

        logger.debug("Broadcast queued for %s clients", sent_count)
        return sent_count > 0

    async def close_all(self) -> None:
        await asyncio.gather(
            *(
                self._close_client_socket(
                    client_id,
                    code=1001,
                    reason="Server shutting down",
                )
                for client_id in list(self.active_connections)
            ),
            return_exceptions=True,
        )
        tasks = list(self._sender_tasks.values())
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        self._sender_tasks.clear()
        self._send_queues.clear()
        self.active_connections.clear()
        self.connection_info.clear()
