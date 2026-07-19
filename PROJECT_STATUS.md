# RVizWeb 项目状态

工程版本：`v1.1.5`（前端配置话题链路一致性修复版本）

整个工程只维护一套版本号，以根目录 `VERSION` 为准，并同步到工程清单和前端系统状态。

更新时间：2026-07-19

## 总体结论

当前工程可作为 ROS2 浏览器可视化与调试工具使用。默认仅监听回环地址；开放到
可信局域网时默认免认证，同时保留 WebSocket Origin 校验和 ROS 发布白名单。
公网访问仍要求统一访问令牌和 HttpOnly 会话。

当前最可靠的运行方式是 `./start.sh sync` 后执行 `./start.sh local`。Dockerfile
已按 Node 22、uv 锁文件与 Nginx 同源代理重写，但 DDS 容器网络仍需要在目标
设备上集成验证。

## 已实现并在当前代码中保留的能力

### 启动与配置

- `start.sh` 支持 `install`、`sync`、`local`、`dev`、`help`；默认 `local` 使用构建后的静态资源，`dev` 才启用热更新。
- 缺少 uv 时可通过官方安装脚本自动安装。
- 后端使用 uv 锁定依赖，前端使用 `npm ci`。
- 启动时以非执行方式解析 `.env`，文件由安装脚本收紧为 `0600`。
- 前后端默认绑定 `127.0.0.1`；RFC1918/ULA 局域网默认免认证，公网访问要求统一令牌。
- 支持通过 `RVIZWEB_CONFIG` 选择启动配置，默认使用 `default.rvizweb`。
- 前后端健康检查、日志归档和退出时进程清理已集成到启动脚本。
- `/docs` 使用仓库内 Swagger UI 5.9.0 资源，不依赖浏览器访问外部 CDN；`/redoc` 保持关闭。
- 前端已升级到 Vite 8、Axios 1.18、Vue 3.5 和 Element Plus 2.14；当前 `npm audit` 为 0 项漏洞。
- Element Plus 已改为组件、服务和样式按需引入；生产构建按 Vue、Three.js、
  Element Plus 和异步设置面板拆分 chunk。

### ROS2 与通信

- 后端使用 rclpy 直接访问 ROS2 图。
- FastAPI `/ws` 提供浏览器实时通信入口。
- WebSocket 使用应用层 `ping/pong` 测量真实往返延迟，状态栏不再展示固定网络数值。
- 后端通过 `ros2 topic list -t --no-daemon` 查询话题，不创建或依赖可能残留的 ROS2 CLI daemon。
- 支持话题发现、会话化订阅、取消订阅和带确认的发布；断线重连会恢复期望订阅。
- WebSocket 为每个客户端使用有界发送队列，慢客户端不会串行阻塞其他客户端。
- 提供节点、话题频率和系统状态查询 API；ROS 图查询带短 TTL 缓存，频率接口默认
  返回已观测值，只有显式启用主动采样时才临时订阅全部可用话题。
- 支持 `/tf`、`/tf_static` 与 Fixed Frame 转换的前端链路。
- 动态 TF 按坐标边保留有限历史，并根据显示消息时间戳插值平移和旋转。

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
- Display 类型由当前 ROS2 话题自动绑定；按类型添加时只列出实际存在话题的消息类型。
- Marker/MarkerArray 按 `(ns,id)` 维护对象，支持删除、全部删除、生命周期和常用
  几何类型；未知类型不会渲染成虚假立方体。
- 隐藏 Display 会清理最后消息缓存，不会在后续 TF 更新时被重新创建。
- 3D 工具栏提供紧邻排列的截图和录像按钮：截图下载 PNG，录像下载 WebM。
- 录像按钮在录制期间显示红色停止状态，结束后自动恢复。
- WebM 编码按浏览器能力依次选择 VP9、VP8 或默认 WebM，不再尝试输出 MP4。

### 目标与配置文件

- 支持目标点预览和 `PoseStamped` 发布。
- `.rvizweb` 可保存、读取和删除。
- 配置写入包含名称、大小、版本和结构校验。
- 覆盖与删除前创建备份，写入使用原子替换。
- 配置读写使用统一访问边界；可信局域网默认免认证，公网可要求访问会话；配置 schema 严格校验并提供 `extensions` 扩展区。
- RTSP 凭据不持久化，目标地址经过 DNS/IP 策略检查，会话和 FFmpeg 进程有全局配额。
- ROS 发布路径使用实时 WebSocket 连接状态，目标发布与订阅显示共享同一连接来源。
- JSON 整数发布到 ROS 浮点字段时会统一转换为浮点数，避免 Pose、Twist 等消息保留为默认零值。
- 系统状态显示当前配置名称、未保存修改和配置文件实际修改时间；设置、Displays、布局和相机视角均纳入变更判断。
- `uav1.rvizweb` 作为设备个人配置保留在本机，并由 Git 忽略。

## 当前限制与已知偏差

### 自动化测试仍需扩展

`backend/tests/` 已覆盖配置原子保存、备份、访问会话、路径安全、RTSP
地址策略/DNS 固定、ROS 消息数值转换与大小限制、WebSocket 心跳、慢客户端
清理、publisher 所有权、本地 Swagger 资源和启动脚本基础行为。前端已有 TF
时间戳、插值、坐标链、静态变换、缓存裁剪、配置指纹、未保存状态、RTSP
脱敏和公开后端 URL 测试，但仍没有组件或端到端测试，ROS2 实时链路也缺少
自动化集成测试。现有验证主要依靠：

- `uv run pytest -q`
- `uv run flake8 app`
- `npm test`
- `npm run lint:check`
- `npm run build`
- `uv run python -m compileall -q app`
- 真实 ROS2 环境中的人工集成测试

因此当前测试可以防止配置存储与启动脚本的基础回归，但不能视为完整 API、前端或 ROS2 覆盖。

### Docker 仍需 ROS2 网络集成验证

- `start.sh` 没有 `docker` 子命令。
- 仓库没有 `docker-compose.yml`。
- Dockerfile 已修复前端 Node 版本、开发依赖构建、后端锁文件安装、同源 WebSocket
  和健康检查；DDS 发现和宿主机网络模式仍需按部署环境验证。

### ROS2 发行版与工作空间差异

`.env.example` 默认加载 ROS2 Humble。其他发行版或工作空间应通过
`ROS2_SETUP_PATHS` 配置，无需修改启动脚本。

### TF 时间语义仍有边界

当前 Fixed Frame 已按消息时间戳查询动态 TF 历史，并在相邻样本之间插值。缓存默认保留 10 秒且每条边最多 200 个样本；超出缓存范围时使用最邻近样本，尚未实现 tf2/RViz 的过去或未来外推错误状态。坐标系父级在运行时改变时，该子坐标系的旧历史会被清空。

### 浏览器录像时间线

当前录像使用 `canvas.captureStream()` 与 `MediaRecorder` 直接生成 WebM，优点是不需要上传画面或安装额外编码器。录像时间戳仍由浏览器媒体管线管理；页面降频、标签页进入后台或渲染负载过高时，可能出现丢帧或时间线不均匀。后端目前不接收画布帧，也不执行 FFmpeg 转码。

## 当前验证基线

每次合入核心修改前至少应执行：

```bash
bash -n start.sh
bash -n install.sh docker/start-container.sh

cd frontend
npm test
npm run lint:check
npm run build

cd ../backend
uv run pytest -q
uv run flake8 app
uv run python -m compileall -q app
```

涉及 ROS2 的修改还应验证：

1. `ros2 topic list -t` 能发现目标话题。
2. 前端 Displays 能刷新并订阅话题。
3. PointCloud2、Odometry、Path、Marker 和 TF 链路按修改范围正常显示。
4. WebSocket 断开后能恢复连接与订阅。
5. 配置保存、覆盖备份、读取和删除符合预期。
6. `Ctrl+C` 后前后端进程均退出。
7. 截图可下载有效 PNG；开始和结束录像后可下载并播放 WebM。
8. MarkerArray 修改颜色、透明度以及隐藏/再次显示均符合 Display 状态。
9. 录像期间按钮保持红色，结束后下载的 WebM 可播放且时长基本符合实际录制时间。

## 优先级建议

### P1：测试与稳定性

- 为 HTTP/WebSocket 认证握手和 Origin 策略补充端到端测试。
- 为 TF 外推错误、缺失 TF 状态和 Display 生命周期补充前端测试。
- 增加 WebSocket 发布/订阅和重连的集成测试。
- 在真实 ROS2 图中覆盖自定义消息、QoS 不匹配和高频点云。

### P2：TF 与性能

- 评估 TF 外推容差和错误展示，使行为更接近 tf2/RViz。
- 对大点云进行采样、限频、内存复用或 LOD 优化。
- 评估 WebSocket 二进制传输或压缩，减少大消息的 JSON 开销。
- 持续监控 Three.js 与主布局包体积，并结合实际路由评估进一步异步拆分。
- 若原生 WebM 时间线无法满足需求，评估接入 `canvas-record` 或 Mediabunny，以固定帧时间戳导出视频；暂不引入后端帧上传和 FFmpeg 编码链路。

### P3：部署与清理

- 在真实设备上验证容器启动、健康检查和 DDS 网络模式。
- 继续清理当前大组件内部的调试日志和可拆分逻辑。
- 将用户指南、开发指南和状态报告中的重复内容继续收敛。

## 状态判定

- 本地启动链路：可用，依赖固定 ROS2 路径。
- ROS2 发现与 WebSocket 桥接：可用，需要网络与 DDS 环境正确。
- 核心 3D 显示：可用，TF 已支持有限历史与插值，外推语义仍有限；截图可用，录像采用浏览器原生 WebM。
- `.rvizweb` 配置管理：已实现，存储与前端变更状态已有单元测试，组件和端到端覆盖仍不足。
- Docker 部署：构建链路已重写，DDS 网络尚未做目标设备集成验证。
- 自动化测试：当前前端 8 个测试套件、后端 59 项通过，组件、端到端与 ROS2
  集成覆盖仍不足。
