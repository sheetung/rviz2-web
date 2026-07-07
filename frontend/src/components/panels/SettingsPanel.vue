<template>
  <div class="settings-panel">
    <section class="settings-section">
      <div class="section-heading">
        <h4>配置文件</h4>
        <span>.rvizweb</span>
      </div>

      <div class="field-row">
        <label>保存为</label>
        <div class="inline-actions">
          <el-input v-model="configName" placeholder="default.rvizweb" size="small" />
          <el-button size="small" type="primary" @click="saveConfig">保存</el-button>
        </div>
      </div>

      <div class="field-row">
        <label>读取配置</label>
        <div class="inline-actions">
          <el-select v-model="selectedConfigName" placeholder="选择配置" size="small" class="config-select">
            <el-option v-for="file in configFiles" :key="file" :label="file" :value="file" />
          </el-select>
          <el-button size="small" @click="loadSelectedConfig">读取</el-button>
          <el-button size="small" type="danger" text @click="deleteSelectedConfig">删除</el-button>
        </div>
      </div>
    </section>

    <section class="settings-section">
      <div class="section-heading">
        <h4>当前配置</h4>
        <span>预览</span>
      </div>
      <div class="summary-grid">
        <div class="summary-item">
          <span class="summary-label">Fixed Frame</span>
          <span class="summary-value">{{ configSummary.fixedFrame }}</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">Odom</span>
          <span class="summary-value">{{ configSummary.odomTopic || '-' }}</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">PointCloud</span>
          <span class="summary-value">{{ configSummary.pointCloudTopic || '-' }}</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">Display</span>
          <span class="summary-value">{{ displayCount }} 项</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">Grid / Axes</span>
          <span class="summary-value">{{ sceneSummary }}</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">View</span>
          <span class="summary-value">{{ configSummary.viewPreset }}</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">Layout</span>
          <span class="summary-value">{{ layoutSummary }}</span>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { configApi } from '../../services/api'

export default {
  name: 'SettingsPanel',
  props: {
    settingsSnapshot: {
      type: Object,
      default: () => ({})
    },
    displaySnapshot: {
      type: Array,
      default: () => []
    }
  },
  emits: [
    'laser-type-change',
    'laser2d-change',
    'pointcloud-change',
    'map-topic-change',
    'odom-topic-change',
    'settings-update',
    'capture-scene-state',
    'display-config-apply',
    'fixed-frame-change'
  ],
  setup(props, { emit }) {
    const configName = ref('default.rvizweb')
    const selectedConfigName = ref('default.rvizweb')
    const configFiles = ref([])

    const configSummary = computed(() => ({
      fixedFrame: props.settingsSnapshot.fixedFrame || 'map',
      odomTopic: props.settingsSnapshot.position?.odomTopic || '',
      pointCloudTopic: props.settingsSnapshot.laser?.pointCloudTopic || '',
      viewPreset: props.settingsSnapshot.scene?.viewPreset || 'iso'
    }))

    const sceneSummary = computed(() => {
      const scene = props.settingsSnapshot.scene || {}
      const grid = scene.showGrid !== false ? '网格开' : '网格关'
      const axes = scene.showAxes !== false ? '坐标轴开' : '坐标轴关'
      return `${grid} / ${axes}`
    })

    const layoutSummary = computed(() => {
      const sceneWidth = props.settingsSnapshot.layout?.sceneWidth || 68
      const panelCount = Object.keys(props.settingsSnapshot.layout?.panelHeights || {}).length
      return `点云 ${Math.round(sceneWidth)}% / 高度 ${panelCount || 5} 项`
    })

    const displayCount = computed(() => props.displaySnapshot.length)

    const normalizeConfigName = (name) => {
      const trimmed = (name || 'default.rvizweb').trim()
      const withoutOldSuffix = trimmed.endsWith('.rviz') ? trimmed.slice(0, -5) : trimmed
      return withoutOldSuffix.endsWith('.rvizweb') ? withoutOldSuffix : `${withoutOldSuffix}.rvizweb`
    }

    const buildConfig = () => ({
      ...props.settingsSnapshot,
      displays: props.displaySnapshot.map(display => ({
        name: display.name,
        messageType: display.messageType,
        visible: display.visible,
        config: display.config || {}
      }))
    })

    const loadConfigFiles = async () => {
      try {
        configFiles.value = await configApi.listConfigs()
      } catch (error) {
        console.warn('Failed to load config list:', error)
      }
    }

    const applyConfig = (config) => {
      const cfg = config || {}
      emit('fixed-frame-change', cfg.fixedFrame || 'map')

      emit('settings-update', {
        type: 'scene',
        showGrid: cfg.scene?.showGrid !== false,
        showAxes: cfg.scene?.showAxes !== false,
        viewPreset: cfg.scene?.viewPreset || 'iso',
        camera: cfg.scene?.camera || null
      })

      emit('settings-update', {
        type: 'layout',
        sceneWidth: cfg.layout?.sceneWidth || 68,
        panelHeights: cfg.layout?.panelHeights || null
      })

      emit('settings-update', {
        type: 'goal',
        goal: cfg.goal || { x: 0, y: 0, z: 0 }
      })

      if (cfg.position) {
        if (cfg.position.odomTopic) emit('odom-topic-change', cfg.position.odomTopic)
        emit('settings-update', {
          type: 'position',
          showTrajectory: cfg.position.showTrajectory !== false,
          trajectoryLength: cfg.position.trajectoryLength || 100
        })
        emit('settings-update', {
          type: 'trajectory',
          trajectoryLength: cfg.position.trajectoryLength || 100
        })
      }

      if (cfg.laser) {
        if (cfg.laser.laserType) emit('laser-type-change', cfg.laser.laserType)
        if (cfg.laser.laserScanTopic) emit('laser2d-change', cfg.laser.laserScanTopic)
        if (cfg.laser.pointCloudTopic) emit('pointcloud-change', cfg.laser.pointCloudTopic)
        emit('settings-update', {
          type: 'laser',
          showLaserPoints: cfg.laser.showLaserPoints !== false,
          showLaserLines: cfg.laser.showLaserLines !== false,
          showIntensity: !!cfg.laser.showIntensity,
          pointSize: cfg.laser.laserPointSize || 0.15
        })
        emit('settings-update', {
          type: 'pointcloud',
          pointSize: cfg.laser.pointSize || 0.03,
          opacity: cfg.laser.pointOpacity || 0.8,
          showIntensity: !!cfg.laser.showIntensity
        })
      }

      if (cfg.map) {
        if (cfg.map.mapTopic) emit('map-topic-change', cfg.map.mapTopic)
        emit('settings-update', {
          type: 'map',
          showMap: cfg.map.showMap !== false,
          opacity: cfg.map.mapOpacity || 0.8,
          showGrid: !!cfg.map.showMapGrid,
          showOrigin: cfg.map.showMapOrigin !== false
        })
      }

      if (Array.isArray(cfg.displays)) {
        emit('display-config-apply', cfg.displays)
      }
    }

    const saveConfig = async () => {
      emit('capture-scene-state')
      const name = normalizeConfigName(configName.value)
      await configApi.saveConfig(name, buildConfig())
      configName.value = name
      selectedConfigName.value = name
      await loadConfigFiles()
      ElMessage.success(`配置已保存: ${name}`)
    }

    const loadSelectedConfig = async () => {
      if (!selectedConfigName.value) return
      const data = await configApi.getConfig(selectedConfigName.value)
      applyConfig(data.config || data)
      configName.value = data.name || selectedConfigName.value
      ElMessage.success(`配置已读取: ${selectedConfigName.value}`)
    }

    const deleteSelectedConfig = async () => {
      if (!selectedConfigName.value) return
      await configApi.deleteConfig(selectedConfigName.value)
      ElMessage.success(`配置已删除: ${selectedConfigName.value}`)
      selectedConfigName.value = ''
      await loadConfigFiles()
    }

    const loadDefaultConfig = async () => {
      await loadConfigFiles()
      if (configFiles.value.includes('default.rvizweb')) {
        selectedConfigName.value = 'default.rvizweb'
        await loadSelectedConfig()
      }
    }

    onMounted(loadDefaultConfig)

    return {
      configName,
      selectedConfigName,
      configFiles,
      configSummary,
      sceneSummary,
      layoutSummary,
      displayCount,
      saveConfig,
      loadSelectedConfig,
      deleteSelectedConfig
    }
  }
}
</script>

<style scoped>
.settings-panel {
  height: 100%;
  overflow-y: auto;
  padding: 12px;
  background: #101820;
}

.settings-section {
  border: 1px solid #263442;
  background: #111b25;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
}

.section-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.section-heading h4 {
  margin: 0;
  font-size: 13px;
  color: #e0e9f3;
}

.section-heading span {
  color: #7e8fa1;
  font-size: 11px;
}

.field-row {
  display: grid;
  gap: 6px;
  margin-bottom: 12px;
}

.field-row:last-child {
  margin-bottom: 0;
}

.field-row label {
  color: #9fb0c2;
  font-size: 12px;
}

.inline-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.config-select {
  flex: 1;
  min-width: 160px;
}

.summary-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
}

.summary-item {
  display: grid;
  gap: 3px;
  padding: 8px;
  background: #0d141c;
  border: 1px solid #22303d;
  border-radius: 6px;
}

.summary-label {
  color: #748598;
  font-size: 11px;
}

.summary-value {
  color: #dce7f3;
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

:deep(.el-select .el-input__wrapper),
:deep(.el-input__wrapper) {
  background-color: #0d141c !important;
  border-color: #2a3948 !important;
}

:deep(.el-input__inner) {
  color: #dce7f3 !important;
}

:deep(.el-button) {
  border-color: #2a3948 !important;
}
</style>
