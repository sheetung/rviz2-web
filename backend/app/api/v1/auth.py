"""基于服务端访问令牌换取 HttpOnly 会话 Cookie。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field

from ...core.config import get_settings
from ...core.security import (
    AUTH_COOKIE_NAME,
    create_session_cookie,
    origin_is_allowed,
    request_is_authenticated,
    valid_access_token,
)

router = APIRouter()


class LoginRequest(BaseModel):
    access_token: str = Field(min_length=1, max_length=4096)


class AuthStatus(BaseModel):
    required: bool
    authenticated: bool


@router.get("/auth/status", response_model=AuthStatus)
async def auth_status(request: Request) -> AuthStatus:
    settings = get_settings()
    return AuthStatus(
        required=bool(settings.api_access_token),
        authenticated=request_is_authenticated(
            request,
            settings,
            request.cookies.get(AUTH_COOKIE_NAME),
            request.headers.get("authorization"),
            request.headers.get("x-api-token"),
        ),
    )


@router.post("/auth/session", response_model=AuthStatus)
async def create_auth_session(
    payload: LoginRequest,
    request: Request,
    response: Response,
) -> AuthStatus:
    settings = get_settings()
    if not settings.api_access_token:
        raise HTTPException(status_code=409, detail="服务端未启用访问令牌")
    if not origin_is_allowed(request.headers.get("origin"), settings):
        raise HTTPException(status_code=403, detail="请求来源不在允许列表")
    if not valid_access_token(settings, payload.access_token):
        raise HTTPException(status_code=401, detail="访问令牌无效")

    response.set_cookie(
        AUTH_COOKIE_NAME,
        create_session_cookie(settings),
        max_age=settings.auth_session_ttl,
        httponly=True,
        secure=request.url.scheme == "https",
        samesite="strict",
        path="/",
    )
    return AuthStatus(required=True, authenticated=True)


@router.delete("/auth/session", response_model=AuthStatus)
async def delete_auth_session(response: Response) -> AuthStatus:
    response.delete_cookie(AUTH_COOKIE_NAME, path="/")
    return AuthStatus(required=True, authenticated=False)
