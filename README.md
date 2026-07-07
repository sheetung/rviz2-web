# RViz2 Web 前端

这是一个通用的 RViz2 风格 Web 前端，用于在浏览器中查看 ROS2 点云、里程计位姿、路径、Marker、地图等数据，并提供基础的期望目标交互能力。项目由 Vue 3 + Three.js 前端和 FastAPI + rclpy 后端组成。

当前工程已适配无人机点云可视化场景。ROS 话题名不写死在 Vue 组件中，而是统一通过项目根目录的 `.env` 文件配置。

## 主要功能

- 常见 ROS2 消息的 3D 可视化：
  - `sensor_msgs/msg/PointCloud2`
  - `sensor_msgs/msg/LaserScan`
  - `nav_msgs/msg/Odometry`
  - `nav_msgs/msg/Path`
  - `visualization_msgs/msg/MarkerArray`
- 无人机位姿显示：
  - 使用 `VITE_ROS_ODOM_TOPIC` 作为无人机位置和姿态来源。
  - 3D 模型为 X 架构无人机，四个水平圆饼表示电机/桨叶，顶部小圆柱表示 LiDAR。
- 点云视图工具栏：
  - 重置视角
  - 网格/坐标轴显示切换
  - 视角预设：俯视图、侧视图、等距图
  - 期望目标：当前已实现 2D 期望，3D 期望预留
- 2D 期望目标交互：
  - 点击 `期望目标 -> 2D期望` 进入选择模式。
  - 左键按下选择目标位置。
  - 移动鼠标设置目标方向。
  - 松开左键发布目标。
  - 选择过程中按 `X` 取消本次目标点。
- 连接状态面板：
  - 右上角连接状态默认收起。
  - 点击连接状态可展开/收起运行状态信息。

## 话题配置

在项目根目录 `.env` 中配置 ROS 话题。前端只读取 `VITE_*` 环境变量；如果某个话题没有配置，前端不会偷偷使用默认话题。

示例：

```env
VITE_ROS_LASER_SCAN_TOPIC=/scan
VITE_ROS_POINTCLOUD_TOPIC=/uav1/prometheus/local_points
VITE_ROS_INFLATED_MAP_TOPIC=/rog_map/inf_occ
VITE_ROS_ODOM_TOPIC=/uav1/prometheus/odom_slam
VITE_ROS_POSE_TOPIC=/uav1/prometheus/pose_slam
VITE_ROS_EXPECTED_CONTROL_TOPIC=/goal_pose
VITE_ROS_INITIAL_POSE_TOPIC=/initialpose
VITE_ROS_GOAL_MARKER_TOPIC=/visualization/goal
VITE_ROS_EXP_SFC_TOPIC=/visualization/exp_sfc
VITE_ROS_PATH_TOPIC=/fsm/path
VITE_ROS_EXP_TRAJ_TOPIC=/visualization/exp_traj
VITE_ROS_BACKUP_TRAJ_TOPIC=/visualization/backup_traj
VITE_ROS_CMD_VEL_TOPIC=/cmd_vel
```

说明：

- 无人机位置和姿态由 `VITE_ROS_ODOM_TOPIC` 驱动。
- `VITE_ROS_POSE_TOPIC` 当前保留给可能的 PoseStamped 可视化用途，不作为无人机位姿来源。
- 2D 期望目标发布到 `VITE_ROS_EXPECTED_CONTROL_TOPIC`。

## 启动方式

推荐使用项目根目录的启动脚本：

```bash
cd /home/amov/RVIZ-RQT-VISUAL
./start.sh
```

也可以分别启动后端和前端。

后端：

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

前端：

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 3000
```

默认访问地址：

- 前端：`http://192.168.1.66:3000/`
- 后端 API：`http://192.168.1.66:8000/`
- 后端文档：`http://192.168.1.66:8000/docs`

## 快捷键

3D 视图获得焦点后可用：

- `D`：输出调试信息
- `R`：重置视角
- `F`：适配点云
- `G`：切换网格
- `M`：适配地图
- `C`：检查订阅状态
- `X`：清除全部可视化对象

进入 2D 期望目标选择时，`X` 会临时变为“取消本次目标点”，不会清除全部对象。


## 目录结构

```text
RVIZ-RQT-VISUAL/
├── backend/                 # FastAPI + rclpy 后端
├── frontend/                # Vue 3 + Three.js 前端
│   └── src/
│       ├── components/RViz  # 3D 场景、目标工具、话题订阅
│       ├── components/RQT   # RQT 风格节点/主题工具
│       └── config           # ROS 话题环境变量配置
├── img/                     # README 图片
├── logs/                    # 运行日志
├── .env                     # Vite 与 ROS 话题配置
├── start.sh                 # 启动脚本
└── README.md
```

## 致谢

感谢 [lovelyyoshino/RVIZ-RQT-VISUAL](https://github.com/lovelyyoshino/RVIZ-RQT-VISUAL) 项目提供的基础与参考。
