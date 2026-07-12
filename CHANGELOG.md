# Changelog

本项目遵循语义化版本控制，整个工程统一使用一套版本号。

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
