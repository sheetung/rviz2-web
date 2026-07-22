from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional
from urllib.parse import urlsplit

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from ...core.config import get_settings

router = APIRouter()

PROJECT_ROOT = Path(__file__).resolve().parents[4]
CONFIG_DIR = PROJECT_ROOT / "rvizweb_configs"
BACKUP_DIR = CONFIG_DIR / "backups"
CONFIG_SUFFIX = ".rvizweb"
SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
_storage_lock = threading.Lock()


class StrictConfigModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Vector3Config(StrictConfigModel):
    x: float = 0
    y: float = 0
    z: float = 0


class CameraConfig(StrictConfigModel):
    position: Vector3Config
    target: Vector3Config
    up: Vector3Config = Field(default_factory=lambda: Vector3Config(z=1))
    zoom: float = Field(default=1, gt=0, le=100)
    projection: Literal["perspective", "orthographic"] = "perspective"


class SceneConfig(StrictConfigModel):
    showGrid: bool = True
    showAxes: bool = True
    viewPreset: Literal["iso", "top", "front", "side"] = "iso"
    camera: Optional[CameraConfig] = None


class DisplayConfig(StrictConfigModel):
    model_config = ConfigDict(extra="allow")

    name: str = Field(min_length=1, max_length=512)
    messageType: str = Field(min_length=1, max_length=256)
    visible: bool = True
    config: Dict[str, Any] = Field(default_factory=dict)


class LayoutConfig(StrictConfigModel):
    sceneWidth: float = Field(default=68, ge=20, le=90)
    panelHeights: Dict[str, float] = Field(default_factory=dict)
    collapsedPanels: Dict[str, bool] = Field(default_factory=dict)


class AppearanceConfig(StrictConfigModel):
    theme: Literal["dark", "light"] = "dark"


class VideoLayoutConfig(StrictConfigModel):
    x: Optional[float] = None
    y: Optional[float] = None
    width: float = Field(default=360, ge=160, le=4096)
    height: float = Field(default=240, ge=160, le=2160)


class VideoConfig(StrictConfigModel):
    sourceUrl: str = Field(default="", max_length=2048)
    visible: bool = False
    layout: VideoLayoutConfig = Field(default_factory=VideoLayoutConfig)

    @field_validator("sourceUrl")
    @classmethod
    def reject_persisted_credentials(cls, value: str) -> str:
        source_url = value.strip()
        if not source_url:
            return ""
        parsed = urlsplit(source_url)
        if (
            parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("配置文件不能保存 RTSP 凭据或查询令牌，请在连接时输入")
        return source_url


class PositionConfig(StrictConfigModel):
    odomTopic: str = Field(default="", max_length=512)
    showRobotModel: bool = False
    showTrajectory: bool = True
    trajectoryLength: int = Field(default=100, ge=10, le=100)


class GoalConfig(StrictConfigModel):
    topic: str = Field(default="", max_length=512)
    x: float = 0
    y: float = 0
    z: float = 0


class LaserConfig(StrictConfigModel):
    laserType: Literal["2d", "3d"] = "3d"
    laserScanTopic: str = Field(default="", max_length=512)
    pointCloudTopic: str = Field(default="", max_length=512)
    showLaserPoints: bool = True
    showLaserLines: bool = True
    showIntensity: bool = False
    laserPointSize: float = Field(default=0.15, gt=0, le=10)
    pointSize: float = Field(default=0.03, gt=0, le=10)
    pointOpacity: float = Field(default=0.8, ge=0, le=1)


class MapConfig(StrictConfigModel):
    mapTopic: str = Field(default="", max_length=512)
    showMap: bool = True
    showMapGrid: bool = False
    showMapOrigin: bool = True
    mapOpacity: float = Field(default=0.8, ge=0, le=1)


class FrontendConfig(StrictConfigModel):

    fixedFrame: str = Field(default="map", min_length=1, max_length=256)
    followFrame: str = Field(default="", max_length=256)
    scene: SceneConfig = Field(default_factory=SceneConfig)
    displays: List[DisplayConfig] = Field(default_factory=list, max_length=256)
    layout: LayoutConfig = Field(default_factory=LayoutConfig)
    appearance: AppearanceConfig = Field(default_factory=AppearanceConfig)
    video: VideoConfig = Field(default_factory=VideoConfig)
    goal: GoalConfig = Field(default_factory=GoalConfig)
    position: PositionConfig = Field(default_factory=PositionConfig)
    laser: LaserConfig = Field(default_factory=LaserConfig)
    map: MapConfig = Field(default_factory=MapConfig)
    extensions: Dict[str, Any] = Field(default_factory=dict)


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
        raise HTTPException(
            status_code=400, detail="配置文件名只能包含字母、数字、点、横线和下划线"
        )
    return value


def _config_path(name: str) -> Path:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    path = CONFIG_DIR / _normalize_name(name)
    if path.parent.resolve() != CONFIG_DIR.resolve():
        raise HTTPException(status_code=400, detail="配置文件路径越界")
    if path.is_symlink():
        raise HTTPException(status_code=400, detail="配置文件不能是符号链接")
    return path


def _read_validated(path: Path) -> StoredConfig:
    settings = get_settings()
    try:
        if path.stat().st_size > settings.config_max_bytes:
            raise HTTPException(status_code=413, detail="配置文件超过大小限制")
        content = path.read_text(encoding="utf-8")
    except HTTPException:
        raise
    except OSError as exc:
        raise HTTPException(status_code=404, detail="配置文件不存在") from exc
    try:
        return StoredConfig.model_validate_json(content)
    except (ValidationError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=422,
            detail=f"配置文件格式无效: {exc}",
        ) from exc


def _modified_at(path: Path) -> datetime:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)


def _prune_backups() -> None:
    settings = get_settings()
    if not BACKUP_DIR.exists():
        return

    backups = sorted(
        (
            path
            for path in BACKUP_DIR.glob(f"*{CONFIG_SUFFIX}.bak")
            if path.is_file() and not path.is_symlink()
        ),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    retained_bytes = 0
    for index, path in enumerate(backups):
        size = path.stat().st_size
        exceeds_count = index >= settings.config_backup_max_files
        exceeds_bytes = retained_bytes + size > settings.config_backup_max_bytes
        if exceeds_count or exceeds_bytes:
            path.unlink(missing_ok=True)
        else:
            retained_bytes += size


def _create_backup(path: Path) -> None:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup_path = BACKUP_DIR / f"{path.stem}.{stamp}{CONFIG_SUFFIX}.bak"
    shutil.copy2(path, backup_path)
    _prune_backups()


@router.get("/configs", response_model=List[str])
async def list_configs() -> List[str]:
    with _storage_lock:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        return sorted(
            path.name
            for path in CONFIG_DIR.glob(f"*{CONFIG_SUFFIX}")
            if path.is_file() and not path.is_symlink()
        )


@router.get("/configs/{name}", response_model=ConfigResponse)
async def get_config(name: str) -> ConfigResponse:
    with _storage_lock:
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
    response_model=ConfigSaveResult,
)
async def save_config(name: str, payload: ConfigPayload) -> ConfigSaveResult:
    with _storage_lock:
        path = _config_path(name)
        document = StoredConfig(name=path.name, version=1, config=payload.config)
        encoded = document.model_dump_json(indent=2).encode("utf-8")
        if len(encoded) > get_settings().config_max_bytes:
            raise HTTPException(status_code=413, detail="配置内容超过大小限制")

        if path.exists():
            _create_backup(path)

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
)
async def delete_config(name: str) -> Dict[str, str]:
    with _storage_lock:
        path = _config_path(name)
        if not path.exists():
            raise HTTPException(status_code=404, detail="配置文件不存在")
        _create_backup(path)
        path.unlink()
        return {"name": path.name, "status": "deleted"}
