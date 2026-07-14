"""
应用配置管理
"""

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from functools import lru_cache

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """应用配置"""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 后端服务配置
    backend_host: str = Field(default="0.0.0.0", description="后端服务主机")
    backend_port: int = Field(default=8000, description="后端服务端口")
    debug: bool = Field(default=False, description="调试模式")

    # ROS2 配置
    ros_domain_id: int = Field(default=0, description="ROS2 Domain ID")
    max_connections: int = Field(default=100, description="最大连接数")
    message_buffer_size: int = Field(default=10000, description="消息缓冲区大小")

    # 安全配置
    cors_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        description="允许访问 API 的前端来源",
    )
    config_api_token: str = Field(default="", description="配置写接口可选令牌")
    config_max_bytes: int = Field(default=1_048_576, ge=1024, le=10_485_760)
    config_name_max_length: int = Field(default=96, ge=8, le=200)

    # RTSP 视频转流配置
    rtsp_transport: Literal["tcp", "udp"] = Field(default="tcp")
    rtsp_frame_rate: int = Field(default=12, ge=1, le=30)
    rtsp_width: int = Field(default=640, ge=160, le=1920)
    rtsp_jpeg_quality: int = Field(default=5, ge=2, le=31)
    rtsp_startup_timeout: float = Field(default=10.0, ge=2.0, le=30.0)
    rtsp_session_ttl: int = Field(default=300, ge=30, le=3600)
    ffmpeg_path: str = Field(default="ffmpeg", description="FFmpeg 可执行文件路径")


@lru_cache()
def get_settings() -> Settings:
    """获取配置实例"""
    return Settings()
