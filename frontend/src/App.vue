<template>
  <div id="app">
    <!-- 顶部状态栏 -->
    <div class="app-header">
      <div class="header-left">
        <div class="app-logo">
          <div class="logo-icon"></div>
          <div class="app-identity">
            <h1 class="app-title">{{ appTitle }}</h1>
            <span class="app-subtitle">ROS2 Workbench</span>
          </div>
        </div>
      </div>
      <div class="header-right">
        <connection-status />
      </div>
    </div>
    
    <!-- 主内容区 -->
    <div class="app-content">
      <router-view />
    </div>
  </div>
</template>

<script>
import { onMounted, onUnmounted } from 'vue'
import ConnectionStatus from './components/common/ConnectionStatus.vue'
import { useConnectionStore } from './composables/useConnectionStore'

export default {
  name: 'App',
  components: {
    ConnectionStatus
  },
  setup() {
    const connectionStore = useConnectionStore()
    const appTitle = String(import.meta.env.VITE_APP_TITLE || 'RVizWeb').trim() || 'RVizWeb'
    
    // 应用启动时初始化连接
    onMounted(() => {
      connectionStore.initializeConnection()
    })
    
    // 应用卸载时清理连接
    onUnmounted(() => {
      connectionStore.disconnect()
    })
    
    return { appTitle }
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  font-family: 'Segoe UI', 'Microsoft YaHei', -apple-system, BlinkMacSystemFont, sans-serif;
  background: #0d1117;
  color: #ffffff;
  overflow: auto;
}

#app {
  height: 100vh;
  background: #0d1117;
  position: relative;
}

.app-header {
  height: 48px;
  background: #111820;
  border-bottom: 1px solid #27313d;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  position: relative;
  z-index: 100;
  box-shadow: none;
}

.header-left {
  display: flex;
  align-items: center;
}

.app-logo {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  width: 28px;
  height: 28px;
  background: #172532;
  border: 1px solid #2f4355;
  border-radius: 6px;
  position: relative;
}

.logo-icon::before {
  content: '';
  position: absolute;
  top: 5px;
  left: 5px;
  right: 5px;
  bottom: 5px;
  border: 2px solid #46bdf0;
  border-radius: 3px;
}

.logo-icon::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 6px;
  height: 6px;
  background: #9ee7ff;
  border-radius: 50%;
  transform: translate(-50%, -50%);
}

.app-identity {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.app-title {
  font-size: 16px;
  font-weight: 600;
  color: #e5edf5;
  line-height: 1;
}

.app-subtitle {
  color: #8292a3;
  font-size: 11px;
  line-height: 1;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

.app-content {
  height: calc(100vh - 48px);
  position: relative;
  z-index: 2;
  overflow: auto;
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 12px;
  height: 12px;
}

::-webkit-scrollbar-track {
  background: rgba(15, 23, 42, 0.5);
  border-radius: 6px;
  margin: 2px;
}

::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.6);
  border-radius: 6px;
  transition: background 0.3s ease;
  border: 2px solid transparent;
  background-clip: content-box;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(59, 130, 246, 0.8);
  background-clip: content-box;
}

::-webkit-scrollbar-thumb:active {
  background: rgba(59, 130, 246, 1.0);
  background-clip: content-box;
}

::-webkit-scrollbar-corner {
  background: rgba(15, 23, 42, 0.5);
}

/* Element Plus 主题定制 */
:root {
  --el-color-primary: #00d4ff;
  --el-color-success: #00ff88;
  --el-color-warning: #ffaa00;
  --el-color-danger: #ff4757;
  --el-color-info: #74b9ff;
  
  --el-bg-color: rgba(15, 23, 42, 0.8);
  --el-bg-color-page: rgba(15, 23, 42, 0.8);
  --el-bg-color-overlay: rgba(15, 23, 42, 0.9);
  
  --el-text-color-primary: #ffffff;
  --el-text-color-regular: #e2e8f0;
  --el-text-color-secondary: #94a3b8;
  --el-text-color-placeholder: #64748b;
  
  --el-border-color: rgba(148, 163, 184, 0.2);
  --el-border-color-light: rgba(148, 163, 184, 0.1);
  --el-border-color-lighter: rgba(148, 163, 184, 0.05);
  --el-border-color-extra-light: rgba(148, 163, 184, 0.03);
}

/* Element Plus 组件样式覆盖 */
.el-card {
  background: rgba(15, 23, 42, 0.6) !important;
  backdrop-filter: blur(10px) !important;
  border: 1px solid rgba(148, 163, 184, 0.1) !important;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2) !important;
}

.el-button {
  backdrop-filter: blur(10px) !important;
}

.el-button--primary {
  background: linear-gradient(45deg, #00d4ff, #0099cc) !important;
  border: none !important;
  box-shadow: 0 2px 10px rgba(0, 212, 255, 0.3) !important;
}

.el-button--success {
  background: linear-gradient(45deg, #00ff88, #00cc66) !important;
  border: none !important;
  box-shadow: 0 2px 10px rgba(0, 255, 136, 0.3) !important;
}

.el-input__wrapper {
  background: rgba(15, 23, 42, 0.6) !important;
  backdrop-filter: blur(10px) !important;
  border: 1px solid rgba(148, 163, 184, 0.2) !important;
  box-shadow: none !important;
}

.el-select .el-input__wrapper {
  background: rgba(15, 23, 42, 0.6) !important;
}

.el-popper {
  background: rgba(15, 23, 42, 0.9) !important;
  backdrop-filter: blur(20px) !important;
  border: 1px solid rgba(148, 163, 184, 0.2) !important;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3) !important;
}
</style>
