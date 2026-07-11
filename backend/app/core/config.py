"""
应用配置管理
"""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings

from functools import lru_cache

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """应用配置"""
    
    # Web 服务配置
    web_host: str = Field(default="0.0.0.0", description="Web 服务主机")
    web_port: int = Field(default=8000, description="Web 服务端口")
    debug: bool = Field(default=False, description="调试模式")
    
    # ROS2 配置
    ros_domain_id: int = Field(default=0, description="ROS2 Domain ID")
    ros_discovery_server: str = Field(default="", description="ROS2 Discovery Server")
    
    # Rosbridge 配置
    rosbridge_host: str = Field(default="0.0.0.0", description="Rosbridge 主机")
    rosbridge_port: int = Field(default=9090, description="Rosbridge 端口")
    max_connections: int = Field(default=100, description="最大连接数")
    message_buffer_size: int = Field(default=10000, description="消息缓冲区大小")
    
    # 安全配置
    secret_key: str = Field(default="ros-web-viz-secret-key", description="JWT 密钥")
    cors_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        description="允许访问 API 的前端来源",
    )
    config_api_token: str = Field(default="", description="配置写接口可选令牌")
    config_max_bytes: int = Field(default=1_048_576, ge=1024, le=10_485_760)
    config_name_max_length: int = Field(default=96, ge=8, le=200)

    class Config:
        env_file = PROJECT_ROOT / ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    """获取配置实例"""
    return Settings()
