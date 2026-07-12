# RVizWeb

> Current release: `v1.0.0`

The root `VERSION` file is the single source of truth for the application version. API version `v1` and `.rvizweb` configuration format version `1` evolve independently. Expand the connection status in the top-right corner to view all three versions. Run `node scripts/sync-version.mjs 1.0.1` after changing the release version, or `node scripts/sync-version.mjs --check` to verify consistency.

![RVizWeb](img/1.png)

![RVizWeb](img/2.png)

[中文](./README.md)

RVizWeb is a browser-based visualization frontend for ROS2, supporting point clouds, odometry, paths, markers, and more. It provides UAV pose display, desired target input, real-time data charts, and RViz-style Displays management. The project consists of a Vue 3 + Three.js frontend and a FastAPI + rclpy backend.

## Features

- RViz-style Displays:
  - Read topics from the current ROS2 graph and add display items.
  - Toggle visibility with an eye icon.
  - Add, delete, and modify topics; message types for added Displays automatically follow ROS2 topics without separate editing.
  - Add dialog supports `By topic` and `By display type`; the type list only includes types actually present in the current ROS2 graph.
  - Hiding or deleting a Display clears its message cache; TF updates will not recreate hidden objects.
  - Each Display can save independent configuration.
- 3D Visualization:
  - `sensor_msgs/msg/PointCloud2`
  - `sensor_msgs/msg/LaserScan`
  - `nav_msgs/msg/Odometry`
  - `nav_msgs/msg/Path`
  - `visualization_msgs/msg/Marker`
  - `visualization_msgs/msg/MarkerArray`
  - `nav_msgs/msg/OccupancyGrid`
  - Auto-subscribes to `/tf` and `/tf_static`, transforming display data to the selected Fixed Frame.
  - Hides data with unresolvable TF chains and shows the reason on the corresponding Display.
- RViz-style Tools & Camera:
  - Top toolbar provides Move Camera, Select, Focus, 2D Pose Estimate, and 2D Goal.
  - Orbit controls: left-click to rotate, middle-click to pan, right-click drag or scroll to zoom.
  - Shortcuts: `M` Move, `S` Select, `F` Focus, `P` 2D Pose, `G` 2D Goal, `Esc` Cancel.
  - Selected objects show a cyan bounding box; top-down preset uses an orthographic camera.
  - Toolbar supports capturing the current 3D canvas as PNG.
  - Supports recording the 3D canvas at 30 FPS; click again to stop and download as WebM. Selects VP9, VP8, or plain WebM based on browser capabilities.
- Point Cloud & Path Styles:
  - PointCloud2 supports per-topic `Point Size`.
  - Path supports per-topic line width and color.
  - MarkerArray supports color override and opacity; leaving color empty uses the message's own color.
- UAV Pose:
  - Select an odom topic in the position panel as the UAV model pose source.
  - The current odom subscription is protected from Display hiding to prevent the UAV model from stopping.
- Desired Target:
  - Enter target `Topic`, `X/Y/Z` below the position info.
  - `Show` only previews the target in the point cloud view.
  - `Publish` sends a `geometry_msgs/msg/PoseStamped` to the configured topic.
  - Default orientation is `+X`.
  - Publish status reads the current WebSocket connection in real time, avoiding stale "disconnected" reports from component initialization.
- Layout & View:
  - Right panel supports manual height dragging.
  - Point cloud view and right panel ratio can be saved.
  - 3D canvas resizes in real time with split pane and bottom dock dimensions, avoiding blank areas after dragging.
  - Grid, axes, view preset, and camera state can be saved.
- Data Charts:
  - Displayed in a resizable dock below the 3D view, collapsed by default at startup.
  - Select numeric fields from topics in the current ROS2 graph; supports multi-curve visibility toggling and deletion.
  - Supports 10-second to 10-minute time ranges, scroll wheel zoom, drag to view history, and return to real time.
  - Pause only freezes the display; data continues to buffer in the background.
  - X-axis shows relative time: seconds for short windows, auto-switches to minutes for 1 minute and above.

> The map file settings entry is temporarily hidden. The underlying display logic and existing config fields for `nav_msgs/msg/OccupancyGrid` are preserved for future restoration.

## Topic Discovery

When adding topics in Displays, the current ROS2 graph is read:

1. The backend first runs `ros2 topic list -t` to get topics and types.
2. If the CLI is unavailable or times out, it falls back to rclpy topic discovery.
3. The frontend Add panel and topic dropdowns refresh the topic list when opened, or click `Refresh` manually.

Topic sources are the current ROS2 system and `.rvizweb` config files, not `.env` or hardcoded frontend defaults.

## Configuration Files

Configuration files are stored in:

```text
rvizweb_configs/*.rvizweb
```

The generic configuration is:

```text
rvizweb_configs/default.rvizweb
```

`default.rvizweb` only contains generic UI settings and is not tied to any specific robot topics. UAV configuration is saved locally as `rvizweb_configs/uav1.rvizweb`; this personal config is ignored by `.gitignore` and not committed to the repository.

The current device's `start.sh` explicitly specifies `uav1.rvizweb` as the startup config. To temporarily switch configs:

```bash
RVIZWEB_CONFIG=default.rvizweb ./start.sh local
```

The startup script validates that the config file exists and uses the `.rvizweb` suffix, then passes it to the frontend via `VITE_RVIZWEB_CONFIG`.

Saving uses atomic replacement via a temp file in the same directory. Backups of overwritten and deleted configs are stored in `rvizweb_configs/backups/`. The backend validates config version, structure, filename, and size; the frontend keeps its current state unchanged on read failure.

The settings panel supports:

- Saving the current frontend state as `.rvizweb`
- Loading existing configs
- Deleting configs
- Switching between dark and light themes, saved with the config
- Auto-compat with user-entered `.rviz` suffix, saved as `.rvizweb`

Configuration files primarily include:

- `fixedFrame`
- `followFrame` (optional; follows TF frame translation without rotating the camera view)
- `scene.showGrid`
- `scene.showAxes`
- `scene.viewPreset`
- `scene.camera`
- `layout.sceneWidth`
- `layout.panelHeights`
- `layout.collapsedPanels`
- `appearance.theme`
- `goal.topic`
- `goal.x/y/z`
- `position.odomTopic`
- `laser`
- `map`
- `displays`

Backend config API:

```text
GET    /api/v1/configs
GET    /api/v1/configs/{name}
POST   /api/v1/configs/{name}
DELETE /api/v1/configs/{name}
```

## Getting Started

Before first use, copy the environment config example and modify as needed:

```bash
cd <your_workspace>/rviz2-web
cp .env.example .env
# Edit .env to adjust ports, ROS_DOMAIN_ID, etc.
```

The backend uses [uv](https://docs.astral.sh/uv/) for Python environment management. Run the following on first install or when dependencies change:

```bash
./start.sh sync
```

Normal local startup:

```bash
./start.sh local
```

Running without arguments also defaults to local mode:

```bash
./start.sh
```

Normal mode builds the frontend for production first, then serves pages via a static preview server without watching source files. For frontend development with hot reload:

```bash
./start.sh dev
```

Local mode requires:

- ROS2 environment available
- Node.js 20.19+
- Python 3.10+
- curl (if `uv` is not installed, the startup script will install it via the official install script)

The startup script reads `.env` from the project root, loads the ROS2 environment, checks the default `.rvizweb` config and ports specified by `FRONTEND_PORT`/`BACKEND_PORT`, waits for frontend and backend health checks, and writes all output to `logs/`. The frontend access host shown after startup is configured by `FRONTEND_PUBLIC_HOST`. Startup failures exit immediately; Ctrl+C stops the entire frontend and backend process group.

The browser tab and top-left title can be changed in `.env`:

```env
VITE_APP_TITLE=RVizWeb
```

In normal mode, re-run `./start.sh` after changes to rebuild the frontend. In dev mode, changes take effect on Vite restart or environment reload.

Config writes are restricted to localhost and LAN addresses by default. When a token is needed, set `CONFIG_API_TOKEN` and `VITE_CONFIG_API_TOKEN` to the same value in `.env`. `CORS_ORIGINS` should list the actual allowed frontend addresses.

The script sources setup.bash files in the order specified by `ROS2_SETUP_PATHS` in `.env`:

```bash
source /opt/ros/humble/setup.bash
source <your_workspace>/install/setup.bash
```

Starting separately:

> Generally not recommended

```bash
cd backend
uv venv --system-site-packages .venv
VIRTUAL_ENV="$PWD/.venv" uv sync --active
source /opt/ros/humble/setup.bash
source <your_workspace>/install/setup.bash
uv run --no-sync uvicorn app.main:app --host 0.0.0.0 --port 8000
```

```bash
cd frontend
npm ci
VITE_RVIZWEB_CONFIG=uav1.rvizweb npm run build
npm run preview -- --host 0.0.0.0 --port 3000
```

Access URLs:

- Frontend: `http://localhost:3000/`
- Backend API: `http://localhost:8000/`
- Backend docs: `http://localhost:8000/docs`

## FAQ

### File Watch Limit

This may only occur in dev mode. If `./start.sh dev` reports:

```text
OS file watch limit reached
ENOSPC: System limit for number of file watchers reached
```

Temporarily increase system watch limits:

```bash
sudo sysctl fs.inotify.max_user_watches=524288
sudo sysctl fs.inotify.max_user_instances=1024
```

You can also use `CHOKIDAR_USEPOLLING=true` polling mode in `.env`. Normal `./start.sh` does not watch files and is not affected by this limit.

### No Topics in Displays

First confirm that topics are visible in the ROS2 environment:

```bash
ros2 topic list -t
```

If the CLI shows topics but the frontend does not, check that the backend sourced the correct ROS2 workspace, then restart the backend.

### Config Changes Not Taking Effect

Before saving a config, the current view, layout ratio, and panel heights are captured. After loading a config, Fixed Frame, Displays, view, grid, axes, goal point, odom topic, and layout are restored.

### Screenshot or Recording Not Downloading

Screenshots and recordings use the browser's download capability. Ensure the site has download permission. Recording relies on `MediaRecorder` and `canvas.captureStream()`; current versions of Chrome, Edge, or Firefox are recommended. Recordings use the WebM format and do not include the toolbar or right panel.

## Verification

Frontend build:

```bash
cd frontend
npm run build
```

Frontend static check:

```bash
cd frontend
npm run lint:check
```

Backend syntax check:

```bash
cd backend
uv run pytest -q
uv run python -m compileall -q app
```

Frontend unit tests (currently covering TF cache and interpolation):

```bash
cd frontend
npm test
```

## Directory Structure

```text
RVIZ-RQT-VISUAL/
├── backend/                  # FastAPI + rclpy backend
│   └── app/
│       ├── api/v1/           # ROS, config, and visualization APIs
│       └── services/         # rosbridge and ROS2 services
├── frontend/                 # Vue 3 + Three.js frontend
│   └── src/
│       ├── components/RViz/  # 3D scene, Displays, controllers
│       ├── components/panels # Settings, position info, desired target, and data charts
│       ├── components/layout # Main layout and panel containers
│       ├── composables/      # ROS bridge connection and state
│       └── services/         # Backend API wrappers
├── rvizweb_configs/          # .rvizweb config file directory
├── .env                      # Runtime environment config (no ROS topic names)
├── start.sh                  # Startup script
└── README.md
```

## Development Notes

- Adding a new right panel: wire the component into `MainLayout.vue` and add persistent state to the config snapshot.
- Adding a new visualization type: extend `Scene3D.vue` subscription and rendering logic first, then add corresponding config items in Displays.
- Adding a new backend endpoint: place it in `backend/app/api/v1/`; frontend wrappers go in `frontend/src/services/api.js`.
- Keep config key names stable to avoid breaking existing `.rvizweb` files.

## Roadmap

- Add strict past/future extrapolation error states for TF and continue covering Display lifecycles.
- Add automated integration tests for WebSocket reconnection and real ROS2 graphs.
- Clean up unreferenced legacy layouts and example components to further reduce maintenance costs.

## Acknowledgements

Thanks to [lovelyyoshino/RVIZ-RQT-VISUAL](https://github.com/lovelyyoshino/RVIZ-RQT-VISUAL) for the foundation and reference.
