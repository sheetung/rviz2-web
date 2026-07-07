<template>
  <div class="topic-config-panel">
    <div class="control-section">
      <h4>话题控制</h4>
      <div class="control-item">
        <label>Fixed Frame:</label>
        <el-input
          v-model="fixedFrame"
          placeholder="map"
          size="small"
          @change="updateFixedFrame"
        />
      </div>

      <div class="topic-add-row">
        <el-select
          v-model="newDisplayTopic"
          filterable
          allow-create
          default-first-option
          placeholder="选择或输入话题"
          size="small"
          class="topic-select"
          @change="onNewDisplayTopicChange"
        >
          <el-option
            v-for="topic in availableTopics"
            :key="topic.name"
            :label="`${topic.name} (${topic.messageType})`"
            :value="topic.name"
          />
        </el-select>
        <el-select
          v-model="newDisplayType"
          filterable
          allow-create
          default-first-option
          placeholder="消息类型"
          size="small"
          class="type-select"
        >
          <el-option
            v-for="type in messageTypeOptions"
            :key="type"
            :label="type"
            :value="type"
          />
        </el-select>
        <el-button size="small" type="primary" @click="addDisplayTopic">增加</el-button>
      </div>

      <div class="display-topic-list">
        <div
          v-for="display in displayTopics"
          :key="display.id"
          class="display-topic-item"
          :class="{ disabled: !display.visible }"
        >
          <el-checkbox v-model="display.visible" @change="toggleDisplayTopic(display)" />
          <el-select
            v-model="display.name"
            filterable
            allow-create
            default-first-option
            size="small"
            class="display-topic-name"
            @focus="rememberDisplayName(display)"
            @change="updateDisplayTopic(display)"
          >
            <el-option
              v-for="topic in availableTopics"
              :key="topic.name"
              :label="topic.name"
              :value="topic.name"
            />
          </el-select>
          <el-select
            v-model="display.messageType"
            filterable
            allow-create
            default-first-option
            size="small"
            class="display-topic-type"
            @change="updateDisplayTopic(display)"
          >
            <el-option
              v-for="type in messageTypeOptions"
              :key="type"
              :label="type"
              :value="type"
            />
          </el-select>
          <el-button size="small" type="danger" text @click="removeDisplayTopic(display)">删除</el-button>
        </div>
      </div>
    </div>

    <div class="control-section">
      <h4>配置文件</h4>
      <div class="config-row">
        <el-input v-model="configName" placeholder="default.rvizweb" size="small" />
        <el-button size="small" type="primary" @click="saveConfig">保存</el-button>
      </div>
      <div class="config-row">
        <el-select v-model="selectedConfigName" placeholder="选择配置" size="small" class="config-select">
          <el-option v-for="file in configFiles" :key="file" :label="file" :value="file" />
        </el-select>
        <el-button size="small" @click="loadSelectedConfig">读取</el-button>
        <el-button size="small" type="danger" text @click="deleteSelectedConfig">删除</el-button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useRosbridge } from '../../composables/useRosbridge'
import { ROS_TOPICS } from '../../config/rosTopics'
import { configApi } from '../../services/api'

export default {
  name: 'TopicConfigPanel',
  props: {
    settingsSnapshot: {
      type: Object,
      default: () => ({})
    }
  },
  emits: [
    'laser-type-change',
    'laser2d-change',
    'pointcloud-change',
    'map-topic-change',
    'odom-topic-change',
    'settings-update',
    'display-topic-change',
    'fixed-frame-change'
  ],
  setup(props, { emit }) {
    const rosbridge = useRosbridge()
    const availableTopics = ref([])
    const fixedFrame = ref('map')
    const configName = ref('default.rvizweb')
    const selectedConfigName = ref('default.rvizweb')
    const configFiles = ref([])
    const newDisplayTopic = ref('')
    const newDisplayType = ref('sensor_msgs/msg/PointCloud2')
    const messageTypeOptions = [
      'sensor_msgs/msg/PointCloud2',
      'sensor_msgs/msg/LaserScan',
      'nav_msgs/msg/Odometry',
      'nav_msgs/msg/Path',
      'visualization_msgs/msg/Marker',
      'visualization_msgs/msg/MarkerArray',
      'geometry_msgs/msg/PoseStamped',
      'geometry_msgs/msg/PoseWithCovarianceStamped',
      'nav_msgs/msg/OccupancyGrid'
    ]

    let displayIdCounter = 0
    const createDisplayTopic = (name, messageType, visible = true) => ({
      id: `display_${++displayIdCounter}`,
      name,
      messageType,
      visible,
      previousName: name
    })
    const createDefaultDisplayTopics = () => [
      createDisplayTopic(ROS_TOPICS.pointCloud, 'sensor_msgs/msg/PointCloud2'),
      createDisplayTopic(ROS_TOPICS.odom, 'nav_msgs/msg/Odometry'),
      createDisplayTopic(ROS_TOPICS.goalMarker, 'visualization_msgs/msg/MarkerArray'),
      createDisplayTopic(ROS_TOPICS.path, 'nav_msgs/msg/Path'),
      createDisplayTopic(ROS_TOPICS.inflatedMap, 'sensor_msgs/msg/PointCloud2')
    ].filter(display => display.name)
    const displayTopics = ref(createDefaultDisplayTopics())

    const loadAvailableTopics = async () => {
      try {
        const [topicList, topicTypes] = await Promise.all([
          rosbridge.getTopics(),
          rosbridge.getTopicTypes()
        ])
        availableTopics.value = topicList.map(topicInfo => {
          const topicName = typeof topicInfo === 'string' ? topicInfo : topicInfo.name
          return {
            name: topicName,
            messageType: topicTypes[topicName] || 'unknown'
          }
        })
      } catch (error) {
        console.error('加载主题列表失败:', error)
      }
    }

    const updateFixedFrame = () => {
      emit('fixed-frame-change', fixedFrame.value || 'map')
    }

    const emitDisplayTopicChange = (action, display, extra = {}) => {
      emit('display-topic-change', {
        action,
        display: {
          name: display.name,
          messageType: display.messageType,
          visible: display.visible
        },
        ...extra
      })
    }

    const onNewDisplayTopicChange = (topicName) => {
      const found = availableTopics.value.find(topic => topic.name === topicName)
      if (found && found.messageType && found.messageType !== 'unknown') {
        newDisplayType.value = found.messageType
      }
    }

    const addDisplayTopic = () => {
      if (!newDisplayTopic.value || !newDisplayType.value) {
        ElMessage.warning('请选择话题和消息类型')
        return
      }
      const existing = displayTopics.value.find(display => display.name === newDisplayTopic.value)
      if (existing) {
        existing.visible = true
        existing.messageType = newDisplayType.value
        emitDisplayTopicChange('update', existing, { oldName: existing.previousName || existing.name })
        existing.previousName = existing.name
        return
      }
      const display = createDisplayTopic(newDisplayTopic.value, newDisplayType.value, true)
      displayTopics.value.push(display)
      emitDisplayTopicChange('add', display)
      newDisplayTopic.value = ''
    }

    const rememberDisplayName = (display) => {
      display.previousName = display.name
    }

    const updateDisplayTopic = (display) => {
      if (!display.name || !display.messageType) return
      emitDisplayTopicChange('update', display, { oldName: display.previousName || display.name })
      display.previousName = display.name
    }

    const toggleDisplayTopic = (display) => {
      emitDisplayTopicChange(display.visible ? 'show' : 'hide', display)
    }

    const removeDisplayTopic = (display) => {
      displayTopics.value = displayTopics.value.filter(item => item.id !== display.id)
      emitDisplayTopicChange('remove', display)
    }

    const applyDisplayTopics = () => {
      displayTopics.value.forEach(display => {
        emitDisplayTopicChange(display.visible ? 'add' : 'hide', display)
      })
    }

    const buildConfig = () => ({
      ...props.settingsSnapshot,
      fixedFrame: fixedFrame.value || 'map',
      displays: displayTopics.value.map(display => ({
        name: display.name,
        messageType: display.messageType,
        visible: display.visible
      }))
    })

    const normalizeConfigName = (name) => {
      const trimmed = (name || 'default.rvizweb').trim()
      const withoutOldSuffix = trimmed.endsWith('.rviz') ? trimmed.slice(0, -5) : trimmed
      return withoutOldSuffix.endsWith('.rvizweb') ? withoutOldSuffix : `${withoutOldSuffix}.rvizweb`
    }

    const loadConfigFiles = async () => {
      try {
        configFiles.value = await configApi.listConfigs()
      } catch (error) {
        console.warn('Failed to load config list:', error)
      }
    }

    const applyConfig = (config) => {
      const cfg = config || {}
      displayTopics.value.forEach(display => emitDisplayTopicChange('remove', display))

      fixedFrame.value = cfg.fixedFrame || 'map'
      updateFixedFrame()

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

      const displays = Array.isArray(cfg.displays) && cfg.displays.length > 0
        ? cfg.displays
        : createDefaultDisplayTopics()
      displayTopics.value = displays
        .filter(display => display.name && display.messageType)
        .map(display => createDisplayTopic(display.name, display.messageType, display.visible !== false))
      applyDisplayTopics()
    }

    const saveConfig = async () => {
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
      } else {
        updateFixedFrame()
        applyDisplayTopics()
      }
    }

    onMounted(async () => {
      await loadAvailableTopics()
      await loadDefaultConfig()
    })

    return {
      availableTopics,
      fixedFrame,
      displayTopics,
      newDisplayTopic,
      newDisplayType,
      messageTypeOptions,
      configName,
      selectedConfigName,
      configFiles,
      updateFixedFrame,
      onNewDisplayTopicChange,
      addDisplayTopic,
      rememberDisplayName,
      updateDisplayTopic,
      toggleDisplayTopic,
      removeDisplayTopic,
      saveConfig,
      loadSelectedConfig,
      deleteSelectedConfig
    }
  }
}
</script>

<style scoped>
.topic-config-panel {
  height: 100%;
  overflow-y: auto;
  padding: 16px;
  background: rgba(15, 23, 42, 0.4);
  border-radius: 8px;
}

.control-item {
  margin-bottom: 16px;
}

.control-item label {
  display: block;
  margin-bottom: 8px;
  color: #cbd5e1;
  font-size: 12px;
  font-weight: 500;
}

.topic-add-row,
.config-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}

.topic-select,
.config-select {
  flex: 1;
  min-width: 160px;
}

.type-select {
  width: 210px;
}

.display-topic-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.display-topic-item {
  display: grid;
  grid-template-columns: 24px minmax(120px, 1fr) minmax(150px, 0.9fr) auto;
  align-items: center;
  gap: 8px;
  padding: 8px;
  background: rgba(15, 23, 42, 0.3);
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 6px;
}

.display-topic-item.disabled {
  opacity: 0.58;
}

.display-topic-name,
.display-topic-type {
  min-width: 0;
}

@media (max-width: 1280px) {
  .display-topic-item {
    grid-template-columns: 24px minmax(0, 1fr);
  }

  .display-topic-type {
    grid-column: 2;
  }
}

:deep(.el-checkbox) {
  color: #cbd5e1 !important;
  margin-right: 0;
}

:deep(.el-select .el-input__wrapper),
:deep(.el-input__wrapper) {
  background-color: rgba(15, 23, 42, 0.6) !important;
  border-color: rgba(148, 163, 184, 0.3) !important;
}

:deep(.el-input__inner) {
  color: #e2e8f0 !important;
}

:deep(.el-button) {
  border-color: rgba(148, 163, 184, 0.3) !important;
}
</style>
