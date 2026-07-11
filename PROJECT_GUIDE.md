# RVizWeb 项目指南

## 项目定位

RVizWeb 是一个面向 ROS2 的浏览器可视化工具。前端使用 Vue 3、Three.js 和 Element Plus，后端使用 FastAPI 与 rclpy。浏览器通过 FastAPI 的 `/ws` WebSocket 与后端通信，后端直接加入 ROS2 图，不依赖独立的 rosbridge_server。

当前工程以本地开发运行方式为主。用户操作说明与界面功能介绍见 `README.md`，本文档重点说明工程结构、配置、启动和维护方式。

## 当前架构

```text
浏览器
  ├── HTTP /api/v1/*  ── FastAPI ── 配置文件与 ROS2 查询接口
  └── WebSocket /ws  ── RosbridgeService ── rclpy ── ROS2 图
```

- 前端：Vue 3、Vite、Three.js、Element Plus、Pinia。
- 后端：Python 3.10–3.12、FastAPI、Uvicorn、rclpy。
- Python 依赖：由 `backend/pyproject.toml`、`backend/uv.lock` 和 uv 管理。
- 前端依赖：由 `frontend/package.json`、`frontend/package-lock.json` 和 npm 管理。
- 可视化配置：保存在 `rvizweb_configs/*.rvizweb`。

## 环境要求

- ROS2 环境，当前启动脚本默认尝试加载 ROS2 Humble。
- Python 3.10–3.12。
- Node.js 18 或更高版本。
- npm、curl、`ss`、`setsid`。
- uv；如果系统中没有，`start.sh` 会通过 uv 官方安装脚本安装。

启动脚本会尝试加载：

```text
/opt/ros/humble/setup.bash
/home/amov/super_ros2_ws/install/setup.bash
```

如果实际工作空间位于其他位置，需要修改 `start.sh` 的 `load_ros` 函数，或在启动脚本前自行加载正确的 ROS2 环境。

## 环境配置

项目根目录的 `.env` 是当前设备的运行配置，`.env.example` 是参考模板。首次部署可复制模板后按实际网络环境调整。

主要变量：

| 变量 | 用途 |
| --- | --- |
| `ROS_DOMAIN_ID` | ROS2 DDS 通信域；未设置该变量的 ROS2 设备默认使用 `0` |
| `BACKEND_HOST` | FastAPI 绑定地址 |
| `BACKEND_PORT` | FastAPI HTTP 与 `/ws` WebSocket 共用端口 |
| `FRONTEND_PORT` | Vite 开发服务器端口 |
| `FRONTEND_PUBLIC_HOST` | 启动完成后显示的前端访问主机或局域网 IP |
| `CORS_ORIGINS` | 允许访问后端 API 的前端来源，使用英文逗号分隔 |
| `CONFIG_API_TOKEN` | 配置写接口的可选令牌 |
| `VITE_CONFIG_API_TOKEN` | 前端携带的配置令牌，应与 `CONFIG_API_TOKEN` 相同 |
| `CONFIG_MAX_BYTES` | 单个 `.rvizweb` 文件的最大字节数 |
| `CONFIG_NAME_MAX_LENGTH` | 配置文件名最大长度 |
| `VITE_DEBUG` | 是否输出前端调试日志 |

`ROSBRIDGE_PORT` 是历史遗留的预留变量。当前工程没有监听 `9090` 的独立 Rosbridge 服务，前端实际连接 `BACKEND_PORT` 上的 `/ws`。

ROS 话题名不应放在 `.env` 中。Displays、Fixed Frame、odom 话题、目标话题和样式等用户状态属于 `.rvizweb` 配置。

## 安装与启动

在项目根目录安装或同步依赖：

```bash
./start.sh sync
```

该命令会：

1. 创建带 `--system-site-packages` 的 `backend/.venv`，以便访问系统 ROS2 Python 包。
2. 使用 `uv sync --active` 同步后端依赖。
3. 使用 `npm ci` 安装前端锁定依赖。

启动前后端：

```bash
./start.sh local
```

不传参数时默认也是 `local`。脚本会读取 `.env`、加载 ROS2 环境、检查端口和依赖、启动两个进程并等待健康检查。日志写入：

```text
logs/backend.log
logs/frontend.log
```

默认加载 `rvizweb_configs/uav1.rvizweb`。临时指定其他配置：

```bash
RVIZWEB_CONFIG=default.rvizweb ./start.sh local
```

配置名必须以 `.rvizweb` 结尾且文件必须存在。按 `Ctrl+C` 后，脚本会清理前后端进程组。

`start.sh` 当前只支持 `sync`、`local` 和 `help`，不支持 `docker` 子命令。

## 访问入口

端口以 `.env` 为准。使用示例端口时：

- 前端：`http://localhost:3000/`
- 后端健康检查：`http://localhost:8000/health`
- OpenAPI 文档：`http://localhost:8000/docs`
- WebSocket：`ws://localhost:8000/ws`

Vite 会将 `/api` 和 `/ws` 请求代理到本地后端，因此日常使用通常只需访问前端地址。

注意：当前 `frontend/vite.config.js` 的代理目标仍固定为 `localhost:8000`。在代理配置改为读取环境变量之前，如果修改 `BACKEND_PORT`，还需要同步修改 Vite 代理目标，否则前端 API 与 WebSocket 请求无法到达后端。

## 核心功能与消息类型

当前 3D 场景主要处理：

- `sensor_msgs/msg/PointCloud2`
- `sensor_msgs/msg/LaserScan`
- `nav_msgs/msg/Odometry`
- `nav_msgs/msg/Path`
- `nav_msgs/msg/OccupancyGrid`
- `visualization_msgs/msg/Marker`
- `visualization_msgs/msg/MarkerArray`
- `geometry_msgs/msg/PoseWithCovarianceStamped`

后端消息桥还包含 Image、CompressedImage、CameraInfo、Twist、TF 等类型的转换或发布支持，但“后端能转换”不等同于“3D 场景对该类型有完整渲染器”。新增类型时应分别检查后端类型映射、WebSocket 序列化和前端渲染逻辑。

Fixed Frame 使用 `/tf` 和 `/tf_static`。当前以前端缓存的最新变换为主，尚未提供完整的按消息时间戳查询、历史缓存与插值语义。

## `.rvizweb` 配置

- `default.rvizweb`：通用界面配置，不应绑定特定机器人话题。
- `uav1.rvizweb`：当前无人机示例配置，也是启动脚本默认配置。
- `backups/`：覆盖或删除前保存的备份。

配置保存使用同目录临时文件和原子替换，并校验文件名、大小、版本及结构。主要状态包括 Fixed Frame、Displays、点云与 Path 样式、相机、网格、坐标轴、布局、目标点和 odom 话题。

配置 API：

```text
GET    /api/v1/configs
GET    /api/v1/configs/{name}
POST   /api/v1/configs/{name}
DELETE /api/v1/configs/{name}
```

## 后端接口

主要 ROS2 查询接口位于 `/api/v1`：

- `/topics`、`/topics/frequencies`、`/topic-info`
- `/topics/subscribe`、`/topics/unsubscribe`、`/topics/publish`
- `/nodes`、`/status`
- `/topology` 及节点/话题连接查询
- `/visualization/*` 可视化状态和插件接口

完整参数与响应模型应以运行时 `/docs` 为准。

## 目录结构

```text
RVIZ-RQT-VISUAL/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # configs、ros、viz API
│   │   ├── core/            # Pydantic 环境配置
│   │   ├── models/          # API 数据模型
│   │   ├── services/        # ROS2、WebSocket、拓扑服务
│   │   └── main.py          # FastAPI 入口
│   ├── pyproject.toml
│   └── uv.lock
├── frontend/
│   ├── src/
│   │   ├── components/RViz/ # 3D 场景与 Displays
│   │   ├── components/RQT/  # 节点图、话题、参数、服务等工具
│   │   ├── components/panels/
│   │   ├── composables/     # WebSocket 与连接状态
│   │   ├── services/        # HTTP API 封装
│   │   └── utils/           # TF、调试与通用工具
│   ├── package.json
│   └── vite.config.js
├── rvizweb_configs/
├── .env
├── .env.example
├── Dockerfile
└── start.sh
```

## 开发与验证

前端检查：

```bash
cd frontend
npm run lint:check
npm run build
```

后端基础检查：

```bash
cd backend
uv run python -m compileall -q app
```

当前 `backend/tests/` 只有 pytest 基础配置，没有可依赖的完整自动化测试套件。涉及 ROS2 订阅、TF、发布和配置写入的修改仍需在真实 ROS2 环境中做集成验证。

## Docker 状态

仓库保留了 `Dockerfile`，但当前 `start.sh` 不负责构建或运行容器，也没有 `docker-compose.yml`。Dockerfile 与本地 uv 工作流、当前配置语义和宿主机 ROS2/DDS 网络仍需单独验证，因此现阶段不要把 Docker 方式视为已验证的推荐启动路径。

## 常见问题

### 前端看不到远端话题

先在运行后端的终端确认：

```bash
ros2 topic list -t
echo "${ROS_DOMAIN_ID:-0}"
echo "${ROS_LOCALHOST_ONLY:-0}"
```

远端设备需要使用相同 Domain ID，且网络多播、防火墙和 DDS 配置允许互相发现。

### 后端找不到 rclpy

重新执行 `./start.sh sync`，并确认脚本加载了正确的 ROS2 安装和工作空间。虚拟环境必须使用 `--system-site-packages` 创建。

### 端口已被占用

修改 `.env` 中的 `FRONTEND_PORT` 时，同时更新 `CORS_ORIGINS` 中对应的前端来源。修改 `BACKEND_PORT` 时还必须同步修改 `frontend/vite.config.js` 中 `/api` 与 `/ws` 的代理目标；这是当前待统一的配置项。

### 配置未按预期恢复

检查 `logs/backend.log`、浏览器控制台以及配置文件中的 `version`、`fixedFrame`、`displays` 等字段。读取失败时前端会保留当前状态，不会用损坏配置覆盖界面。
