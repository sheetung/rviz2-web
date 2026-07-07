# RViz2 Web 前端

这是一个通用的 RViz2 风格 Web 前端，用于在浏览器中查看 ROS2 点云、里程计位姿、路径、Marker、地图等数据，并提供基础的期望目标交互能力。项目由 Vue 3 + Three.js 前端和 FastAPI + rclpy 后端组成。

当前工程已适配无人机点云可视化场景。ROS 话题可在前端 Displays 中从当前 ROS2 话题列表选择，并可保存到 `rvizweb_configs/*.rvizweb` 配置文件中。

## 主要功能

- 常见 ROS2 消息的 3D 可视化：
  - `sensor_msgs/msg/PointCloud2`
  - `sensor_msgs/msg/LaserScan`
  - `nav_msgs/msg/Odometry`
  - `nav_msgs/msg/Path`
  - `visualization_msgs/msg/MarkerArray`
- 无人机位姿显示：
  - 使用配置文件中的位置 odom 话题作为无人机位置和姿态来源。
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

## 话题与配置

- Displays 中的 Add 会读取当前 ROS2 图中的话题，后端优先使用 `ros2 topic list -t` 获取话题和类型。
- Fixed Frame、Displays、点云大小、Path 颜色/宽度、位置 odom 话题、目标点和面板布局都可以保存到 `rvizweb_configs/*.rvizweb`。
- 默认配置文件为 `rvizweb_configs/default.rvizweb`，也可以在设置中另存、读取或删除其他配置。
- `.env` 只保留端口、日志级别、ROS_DOMAIN_ID 等运行环境配置，不再保存话题名；前端代码也不提供内置话题兜底。

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
│       ├── components/layout # 工作台布局与通用面板容器
│       └── config           # ROS 话题、工作台面板等配置
├── img/                     # README 图片
├── logs/                    # 运行日志
├── .env                     # 运行环境配置
├── start.sh                 # 启动脚本
└── README.md
```

## 前端扩展

- 新增右侧工作台面板：在 `MainLayout.vue` 接入对应组件，并把需要持久化的状态写入配置文件结构。
- 新增可视化/控制模块：优先放在 `frontend/src/components/RViz/`，复用 `WorkbenchPanel.vue` 作为面板外壳。
- 新增后端接口：统一在 `frontend/src/services/api.js` 增加 API 封装，组件侧不要直接拼接请求逻辑。

## 致谢

感谢 [lovelyyoshino/RVIZ-RQT-VISUAL](https://github.com/lovelyyoshino/RVIZ-RQT-VISUAL) 项目提供的基础与参考。
