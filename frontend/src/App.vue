<template>
  <div id="app">
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

    onMounted(() => {
      connectionStore.initializeConnection()
    })

    onUnmounted(() => {
      connectionStore.disconnect()
    })

    return { appTitle }
  }
}
</script>

<style>
:root {
  --bg-app: #0d1117;
  --bg-surface: #0f141a;
  --bg-panel: #151b22;
  --bg-header: #1c232b;
  --bg-elevated: #111820;
  --bg-input: #121820;
  --border: #2d3742;
  --border-strong: #425161;
  --border-muted: #27313d;
  --text-primary: #e5edf5;
  --text-secondary: #9aa8b5;
  --text-muted: #8292a3;
  --accent: #46bdf0;
  --accent-strong: #00d4ff;
  --accent-soft: #172532;
  --success: #3dd68c;
  --warning: #f0b429;
  --danger: #f07178;
  --info: #74b9ff;
  --radius: 6px;
  --radius-sm: 4px;
  --header-h: 48px;
  --panel-header-h: 30px;
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --handle: #33404c;
  --handle-hover: #5c7a95;
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.25);
  --scrollbar-thumb: #3a4652;
  --bg-hover: #24303a;
  --bg-active: #1a232c;
  --accent-dark: #1782a8;
  --accent-mid: #1b95c0;
  --accent-glow: #9ee7ff;
  --text-inverse: #ffffff;
  --bg-subtle: rgba(148, 163, 184, 0.1);
  --border-subtle: rgba(148, 163, 184, 0.15);
  --radius-md: 6px;

  --el-color-primary: var(--accent-strong);
  --el-color-success: var(--success);
  --el-color-warning: var(--warning);
  --el-color-danger: var(--danger);
  --el-color-info: var(--info);

  --el-bg-color: var(--bg-panel);
  --el-bg-color-page: var(--bg-app);
  --el-bg-color-overlay: var(--bg-header);

  --el-text-color-primary: var(--text-primary);
  --el-text-color-regular: var(--text-primary);
  --el-text-color-secondary: var(--text-secondary);
  --el-text-color-placeholder: var(--text-muted);

  --el-border-color: var(--border);
  --el-border-color-light: var(--border-muted);
  --el-border-color-lighter: var(--border-muted);
  --el-border-color-extra-light: var(--border-muted);
  --el-border-radius-base: var(--radius-sm);
  --el-fill-color-blank: var(--bg-input);
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html,
body {
  font-family: 'Segoe UI', 'Microsoft YaHei', -apple-system, BlinkMacSystemFont, sans-serif;
  background: var(--bg-app);
  color: var(--text-primary);
  overflow: auto;
}

#app {
  height: 100vh;
  background: var(--bg-app);
  position: relative;
}

.app-header {
  height: var(--header-h);
  background: var(--bg-elevated);
  border-bottom: 1px solid var(--border-muted);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--space-5);
  position: relative;
  z-index: 100;
}

.header-left {
  display: flex;
  align-items: center;
}

.app-logo {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.logo-icon {
  width: 28px;
  height: 28px;
  background: var(--accent-soft);
  border: 1px solid var(--border-strong);
  border-radius: var(--radius);
  position: relative;
}

.logo-icon::before {
  content: '';
  position: absolute;
  top: 5px;
  left: 5px;
  right: 5px;
  bottom: 5px;
  border: 2px solid var(--accent);
  border-radius: 3px;
}

.logo-icon::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 6px;
  height: 6px;
  background: var(--accent-glow);
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
  color: var(--text-primary);
  line-height: 1;
}

.app-subtitle {
  color: var(--text-muted);
  font-size: 11px;
  line-height: 1;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

.app-content {
  height: calc(100vh - var(--header-h));
  position: relative;
  z-index: 2;
  overflow: auto;
}

::-webkit-scrollbar {
  width: 10px;
  height: 10px;
}

::-webkit-scrollbar-track {
  background: var(--bg-elevated);
  border-radius: var(--radius);
}

::-webkit-scrollbar-thumb {
  background: var(--scrollbar-thumb);
  border-radius: 999px;
  border: 2px solid transparent;
  background-clip: content-box;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--handle-hover);
  background-clip: content-box;
}

::-webkit-scrollbar-corner {
  background: var(--bg-elevated);
}

.el-card {
  background: var(--bg-panel) !important;
  border: 1px solid var(--border) !important;
  box-shadow: none !important;
}

.el-button {
  --el-button-bg-color: var(--bg-header);
  --el-button-border-color: var(--border);
  --el-button-text-color: var(--text-primary);
  --el-button-hover-bg-color: var(--bg-hover);
  --el-button-hover-border-color: var(--border-strong);
  --el-button-hover-text-color: var(--text-primary);
  --el-button-active-bg-color: var(--bg-active);
  --el-button-active-border-color: var(--border-strong);
}

.el-button--primary {
  --el-button-bg-color: var(--accent-dark);
  --el-button-border-color: var(--accent-mid);
  --el-button-text-color: var(--text-inverse);
  --el-button-hover-bg-color: var(--accent-mid);
  --el-button-hover-border-color: var(--accent);
  --el-button-hover-text-color: var(--text-inverse);
  --el-button-active-bg-color: #147296;
  --el-button-active-border-color: #147296;
}

.el-button--success {
  --el-button-bg-color: #1f8a5b;
  --el-button-border-color: #27a36c;
  --el-button-hover-bg-color: #27a36c;
  --el-button-hover-border-color: var(--success);
}

.el-input__wrapper {
  background: var(--bg-input) !important;
  border: 1px solid var(--border) !important;
  box-shadow: none !important;
}

.el-input__wrapper:hover,
.el-input__wrapper.is-focus {
  border-color: var(--border-strong) !important;
}

.el-select .el-input__wrapper {
  background: var(--bg-input) !important;
}

.el-popper.is-light,
.el-popper {
  background: var(--bg-header) !important;
  border: 1px solid var(--border) !important;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35) !important;
  color: var(--text-primary) !important;
}

.el-dropdown-menu {
  background: var(--bg-header) !important;
  border: 1px solid var(--border) !important;
}

.el-dropdown-menu__item {
  color: var(--text-primary) !important;
}

.el-dropdown-menu__item:not(.is-disabled):hover {
  background: var(--bg-hover) !important;
  color: var(--accent) !important;
}
</style>
