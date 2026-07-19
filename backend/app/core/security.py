"""HTTP、WebSocket 与 ROS 操作的统一安全边界。"""

from __future__ import annotations

import fnmatch
import hashlib
import hmac
import ipaddress
import re
import secrets
import time
from typing import Optional

from fastapi import Cookie, Header, HTTPException, Request, WebSocket

from .config import Settings, get_settings

AUTH_COOKIE_NAME = "rvizweb_session"
ROS_TOPIC_PATTERN = re.compile(r"^/[A-Za-z0-9_~-]+(?:/[A-Za-z0-9_~-]+)*$")
LAN_NETWORKS = tuple(
    ipaddress.ip_network(network)
    for network in (
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",
        "fc00::/7",
        "fe80::/10",
    )
)


def split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def client_ip(
    client_host: str,
    forwarded_for: Optional[str] = None,
) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
    """只信任由回环反向代理传入的 X-Forwarded-For。"""
    try:
        direct_ip = ipaddress.ip_address(client_host)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail="无法确认客户端地址") from exc

    if direct_ip.is_loopback and forwarded_for:
        # 只信任直接连接的本机反向代理追加的最右侧一跳。取最左侧会信任
        # 客户端自行伪造的 X-Forwarded-For，并可造成回环身份绕过。
        forwarded_host = forwarded_for.rsplit(",", 1)[-1].strip()
        try:
            return ipaddress.ip_address(forwarded_host)
        except ValueError as exc:
            raise HTTPException(status_code=403, detail="代理客户端地址无效") from exc
    return direct_ip


def _session_signature(settings: Settings, expires_at: int, nonce: str) -> str:
    payload = f"v1.{expires_at}.{nonce}".encode()
    return hmac.new(
        settings.api_access_token.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()


def create_session_cookie(settings: Settings) -> str:
    expires_at = int(time.time()) + settings.auth_session_ttl
    nonce = secrets.token_urlsafe(18)
    signature = _session_signature(settings, expires_at, nonce)
    return f"v1.{expires_at}.{nonce}.{signature}"


def valid_session_cookie(settings: Settings, cookie: str | None) -> bool:
    if not settings.api_access_token or not cookie:
        return False
    try:
        version, expires_raw, nonce, signature = cookie.split(".", 3)
        expires_at = int(expires_raw)
    except (TypeError, ValueError):
        return False
    if version != "v1" or expires_at < int(time.time()):
        return False
    expected = _session_signature(settings, expires_at, nonce)
    return hmac.compare_digest(signature, expected)


def valid_access_token(settings: Settings, candidate: str | None) -> bool:
    return bool(
        settings.api_access_token
        and candidate
        and hmac.compare_digest(candidate, settings.api_access_token)
    )


def _bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    return token.strip() if scheme.lower() == "bearer" else None


def client_is_allowed_without_token(
    settings: Settings,
    address: ipaddress.IPv4Address | ipaddress.IPv6Address,
) -> bool:
    if address.is_loopback:
        return True
    return settings.allow_unauthenticated_lan and any(
        address in network for network in LAN_NETWORKS
    )


def request_is_authenticated(
    request: Request,
    settings: Settings,
    session_cookie: str | None = None,
    authorization: str | None = None,
    api_token: str | None = None,
) -> bool:
    if valid_session_cookie(settings, session_cookie):
        return True
    if valid_access_token(settings, _bearer_token(authorization) or api_token):
        return True
    forwarded_for = request.headers.get("x-forwarded-for")
    client = request.client.host if request.client else ""
    return client_is_allowed_without_token(
        settings,
        client_ip(client, forwarded_for),
    )


async def require_api_access(
    request: Request,
    session_cookie: str | None = Cookie(default=None, alias=AUTH_COOKIE_NAME),
    authorization: str | None = Header(default=None),
    api_token: str | None = Header(default=None, alias="X-API-Token"),
) -> None:
    settings = get_settings()
    if not request_is_authenticated(
        request,
        settings,
        session_cookie,
        authorization,
        api_token,
    ):
        raise HTTPException(status_code=401, detail="需要有效的 RVizWeb 访问会话")


def origin_is_allowed(origin: str | None, settings: Settings) -> bool:
    if not origin:
        return True
    return origin in split_csv(settings.cors_origins)


def websocket_is_authenticated(websocket: WebSocket, settings: Settings) -> bool:
    if not origin_is_allowed(websocket.headers.get("origin"), settings):
        return False
    if valid_session_cookie(settings, websocket.cookies.get(AUTH_COOKIE_NAME)):
        return True
    if valid_access_token(
        settings,
        _bearer_token(websocket.headers.get("authorization")),
    ):
        return True
    forwarded_for = websocket.headers.get("x-forwarded-for")
    client = websocket.client.host if websocket.client else ""
    return client_is_allowed_without_token(
        settings,
        client_ip(client, forwarded_for),
    )


def ensure_ros_operation_allowed(
    settings: Settings,
    operation: str,
    topic: str,
    message_type: str | None = None,
) -> None:
    if not topic or len(topic) > 512 or not ROS_TOPIC_PATTERN.fullmatch(topic):
        raise ValueError("ROS topic 名称无效")

    if operation == "subscribe":
        allowed_topics = split_csv(settings.ros_subscribe_topic_allowlist)
    elif operation == "publish":
        allowed_topics = split_csv(settings.ros_publish_topic_allowlist)
    else:
        raise ValueError(f"未知 ROS 操作: {operation}")

    if not any(fnmatch.fnmatchcase(topic, pattern) for pattern in allowed_topics):
        raise PermissionError(f"不允许 {operation} ROS topic: {topic}")

    if operation == "publish":
        allowed_types = set(split_csv(settings.ros_publish_type_allowlist))
        if not message_type or message_type not in allowed_types:
            raise PermissionError(
                f"不允许发布 ROS 消息类型: {message_type or '<empty>'}"
            )
