from __future__ import annotations

import ipaddress
import json
import os
import re
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from ...core.config import get_settings

router = APIRouter()

PROJECT_ROOT = Path(__file__).resolve().parents[4]
CONFIG_DIR = PROJECT_ROOT / "rvizweb_configs"
BACKUP_DIR = CONFIG_DIR / "backups"
CONFIG_SUFFIX = ".rvizweb"
SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")


class DisplayConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str = Field(min_length=1, max_length=512)
    messageType: str = Field(min_length=1, max_length=256)
    visible: bool = True
    config: Dict[str, Any] = Field(default_factory=dict)


class LayoutConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    sceneWidth: float = Field(default=68, ge=20, le=90)
    panelHeights: Dict[str, float] = Field(default_factory=dict)
    collapsedPanels: Dict[str, bool] = Field(default_factory=dict)


class AppearanceConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    theme: Literal["dark", "light"] = "dark"


class VideoLayoutConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    x: Optional[float] = None
    y: Optional[float] = None
    width: float = Field(default=360, ge=160, le=4096)
    height: float = Field(default=240, ge=160, le=2160)


class VideoConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    sourceUrl: str = Field(default="", max_length=2048)
    visible: bool = False
    layout: VideoLayoutConfig = Field(default_factory=VideoLayoutConfig)


class PositionConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    odomTopic: str = Field(default="", max_length=512)
    showRobotModel: bool = False
    showTrajectory: bool = True
    trajectoryLength: int = Field(default=100, ge=10, le=100)


class FrontendConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    fixedFrame: str = Field(default="map", min_length=1, max_length=256)
    followFrame: str = Field(default="", max_length=256)
    displays: List[DisplayConfig] = Field(default_factory=list, max_length=256)
    layout: LayoutConfig = Field(default_factory=LayoutConfig)
    appearance: AppearanceConfig = Field(default_factory=AppearanceConfig)
    video: VideoConfig = Field(default_factory=VideoConfig)
    position: PositionConfig = Field(default_factory=PositionConfig)


class ConfigPayload(BaseModel):
    name: str = Field(default="default.rvizweb")
    config: FrontendConfig


class StoredConfig(BaseModel):
    name: str
    version: Literal[1]
    config: FrontendConfig


class ConfigResponse(StoredConfig):
    modified_at: datetime


class ConfigSaveResult(BaseModel):
    name: str
    status: Literal["saved"]
    modified_at: datetime


def _normalize_name(name: str) -> str:
    settings = get_settings()
    value = (name or "default.rvizweb").strip()
    if value.endswith(".rviz"):
        value = value[:-5]
    if not value.endswith(CONFIG_SUFFIX):
        value = f"{value}{CONFIG_SUFFIX}"
    if len(value) > settings.config_name_max_length:
        raise HTTPException(status_code=400, detail="配置文件名过长")
    if not SAFE_NAME.fullmatch(value):
        raise HTTPException(status_code=400, detail="配置文件名只能包含字母、数字、点、横线和下划线")
    return value


def _config_path(name: str) -> Path:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    path = CONFIG_DIR / _normalize_name(name)
    if path.parent.resolve() != CONFIG_DIR.resolve():
        raise HTTPException(status_code=400, detail="配置文件路径越界")
    if path.is_symlink():
        raise HTTPException(status_code=400, detail="配置文件不能是符号链接")
    return path


def _require_config_write_access(
    request: Request,
    config_token: str | None = Header(default=None, alias="X-Config-Token"),
) -> None:
    settings = get_settings()
    client_host = request.client.host if request.client else ""
    try:
        client_ip = ipaddress.ip_address(client_host)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail="无法确认客户端地址") from exc
    if not (client_ip.is_loopback or client_ip.is_private):
        raise HTTPException(status_code=403, detail="配置写入仅允许本机或局域网客户端")
    if settings.config_api_token and config_token != settings.config_api_token:
        raise HTTPException(status_code=401, detail="配置写入令牌无效")


def _read_validated(path: Path) -> StoredConfig:
    settings = get_settings()
    if path.stat().st_size > settings.config_max_bytes:
        raise HTTPException(status_code=413, detail="配置文件超过大小限制")
    try:
        return StoredConfig.model_validate_json(
            path.read_text(encoding="utf-8")
        )
    except (OSError, ValidationError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=422,
            detail=f"配置文件格式无效: {exc}",
        ) from exc


def _modified_at(path: Path) -> datetime:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)


@router.get("/configs", response_model=List[str])
async def list_configs() -> List[str]:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return sorted(
        path.name
        for path in CONFIG_DIR.glob(f"*{CONFIG_SUFFIX}")
        if path.is_file() and not path.is_symlink()
    )


@router.get("/configs/{name}", response_model=ConfigResponse)
async def get_config(name: str) -> ConfigResponse:
    path = _config_path(name)
    if not path.exists():
        raise HTTPException(status_code=404, detail="配置文件不存在")
    stored = _read_validated(path)
    return ConfigResponse(
        **stored.model_dump(),
        modified_at=_modified_at(path),
    )


@router.post(
    "/configs/{name}",
    dependencies=[Depends(_require_config_write_access)],
    response_model=ConfigSaveResult,
)
async def save_config(name: str, payload: ConfigPayload) -> ConfigSaveResult:
    path = _config_path(name)
    document = StoredConfig(name=path.name, version=1, config=payload.config)
    encoded = document.model_dump_json(indent=2).encode("utf-8")
    if len(encoded) > get_settings().config_max_bytes:
        raise HTTPException(status_code=413, detail="配置内容超过大小限制")

    if path.exists():
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        backup_path = BACKUP_DIR / f"{path.stem}.{stamp}{CONFIG_SUFFIX}.bak"
        shutil.copy2(path, backup_path)

    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=CONFIG_DIR,
            prefix=f".{path.name}.",
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    except OSError as exc:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"保存配置失败: {exc}") from exc
    return ConfigSaveResult(
        name=path.name,
        status="saved",
        modified_at=_modified_at(path),
    )


@router.delete(
    "/configs/{name}",
    dependencies=[Depends(_require_config_write_access)],
)
async def delete_config(name: str) -> Dict[str, str]:
    path = _config_path(name)
    if not path.exists():
        raise HTTPException(status_code=404, detail="配置文件不存在")
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    shutil.copy2(path, BACKUP_DIR / f"{path.stem}.{stamp}{CONFIG_SUFFIX}.bak")
    path.unlink()
    return {"name": path.name, "status": "deleted"}
