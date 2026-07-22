# Changelog

本项目遵循语义化版本控制，整个工程统一使用一套版本号。

## [1.2.0] - 2026-07-22

### Added

- 增加 `VITE_ROS_WS_URL`，支持配置浏览器使用的完整 WebSocket 地址。
- 数据图表支持 PX4 等自定义 ROS 消息，并可从首条消息动态发现数值字段。
- 增加 WebSocket、Publisher 所有权、Marker 状态、自动重连和图表字段回归测试。

### Changed

- ROS 高频消息按 Topic 合并为最新帧，WebSocket 客户端使用相互隔离的有界发送队列。
- ROS 图查询增加短时缓存，消息转换和 JSON 序列化移出主事件循环。
- Marker 的 TF 刷新改为原位更新，避免重建对象和重置 lifetime。
- 前后端默认绑定回环地址；应用不再提供登录或配置写入 Token 鉴权，局域网和公网访问边界由防火墙、VPN 或可信反向代理负责。
- 重写 Docker 多阶段构建、Nginx 同源代理、启动脚本和依赖锁定流程。

### Fixed

- 修复 REST 并发发布共用 owner 时 Publisher 被提前销毁的问题。
- 修复 Marker 在 TF 延迟到达后无法恢复显示，以及 MarkerArray lifetime 被重复重置的问题。
- 修复后端短暂离线后前端可能永久停止自动重连的问题。
- 修复 PX4 消息中的 NaN/Infinity 导致浏览器拒绝整条 WebSocket JSON 消息的问题。
- 修复未测量 Topic 被误报为“无数据”，以及图表 Y 轴小范围刻度显示相同的问题。
- 调整 Odom 面板连接状态位置并移除重复的话题状态行。

## [1.1.5] - 2026-07-18

### Fixed

- 修复位姿控制器的话题发现结果可能覆盖 `.rvizweb` 中 odom 话题的异步初始化竞争。
- 修复 odom、激光、点云和地图切换话题后旧订阅未正确清理的问题。
- 修复加载空话题配置时遗留上一份配置状态，以及点云话题未恢复的问题。
- 修复 Displays 面板自行应用默认配置可能与启动配置异步加载竞争的问题。

## [1.1.1] - 2026-07-14

### Added

- 增加可配置 RTSP 视频连接入口，视频地址和窗口布局可随 `.rvizweb` 配置保存。
- WebSocket 协议增加系统状态查询，CPU、内存和温度复用前端现有实时连接。

### Changed

- WebSocket 地址跟随后端配置端口，避免修改 `BACKEND_PORT` 后仍连接前端端口。
- RTSP 输入框使用通用本机占位地址，不再包含部署设备地址。
- 前端系统消息统一使用同一通知服务、显示时长和去重规则。

### Fixed

- 修复统一通知服务后遗漏 Message 样式，导致读取话题等通知不可见的问题。
- 修复目标发布链路读取到过期 WebSocket 连接状态的问题。

## [1.1.0] - 2026-07-14

### Added

- PointCloud2 Display 支持按话题选择 `Points` 或 `Boxes` 渲染方式。
- `Points` 与 `Boxes` 分别提供独立的 `Point Size` 和 `Box Size` 配置，并随 `.rvizweb` 配置保存和恢复。
- `Boxes` 使用 `InstancedMesh` 批量渲染真实三维体素，并保留逐实例高度颜色映射。

### Changed

- 同一话题的点云样式调整直接作用于当前对象，不再反复退订和重新订阅。
- 体素颜色改为不受场景灯光衰减的原色显示，使视觉效果更接近 RViz。
- 点云聚焦支持实例化体素的完整边界框以及 Fixed Frame 变换。

### Fixed

- 修复 Boxes 实例颜色被缺失的普通顶点颜色通道压黑的问题。
- 修复坐标轴文字透明 Sprite 写入深度缓冲，导致视角变化时出现方形空白的问题。

## [1.0.2] - 2026-07-13

### Fixed

- 修复 WebSocket JSON 整数无法赋值给 ROS2 浮点字段，导致目标点、初始位姿、Pose 和 Twist 的整数坐标被静默保留为 0 的问题。
- 统一期望目标表单的数据源，确保配置默认值、展示值和发布值一致。
- 增加跨消息类型的整数转浮点回归测试。

## [1.0.1] - 修复前端打开时主题渲染错误
## [1.0.0] - 2026-07-12

### Added

- ROS2 话题发现、订阅、取消订阅和消息发布。
- PointCloud2、LaserScan、Odometry、Path、Marker 与 MarkerArray 三维显示。
- `/tf`、`/tf_static`、Fixed Frame、TF 历史插值和 Follow Frame。
- RViz 风格 Displays、2D 目标、相机工具、PNG 截图和 WebM 录像。
- `.rvizweb` 配置保存、读取、校验、原子写入和备份。
- uv 后端依赖管理、前后端健康检查及统一启动脚本。

### Fixed

- 修复隐藏 Display 被后续 TF 更新重新创建的问题。
- 修复目标发布读取旧 ROS 连接状态的问题。
- 修复点云、MarkerArray 与相机视角相关的显示和交互问题。
