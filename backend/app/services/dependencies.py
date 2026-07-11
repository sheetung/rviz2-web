"""
依赖注入服务
管理应用中的全局服务实例，避免循环导入
"""

from .rosbridge import RosbridgeService
from ..core.config import get_settings

# 全局 Rosbridge 服务实例
_rosbridge_service = None

def get_rosbridge_service() -> RosbridgeService:
    """获取 Rosbridge 服务实例"""
    global _rosbridge_service
    if _rosbridge_service is None:
        settings = get_settings()
        _rosbridge_service = RosbridgeService(settings)
    return _rosbridge_service
