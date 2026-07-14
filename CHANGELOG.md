# Changelog

本项目遵循语义化版本控制，整个工程统一使用一套版本号。

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
