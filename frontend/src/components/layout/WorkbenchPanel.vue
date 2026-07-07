<template>
  <section class="workbench-panel" :class="[panelClass, { fullscreen }]">
    <div v-if="fullscreen" class="fullscreen-exit-btn">
      <el-button size="large" @click="$emit('toggle-fullscreen', id)">
        <el-icon><CloseBold /></el-icon>
        退出全屏
      </el-button>
      <div class="esc-hint">按 ESC 键退出</div>
    </div>

    <header class="workbench-panel-header">
      <h5>{{ title }}</h5>
      <el-button size="small" text @click="$emit('toggle-fullscreen', id)">
        <el-icon>
          <FullScreen v-if="!fullscreen" />
          <CloseBold v-else />
        </el-icon>
      </el-button>
    </header>

    <div class="workbench-panel-content">
      <slot />
    </div>
  </section>
</template>

<script>
import { FullScreen, CloseBold } from '@element-plus/icons-vue'

export default {
  name: 'WorkbenchPanel',
  components: {
    FullScreen,
    CloseBold
  },
  props: {
    id: {
      type: String,
      required: true
    },
    title: {
      type: String,
      required: true
    },
    fullscreen: {
      type: Boolean,
      default: false
    },
    panelClass: {
      type: [String, Array, Object],
      default: ''
    }
  },
  emits: ['toggle-fullscreen']
}
</script>

<style scoped>
.workbench-panel {
  min-width: 200px;
  min-height: 0;
  background: #111821;
  border: 1px solid #27313d;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.24);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
  position: relative;
}

.workbench-panel:hover {
  border-color: #3f5163;
  box-shadow: 0 14px 30px rgba(0, 0, 0, 0.28);
}

.workbench-panel-header {
  height: 30px;
  background: #151e28;
  border-bottom: 1px solid #27313d;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 10px;
}

.workbench-panel-header h5 {
  font-size: 12px;
  font-weight: 600;
  color: #dce7f3;
  margin: 0;
}

.workbench-panel-content {
  height: calc(100% - 30px);
  overflow: auto;
  padding: 8px;
}

.fullscreen {
  position: fixed;
  inset: 0;
  z-index: 9999;
  border-radius: 0;
}

.fullscreen .workbench-panel-content {
  height: calc(100vh - 30px);
}

.fullscreen-exit-btn {
  position: absolute;
  top: 16px;
  right: 16px;
  z-index: 10001;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.esc-hint {
  font-size: 12px;
  color: #9fb0c2;
}
</style>
