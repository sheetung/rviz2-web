from pathlib import Path
import json
import re
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()

PROJECT_ROOT = Path(__file__).resolve().parents[4]
CONFIG_DIR = PROJECT_ROOT / "rvizweb_configs"
CONFIG_SUFFIX = ".rvizweb"
SAFE_NAME = re.compile(r"^[A-Za-z0-9_.-]+$")


class ConfigPayload(BaseModel):
    name: str = Field(default="default.rvizweb")
    config: Dict[str, Any] = Field(default_factory=dict)


def _normalize_name(name: str) -> str:
    value = (name or "default.rvizweb").strip()
    if value.endswith(".rviz"):
        value = value[:-5]
    if not value.endswith(CONFIG_SUFFIX):
        value = f"{value}{CONFIG_SUFFIX}"
    if "/" in value or "\\" in value or not SAFE_NAME.match(value):
        raise HTTPException(status_code=400, detail="Invalid config name")
    return value


def _config_path(name: str) -> Path:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return CONFIG_DIR / _normalize_name(name)


@router.get("/configs", response_model=List[str])
async def list_configs() -> List[str]:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return sorted(path.name for path in CONFIG_DIR.glob(f"*{CONFIG_SUFFIX}") if path.is_file())


@router.get("/configs/{name}")
async def get_config(name: str) -> Dict[str, Any]:
    path = _config_path(name)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Config not found")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail=f"Invalid config file: {exc}") from exc


@router.post("/configs/{name}")
async def save_config(name: str, payload: ConfigPayload) -> Dict[str, str]:
    path = _config_path(name)
    data = {
        "name": _normalize_name(name),
        "version": 1,
        "config": payload.config,
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"name": path.name, "status": "saved"}


@router.delete("/configs/{name}")
async def delete_config(name: str) -> Dict[str, str]:
    path = _config_path(name)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Config not found")
    path.unlink()
    return {"name": path.name, "status": "deleted"}
