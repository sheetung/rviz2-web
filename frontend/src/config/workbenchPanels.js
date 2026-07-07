export const WORKBENCH_PANELS = [
  {
    id: 'scene',
    title: '3D 可视化',
    drag: { x: 20, y: 20, width: 800, height: 600 }
  },
  {
    id: 'gps',
    title: '位置信息',
    drag: { x: 860, y: 20, width: 300, height: 220 },
    fullscreen: true
  },
  {
    id: 'topics',
    title: '话题控制',
    drag: { x: 860, y: 260, width: 420, height: 340 },
    fullscreen: true
  },
  {
    id: 'settings',
    title: '设置',
    drag: { x: 1300, y: 20, width: 360, height: 300 },
    fullscreen: true
  },
  {
    id: 'controller',
    title: '3D 控制器',
    drag: { x: 1180, y: 300, width: 240, height: 180 },
    fullscreen: true
  },
  {
    id: 'status',
    title: '状态面板',
    drag: { x: 20, y: 640, width: 200, height: 160 },
    fullscreen: true
  },
  {
    id: 'chart',
    title: '数据图表',
    drag: { x: 240, y: 640, width: 200, height: 160 },
    fullscreen: true
  }
]

export const WORKBENCH_PANEL_ORDER = WORKBENCH_PANELS.map(panel => panel.id)

export const WORKBENCH_PANEL_TITLES = WORKBENCH_PANELS.reduce((titles, panel) => {
  titles[panel.id] = panel.title
  return titles
}, {
  topology: 'ROS 通信拓扑图'
})

export const createFullscreenState = () => WORKBENCH_PANELS
  .filter(panel => panel.fullscreen)
  .reduce((state, panel) => {
    state[panel.id] = false
    return state
  }, { topology: false })

export const createDragPanels = () => WORKBENCH_PANELS.map(panel => ({
  id: panel.id,
  title: panel.title,
  x: panel.drag.x,
  y: panel.drag.y,
  width: panel.drag.width,
  height: panel.drag.height,
  minimized: false,
  fullscreen: false,
  zoomLevel: 1.0,
  originalWidth: panel.drag.width,
  originalHeight: panel.drag.height,
  dragOrder: 0
}))
