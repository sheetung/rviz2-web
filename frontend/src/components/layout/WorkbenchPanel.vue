<template>
  <section class="workbench-panel" :class="panelClass">
    <header class="workbench-panel-header">
      <h5>{{ title }}</h5>
    </header>

    <div class="workbench-panel-content">
      <slot />
    </div>
  </section>
</template>

<script>
export default {
  name: 'WorkbenchPanel',
  props: {
    id: {
      type: String,
      required: true
    },
    title: {
      type: String,
      required: true
    },
    panelClass: {
      type: [String, Array, Object],
      default: ''
    }
  }
}
</script>

<style scoped>
.workbench-panel {
  min-width: 200px;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: #151b22;
  border: 1px solid #2d3742;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: none;
  transition: border-color 0.2s ease;
  position: relative;
}

.workbench-panel:hover {
  border-color: #425161;
}

.workbench-panel-header {
  height: 30px;
  flex: 0 0 30px;
  background: #1c232b;
  border-bottom: 1px solid #2d3742;
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
  flex: 1;
  min-height: 0;
  overflow: auto;
  padding: 8px;
}
</style>
