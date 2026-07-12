# RVizWeb 项目状态

更新时间：2026-07-12

## 总体结论

当前工程可作为 ROS2 本地网络中的浏览器可视化与调试工具使用。核心链路已经形成：FastAPI/rclpy 后端加入 ROS2 图，浏览器通过 `/ws` 收发消息，Three.js 场景按 `.rvizweb` 配置展示数据。

当前最可靠的运行方式是 `./start.sh sync` 后执行 `./start.sh local`。Dockerfile 尚未按当前工程完整验证；自动化测试覆盖也不足，因此不再使用“100% 完成”或未经验证的完成度百分比描述项目状态。

## 已实现并在当前代码中保留的能力

### 启动与配置

- `start.sh` 支持 `sync`、`local`、`dev`、`help`；默认 `local` 使用构建后的静态资源，`dev` 才启用热更新。
- 缺少 uv 时可通过官方安装脚本自动安装。
- 后端使用 uv 锁定依赖，前端使用 `npm ci`。
- 启动时读取 `.env`，端口使用 `BACKEND_PORT` 与 `FRONTEND_PORT`。
- 支持通过 `RVIZWEB_CONFIG` 选择启动配置，默认使用 `uav1.rvizweb`。
- 前后端健康检查、日志归档和退出时进程清理已集成到启动脚本。
- 前端已升级到 Vite 8、Axios 1.18、Vue 3.5 和 Element Plus 2.14；当前 `npm audit` 为 0 项漏洞。
- Element Plus 已改为组件、服务和样式按需引入；生产 JS 从约 973 KB 降至 342 KB，CSS 从约 356 KB 降至 111 KB。

### ROS2 与通信

- 后端使用 rclpy 直接访问 ROS2 图。
- FastAPI `/ws` 提供浏览器实时通信入口。
- 支持话题发现、订阅、取消订阅和发布。
- 提供节点、话题频率和系统状态查询 API。
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
- MarkerArray 支持按 Display 覆盖颜色和透明度。
- 隐藏 Display 会清理最后消息缓存，不会在后续 TF 更新时被重新创建。
- 3D 工具栏支持 PNG 截图，以及按浏览器能力输出 MP4 或 WebM 的录像下载。

### 目标与配置文件

- 支持目标点预览和 `PoseStamped` 发布。
- `.rvizweb` 可保存、读取和删除。
- 配置写入包含名称、大小、版本和结构校验。
- 覆盖与删除前创建备份，写入使用原子替换。
- 配置写接口支持可选令牌。
- ROS 发布路径使用实时 WebSocket 连接状态，目标发布与订阅显示共享同一连接来源。
- `uav1.rvizweb` 作为设备个人配置保留在本机，并由 Git 忽略。

## 当前限制与已知偏差

### 自动化测试仍需扩展

`backend/tests/` 已覆盖配置原子保存、备份、写入权限、路径安全和启动脚本基础行为。前端已有 TF 时间戳、插值、坐标链、静态变换与缓存裁剪测试，但仍没有组件或端到端测试，ROS2 实时链路也缺少自动化集成测试。现有验证主要依靠：

- `uv run pytest -q`
- `npm test`
- `npm run lint:check`
- `npm run build`
- `uv run python -m compileall -q app`
- 真实 ROS2 环境中的人工集成测试

因此当前测试可以防止配置存储与启动脚本的基础回归，但不能视为完整 API、前端或 ROS2 覆盖。

### Docker 尚非推荐路径

- `start.sh` 没有 `docker` 子命令。
- 仓库没有 `docker-compose.yml`。
- Dockerfile 保留了旧式单容器启动结构，尚需验证前端产物、后端依赖、环境变量和 DDS 网络。

### ROS2 环境路径与发行版固定

`start.sh` 当前写死尝试加载 ROS2 Humble 和 `/home/amov/super_ros2_ws`。在其他用户、工作空间或 ROS2 发行版上，需要调整脚本或预先加载环境。

### TF 时间语义仍有边界

当前 Fixed Frame 已按消息时间戳查询动态 TF 历史，并在相邻样本之间插值。缓存默认保留 10 秒且每条边最多 200 个样本；超出缓存范围时使用最邻近样本，尚未实现 tf2/RViz 的过去或未来外推错误状态。坐标系父级在运行时改变时，该子坐标系的旧历史会被清空。

## 当前验证基线

每次合入核心修改前至少应执行：

```bash
bash -n start.sh

cd frontend
npm test
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
7. 截图可下载有效 PNG；开始和结束录像后可下载并播放 WebM。
8. MarkerArray 修改颜色、透明度以及隐藏/再次显示均符合 Display 状态。

## 优先级建议

### P0：配置与启动一致性

- 让 ROS2 安装路径和工作空间路径可配置，避免绑定单台设备。
- 明确 `DEBUG`、`FRONTEND_HOST` 的实际读取链路。

### P1：测试与稳定性

- 为 `.rvizweb` 校验、原子保存、备份和令牌权限补充后端测试。
- 为 TF 外推错误、缺失 TF 状态和 Display 生命周期补充前端测试。
- 增加 WebSocket 发布/订阅和重连的集成测试。
- 在真实 ROS2 图中覆盖自定义消息、QoS 不匹配和高频点云。

### P2：TF 与性能

- 评估 TF 外推容差和错误展示，使行为更接近 tf2/RViz。
- 对大点云进行采样、限频、内存复用或 LOD 优化。
- 评估 WebSocket 二进制传输或压缩，减少大消息的 JSON 开销。
- 持续监控 Three.js 与主布局包体积，并结合实际路由评估进一步异步拆分。

### P3：部署与清理

- 决定是否正式维护 Docker；若维护，应重写并验证容器启动、健康检查和 DDS 网络说明。
- 继续清理当前大组件内部的调试日志和可拆分逻辑。
- 将用户指南、开发指南和状态报告中的重复内容继续收敛。

## 状态判定

- 本地启动链路：可用，依赖固定 ROS2 路径。
- ROS2 发现与 WebSocket 桥接：可用，需要网络与 DDS 环境正确。
- 核心 3D 显示：可用，TF 已支持有限历史与插值，外推语义仍有限。
- `.rvizweb` 配置管理：已实现，自动化回归测试不足。
- Docker 部署：保留实现，当前未验证。
- 自动化测试：配置与启动脚本已有基础覆盖，前端、TF 与 ROS2 集成覆盖仍不足。
