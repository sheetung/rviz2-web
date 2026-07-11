# RVizWeb

![RVizWeb](img/1.png)

RVizWeb 是一个面向 ROS2 的浏览器可视化前端，用于查看点云、里程计、路径、Marker、地图等数据，并提供无人机位姿显示、期望目标输入和 RViz 风格的 Displays 管理。项目由 Vue 3 + Three.js 前端和 FastAPI + rclpy 后端组成。

当前版本以配置文件驱动前端状态：话题、Fixed Frame、Displays、点云大小、Path 样式、视角、网格/坐标轴、目标点和面板比例都可以保存到 `rvizweb_configs/*.rvizweb`。`.env` 只保存端口、日志级别、`ROS_DOMAIN_ID` 等运行环境配置，不保存 ROS 话题名，前端代码也不提供内置话题兜底。

## 功能

- RViz 风格 Displays：
  - 从当前 ROS2 图读取话题并添加显示项。
  - 用眼睛图标控制显示/隐藏。
  - 支持添加、删除、修改话题和消息类型。
  - 每个 Display 可保存独立配置。
- 3D 可视化：
  - `sensor_msgs/msg/PointCloud2`
  - `sensor_msgs/msg/LaserScan`
  - `nav_msgs/msg/Odometry`
  - `nav_msgs/msg/Path`
  - `visualization_msgs/msg/Marker`
  - `visualization_msgs/msg/MarkerArray`
  - `nav_msgs/msg/OccupancyGrid`
  - 自动订阅 `/tf` 和 `/tf_static`，将显示数据转换到选定的 Fixed Frame。
  - 找不到 TF 链时隐藏错误坐标的数据，并在对应 Display 显示原因。
- 点云与路径样式：
  - PointCloud2 支持按话题设置 `Point Size`。
  - Path 支持按话题设置线宽和颜色。
- 无人机位姿：
  - 位置面板中选择 odom 话题作为无人机模型位姿来源。
  - 当前 odom 订阅会被保护，避免 Displays 隐藏同名话题后无人机模型停止跟随。
- 期望目标：
  - 在位置信息下方输入目标 `Topic`、`X/Y/Z`。
  - `展示` 只在点云视图中预览目标。
  - `发布` 才向配置的话题发布 `geometry_msgs/msg/PoseStamped`。
  - 默认方向为 `+X`。
- 布局与视图：
  - 右侧面板支持手动拖拽高度。
  - 点云视图和右侧功能区比例可保存。
  - 网格、坐标轴、视角预设和相机状态可保存。

## 话题读取

Displays 添加话题时会读取当前 ROS2 图：

1. 后端优先执行 `ros2 topic list -t` 获取话题和类型。
2. 如果 CLI 不可用或超时，回退到 rclpy 的 topic discovery。
3. 前端 Add 面板和 Topic 下拉框打开时会刷新话题列表，也可以手动点击 `Refresh`。

因此话题来源是当前 ROS2 系统和 `.rvizweb` 配置文件，不来自 `.env` 或前端硬编码默认值。

## 配置文件

配置文件保存在：

```text
rvizweb_configs/*.rvizweb
```

通用配置为：

```text
rvizweb_configs/default.rvizweb
```

`default.rvizweb` 只包含通用界面设置，不绑定具体机器人话题。无人机配置保存在 `rvizweb_configs/uav1.rvizweb`。

当前设备的 `start.sh` 明确指定 `uav1.rvizweb` 为启动配置。临时切换配置时可覆盖：

```bash
RVIZWEB_CONFIG=default.rvizweb ./start.sh local
```

启动脚本会检查配置文件是否存在以及是否使用 `.rvizweb` 后缀，然后通过 `VITE_RVIZWEB_CONFIG` 交给前端自动读取。

保存配置采用同目录临时文件原子替换，覆盖和删除前的副本保存在 `rvizweb_configs/backups/`。后端会校验配置版本、结构、文件名和大小；配置读取失败时前端保持当前状态不变。

设置面板支持：

- 保存当前前端状态为 `.rvizweb`
- 读取已有配置
- 删除配置
- 自动兼容用户输入的 `.rviz` 后缀并保存为 `.rvizweb`

配置文件主要包含：

- `fixedFrame`
- `scene.showGrid`
- `scene.showAxes`
- `scene.viewPreset`
- `scene.camera`
- `layout.sceneWidth`
- `layout.panelHeights`
- `goal.topic`
- `goal.x/y/z`
- `position.odomTopic`
- `laser`
- `map`
- `displays`

后端配置 API：

```text
GET    /api/v1/configs
GET    /api/v1/configs/{name}
POST   /api/v1/configs/{name}
DELETE /api/v1/configs/{name}
```

## 启动

后端使用 [uv](https://docs.astral.sh/uv/) 管理 Python 环境。首次安装或依赖变化后执行：

```bash
cd /home/amov/RVIZ-RQT-VISUAL
./start.sh sync
```

本地启动：

```bash
cd /home/amov/RVIZ-RQT-VISUAL
./start.sh local
```

不传参数时默认也是本地模式：

```bash
./start.sh
```

本地模式需要：

- ROS2 环境可用
- Node.js 20.19+
- Python 3.10+
- curl（若未安装 `uv`，启动脚本会通过官方安装脚本自动安装）

启动脚本会读取项目根目录 `.env`，加载 ROS2 环境，检查默认 `.rvizweb` 配置以及 `FRONTEND_PORT`、`BACKEND_PORT` 指定的端口，等待前后端健康检查，并把输出统一写入 `logs/`。启动后显示的前端访问主机由 `FRONTEND_PUBLIC_HOST` 配置。启动失败会立即退出；Ctrl+C 会停止整个前后端进程组。

配置写入默认只允许本机和局域网地址。需要令牌时，在 `.env` 中将 `CONFIG_API_TOKEN` 与 `VITE_CONFIG_API_TOKEN` 设置成相同值。`CORS_ORIGINS` 应列出实际允许访问的前端地址。

脚本会尝试 source：

```bash
/opt/ros/humble/setup.bash
/home/amov/super_ros2_ws/install/setup.bash
```

分别启动：

```bash
cd backend
uv venv --system-site-packages .venv
VIRTUAL_ENV="$PWD/.venv" uv sync --active
source /opt/ros/humble/setup.bash
source /home/amov/super_ros2_ws/install/setup.bash
uv run --no-sync uvicorn app.main:app --host 0.0.0.0 --port 8000
```

```bash
cd frontend
npm ci
VITE_RVIZWEB_CONFIG=uav1.rvizweb npm run dev -- --host 0.0.0.0 --port 3000
```

访问地址：

- 前端：`http://localhost:3000/`
- 后端 API：`http://localhost:8000/`
- 后端文档：`http://localhost:8000/docs`

## 常见问题

### 文件监听数量不足

如果启动时报：

```text
OS file watch limit reached
ENOSPC: System limit for number of file watchers reached
```

可以临时增大系统监听数量：

```bash
sudo sysctl fs.inotify.max_user_watches=524288
sudo sysctl fs.inotify.max_user_instances=1024
```

也可以继续使用当前脚本中的 `CHOKIDAR_USEPOLLING=true` 轮询模式。

### Displays 没有话题

先确认 ROS2 环境中能看到话题：

```bash
ros2 topic list -t
```

如果命令行有话题但前端没有，检查后端是否 source 了正确的 ROS2 workspace，并重启后端。

### 修改配置后没有生效

保存配置前会捕获当前视角、布局比例和面板高度。读取配置后会恢复 Fixed Frame、Displays、视图、网格、坐标轴、目标点、odom 话题和布局。

## 验证

前端构建：

```bash
cd frontend
npm run build
```

后端语法检查：

```bash
cd backend
uv run pytest -q
uv run python -m compileall -q app
```

前端 TF 单元测试：

```bash
cd frontend
npm test
```

## 目录结构

```text
RVIZ-RQT-VISUAL/
├── backend/                  # FastAPI + rclpy 后端
│   └── app/
│       ├── api/v1/           # ROS、配置文件、可视化 API
│       └── services/         # rosbridge 与 ROS2 服务
├── frontend/                 # Vue 3 + Three.js 前端
│   └── src/
│       ├── components/RViz/  # 3D 场景、Displays、控制器
│       ├── components/panels # 设置、位置信息、期望目标等右侧面板
│       ├── components/layout # 主布局与面板容器
│       ├── composables/      # ROS bridge 连接与状态
│       └── services/         # 后端 API 封装
├── rvizweb_configs/          # .rvizweb 配置文件目录
├── .env                      # 运行环境配置，不保存 ROS 话题名
├── start.sh                  # 启动脚本
└── README.md
```

## 开发说明

- 新增右侧面板：在 `MainLayout.vue` 接入组件，并把需要持久化的状态写入配置快照。
- 新增可视化类型：优先扩展 `Scene3D.vue` 的订阅和渲染逻辑，再在 Displays 中补充对应的配置项。
- 新增后端接口：放在 `backend/app/api/v1/`，前端统一通过 `frontend/src/services/api.js` 封装。
- 配置项命名保持稳定，避免破坏已有 `.rvizweb` 文件。

## 后续计划

- 继续缩小 Element Plus 产物并完善组件、图标和样式的按需引入。
- 为 TF 增加严格的过去/未来外推错误状态，并继续覆盖 Display 生命周期。
- 增加 WebSocket 重连和真实 ROS2 图的自动化集成测试。

## 致谢

感谢 [lovelyyoshino/RVIZ-RQT-VISUAL](https://github.com/lovelyyoshino/RVIZ-RQT-VISUAL) 项目提供的基础与参考。
