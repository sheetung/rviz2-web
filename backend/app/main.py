"""
FastAPI 应用入口
支持 RViz2 Web 可视化系统
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

from .core.config import get_settings
from .core.version import APP_VERSION
from .api.v1 import ros, configs
from .services.dependencies import get_rosbridge_service

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 获取配置
settings = get_settings()

# 创建 FastAPI 应用
app = FastAPI(
    title="RViz2 Web Visualization",
    description="基于 Vue.js + FastAPI 的 ROS2 可视化平台",
    version=APP_VERSION
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局 Rosbridge 服务实例将通过依赖注入管理

# 注册 API 路由
app.include_router(ros.router, prefix="/api/v1", tags=["ROS"])
app.include_router(configs.router, prefix="/api/v1", tags=["Configs"])

# 静态文件服务 (用于单一容器部署)
if os.path.exists("./static"):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")

@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("Starting RViz2 Web Visualization System")
    
    # 初始化 Rosbridge 服务
    service = get_rosbridge_service()
    await service.start()
    
    logger.info(f"Server started on port {settings.backend_port}")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("Shutting down RViz2 Web Visualization System")
    
    # 清理 Rosbridge 服务
    service = get_rosbridge_service()
    await service.stop()

@app.get("/")
async def root():
    """根路径"""
    return {"message": "RViz2 Web Visualization System", "version": APP_VERSION}

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "ros-web-viz",
        "version": APP_VERSION,
    }


@app.get("/api/v1/version")
async def version_info():
    """返回工程、API 与配置格式版本。"""
    return {
        "version": APP_VERSION,
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 端点 - Rosbridge 协议"""
    service = get_rosbridge_service()
    await service.handle_websocket(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=settings.debug
    )
