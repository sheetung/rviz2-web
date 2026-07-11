# RVizWeb 项目状态

更新时间：2026-07-11

## 总体结论

当前工程可作为 ROS2 本地网络中的浏览器可视化与调试工具使用。核心链路已经形成：FastAPI/rclpy 后端加入 ROS2 图，浏览器通过 `/ws` 收发消息，Three.js 场景按 `.rvizweb` 配置展示数据。

当前最可靠的运行方式是 `./start.sh sync` 后执行 `./start.sh local`。Dockerfile 尚未按当前工程完整验证；自动化测试覆盖也不足，因此不再使用“100% 完成”或未经验证的完成度百分比描述项目状态。

## 已实现并在当前代码中保留的能力

### 启动与配置

- `start.sh` 支持 `sync`、`local`、`help`。
- 缺少 uv 时可通过官方安装脚本自动安装。
- 后端使用 uv 锁定依赖，前端使用 `npm ci`。
- 启动时读取 `.env`，端口使用 `BACKEND_PORT` 与 `FRONTEND_PORT`。
- 支持通过 `RVIZWEB_CONFIG` 选择启动配置，默认使用 `uav1.rvizweb`。
- 前后端健康检查、日志归档和退出时进程清理已集成到启动脚本。

### ROS2 与通信

- 后端使用 rclpy 直接访问 ROS2 图。
- FastAPI `/ws` 提供浏览器实时通信入口。
- 支持话题发现、订阅、取消订阅和发布。
- 提供节点、话题频率、系统状态和拓扑查询 API。
- 支持 `/tf`、`/tf_static` 与 Fixed Frame 转换的前端链路。

### 3D 可视化

- PointCloud2 点云。
- LaserScan 激光数据。
- Odometry 位姿与轨迹。
- Path 路径。
- Marker 与 MarkerArray。
- OccupancyGrid 地图。
- PoseWithCovarianceStamped 位姿显示。
- 网格、坐标轴、视角预设、相机状态及布局保存。
- Displays 可从当前 ROS2 图选择话题，并保存每项显示配置。

### 目标与配置文件

- 支持目标点预览和 `PoseStamped` 发布。
- `.rvizweb` 可保存、读取和删除。
- 配置写入包含名称、大小、版本和结构校验。
- 覆盖与删除前创建备份，写入使用原子替换。
- 配置写接口支持可选令牌。

### RQT 风格工具

代码中包含话题监视、节点/话题拓扑图、参数编辑、服务调用、系统信息、日志和图表面板。各工具对不同 ROS2 发行版、自定义消息和大型系统的兼容程度仍需要持续实机验证。

## 当前限制与已知偏差

### 自动化测试仍需扩展

`backend/tests/` 已覆盖配置原子保存、备份、写入权限、路径安全和启动脚本基础行为。前端仍没有单元测试或端到端测试脚本，ROS2 实时链路也缺少自动化集成测试。现有验证主要依靠：

- `uv run pytest -q`
- `npm run lint:check`
- `npm run build`
- `uv run python -m compileall -q app`
- 真实 ROS2 环境中的人工集成测试

因此当前测试可以防止配置存储与启动脚本的基础回归，但不能视为完整 API、前端或 ROS2 覆盖。

### Docker 尚非推荐路径

- `start.sh` 没有 `docker` 子命令。
- 仓库没有 `docker-compose.yml`。
- Dockerfile 保留了旧式单容器启动结构，尚需验证前端产物、后端依赖、环境变量和 DDS 网络。
- `9090` 目前没有独立服务监听；浏览器使用后端端口上的 `/ws`。

### 环境配置仍有历史项

- `ROSBRIDGE_PORT` 当前只作为预留变量存在，没有实际监听者。
- 后端 `Settings` 中仍保留部分旧的 `web_*`、rosbridge 和容量配置字段；启动入口实际以 `start.sh` 传给 Uvicorn 的 `BACKEND_HOST/BACKEND_PORT` 为准。
- `frontend/vite.config.js` 的 `/api`、`/ws` 代理仍固定指向 `localhost:8000`，尚未跟随 `BACKEND_PORT`。
- `LOG_LEVEL` 的端到端配置行为需要进一步统一验证。

### ROS2 环境路径与发行版固定

`start.sh` 当前写死尝试加载 ROS2 Humble 和 `/home/amov/super_ros2_ws`。在其他用户、工作空间或 ROS2 发行版上，需要调整脚本或预先加载环境。

### TF 时间语义有限

当前 Fixed Frame 主要使用前端维护的最新 TF 数据。尚未实现 RViz 等价的按消息时间戳查找、完整历史缓存与插值；高速运动或延迟消息场景可能出现瞬时缺链或位置偏差。

### 前端历史组件较多

工程中同时保留多套布局组件、示例话题常量和部分旧 RViz/RQT 组件。当前主界面并不一定使用所有文件。后续清理前需要通过入口与组件引用关系确认，不能仅按文件名删除。

## 当前验证基线

每次合入核心修改前至少应执行：

```bash
bash -n start.sh

cd frontend
npm run lint:check
npm run build

cd ../backend
uv run pytest -q
uv run python -m compileall -q app
```

涉及 ROS2 的修改还应验证：

1. `ros2 topic list -t` 能发现目标话题。
2. 前端 Displays 能刷新并订阅话题。
3. PointCloud2、Odometry、Path、Marker 和 TF 链路按修改范围正常显示。
4. WebSocket 断开后能恢复连接与订阅。
5. 配置保存、覆盖备份、读取和删除符合预期。
6. `Ctrl+C` 后前后端进程均退出。

## 优先级建议

### P0：配置与启动一致性

- 删除或正式实现 `ROSBRIDGE_PORT`，避免让用户误以为需要开放 `9090`。
- 将后端 `Settings` 的 `web_host/web_port` 与 `.env` 的 `BACKEND_HOST/BACKEND_PORT` 统一。
- 让 ROS2 安装路径和工作空间路径可配置，避免绑定单台设备。
- 明确 `LOG_LEVEL`、`DEBUG`、`FRONTEND_HOST` 的实际读取链路。

### P1：测试与稳定性

- 为 `.rvizweb` 校验、原子保存、备份和令牌权限补充后端测试。
- 为 TF 链查找、缺失 TF 状态和 Display 生命周期补充前端测试。
- 增加 WebSocket 发布/订阅和重连的集成测试。
- 在真实 ROS2 图中覆盖自定义消息、QoS 不匹配和高频点云。

### P2：TF 与性能

- 增加按 ROS 消息时间戳的 TF 历史缓存和插值。
- 对大点云进行采样、限频、内存复用或 LOD 优化。
- 评估 WebSocket 二进制传输或压缩，减少大消息的 JSON 开销。
- 持续控制前端生产包体积并评估 Element Plus 按需引入。

### P3：部署与清理

- 决定是否正式维护 Docker；若维护，应重写并验证容器启动、健康检查和 DDS 网络说明。
- 清理未引用的布局、示例话题和旧组件。
- 将用户指南、开发指南和状态报告中的重复内容继续收敛。

## 状态判定

- 本地启动链路：可用，依赖固定 ROS2 路径。
- ROS2 发现与 WebSocket 桥接：可用，需要网络与 DDS 环境正确。
- 核心 3D 显示：可用，TF 时间语义仍有限。
- `.rvizweb` 配置管理：已实现，自动化回归测试不足。
- RQT 风格工具：已实现多项功能，需按具体工具实机验证。
- Docker 部署：保留实现，当前未验证。
- 自动化测试：配置与启动脚本已有基础覆盖，前端、TF 与 ROS2 集成覆盖仍不足。
