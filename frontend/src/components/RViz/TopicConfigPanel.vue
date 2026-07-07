<template>
  <div class="topic-config-panel rviz-displays">
    <section class="displays-tree">
      <div class="panel-caption">
        <div>
          <span>Displays</span>
          <span class="caption-subtitle">RViz Web</span>
        </div>
        <span class="caption-count">{{ enabledDisplayCount }}/{{ displayTopics.length }}</span>
      </div>

      <div class="tree-list">
        <div
          class="tree-row global-row"
          :class="{ selected: selectedDisplayId === 'global' }"
          @click="selectDisplay('global')"
        >
          <span class="tree-caret">▾</span>
          <span class="status-dot ok"></span>
          <span class="tree-label">Global Options</span>
          <span class="tree-value">{{ fixedFrame || 'map' }}</span>
        </div>

        <div class="property-row global-property">
          <span>Fixed Frame</span>
          <el-input
            v-model="fixedFrame"
            placeholder="map"
            size="small"
            @change="updateFixedFrame"
          />
        </div>

        <div class="property-row global-property read-only">
          <span>Frame Rate</span>
          <span>30</span>
        </div>

        <template v-for="display in displayTopics" :key="display.id">
          <div
            class="tree-row display-row"
            :class="{ selected: selectedDisplayId === display.id, disabled: !display.visible }"
            @click="selectDisplay(display.id)"
          >
            <span class="tree-caret">{{ selectedDisplayId === display.id ? '▾' : '▸' }}</span>
            <span class="status-dot" :class="{ ok: display.visible, muted: !display.visible }"></span>
            <span class="display-kind">{{ displayTypeLabel(display.messageType) }}</span>
            <span class="tree-label">{{ displayLabel(display) }}</span>
            <el-button
              class="visibility-button"
              size="small"
              text
              @click.stop="toggleDisplayVisible(display)"
            >
              <el-icon>
                <View v-if="display.visible" />
                <Hide v-else />
              </el-icon>
            </el-button>
          </div>

          <div
            v-if="selectedDisplayId === display.id"
            class="property-row display-property"
            @click.stop
          >
            <span>Enabled</span>
            <el-switch
              v-model="display.visible"
              size="small"
              @change="toggleDisplayTopic(display)"
            />
          </div>

          <div
            v-if="selectedDisplayId === display.id"
            class="property-row display-property"
            @click.stop
          >
            <span>Topic</span>
            <el-select
              v-model="display.name"
              filterable
              allow-create
              default-first-option
              size="small"
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
          </div>

          <div
            v-if="selectedDisplayId === display.id"
            class="property-row display-property"
            @click.stop
          >
            <span>Type</span>
            <el-select
              v-model="display.messageType"
              filterable
              allow-create
              default-first-option
              size="small"
              @change="updateDisplayTopic(display)"
            >
              <el-option
                v-for="type in messageTypeOptions"
                :key="type"
                :label="type"
                :value="type"
              />
            </el-select>
          </div>

          <div
            v-if="selectedDisplayId === display.id"
            class="property-row display-property read-only"
          >
            <span>Status</span>
            <span>{{ display.visible ? 'OK' : 'Hidden' }}</span>
          </div>
        </template>

        <div v-if="displayTopics.length === 0" class="empty-displays">
          没有显示项
        </div>
      </div>

      <div class="display-actions">
        <el-button size="small" @click="openCreateDialog">
          <el-icon><Plus /></el-icon>
          Add
        </el-button>
        <el-button size="small" :disabled="!selectedDisplay" @click="duplicateSelectedDisplay">
          <el-icon><CopyDocument /></el-icon>
          Duplicate
        </el-button>
        <el-button size="small" :disabled="!selectedDisplay" @click="removeSelectedDisplay">
          <el-icon><Delete /></el-icon>
          Remove
        </el-button>
      </div>
    </section>

    <el-dialog
      v-model="isCreateOpen"
      title="Create visualization"
      width="min(520px, calc(100vw - 32px))"
      append-to-body
      class="rviz-create-dialog"
    >
      <el-tabs v-model="createMode" class="create-tabs">
        <el-tab-pane label="By topic" name="topic">
          <div class="topic-browser">
            <button
              v-for="topic in availableTopics"
              :key="topic.name"
              type="button"
              class="topic-choice"
              :class="{ active: newDisplayTopic === topic.name }"
              @click="selectTopic(topic)"
            >
              <span>{{ topic.name }}</span>
              <small>{{ topic.messageType }}</small>
            </button>
          </div>
        </el-tab-pane>

        <el-tab-pane label="By display type" name="type">
          <div class="display-type-browser">
            <button
              v-for="type in messageTypeOptions"
              :key="type"
              type="button"
              class="type-choice"
              :class="{ active: newDisplayType === type }"
              @click="selectDisplayType(type)"
            >
              <span>{{ displayTypeLabel(type) }}</span>
              <small>{{ type }}</small>
            </button>
          </div>
        </el-tab-pane>
      </el-tabs>

      <div class="create-form">
        <label>
          Topic
          <el-select
            v-model="newDisplayTopic"
            filterable
            allow-create
            default-first-option
            placeholder="选择或输入话题"
            size="small"
            @change="onNewDisplayTopicChange"
          >
            <el-option
              v-for="topic in availableTopics"
              :key="topic.name"
              :label="`${topic.name} (${topic.messageType})`"
              :value="topic.name"
            />
          </el-select>
        </label>
        <label>
          Display Type
          <el-select
            v-model="newDisplayType"
            filterable
            allow-create
            default-first-option
            placeholder="消息类型"
            size="small"
          >
            <el-option
              v-for="type in messageTypeOptions"
              :key="type"
              :label="type"
              :value="type"
            />
          </el-select>
        </label>
      </div>

      <template #footer>
        <el-button size="small" @click="isCreateOpen = false">Cancel</el-button>
        <el-button size="small" type="primary" @click="addDisplayTopic">OK</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { computed, ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, CopyDocument, Delete, View, Hide } from '@element-plus/icons-vue'
import { useRosbridge } from '../../composables/useRosbridge'
import { ROS_TOPICS } from '../../config/rosTopics'

export default {
  name: 'TopicConfigPanel',
  components: {
    Plus,
    CopyDocument,
    Delete,
    View,
    Hide
  },
  props: {
    displays: {
      type: Array,
      default: () => []
    }
  },
  emits: [
    'display-topic-change',
    'fixed-frame-change'
  ],
  setup(props, { emit, expose }) {
    const rosbridge = useRosbridge()
    const availableTopics = ref([])
    const fixedFrame = ref('map')
    const newDisplayTopic = ref('')
    const newDisplayType = ref('sensor_msgs/msg/PointCloud2')
    const selectedDisplayId = ref('global')
    const isCreateOpen = ref(false)
    const createMode = ref('topic')
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
    const displayTopics = ref(props.displays.length > 0
      ? props.displays.map(display => createDisplayTopic(display.name, display.messageType, display.visible !== false))
      : createDefaultDisplayTopics()
    )
    const selectedDisplay = computed(() =>
      displayTopics.value.find(display => display.id === selectedDisplayId.value) || null
    )
    const enabledDisplayCount = computed(() =>
      displayTopics.value.filter(display => display.visible).length
    )

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
        selectedDisplayId.value = existing.id
        isCreateOpen.value = false
        return
      }
      const display = createDisplayTopic(newDisplayTopic.value, newDisplayType.value, true)
      displayTopics.value.push(display)
      emitDisplayTopicChange('add', display)
      selectedDisplayId.value = display.id
      isCreateOpen.value = false
      newDisplayTopic.value = ''
    }

    const openCreateDialog = () => {
      isCreateOpen.value = true
      createMode.value = availableTopics.value.length > 0 ? 'topic' : 'type'
    }

    const selectTopic = (topic) => {
      newDisplayTopic.value = topic.name
      onNewDisplayTopicChange(topic.name)
    }

    const selectDisplayType = (type) => {
      newDisplayType.value = type
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

    const toggleDisplayVisible = (display) => {
      display.visible = !display.visible
      toggleDisplayTopic(display)
    }

    const removeDisplayTopic = (display) => {
      displayTopics.value = displayTopics.value.filter(item => item.id !== display.id)
      emitDisplayTopicChange('remove', display)
      if (selectedDisplayId.value === display.id) {
        selectedDisplayId.value = 'global'
      }
    }

    const removeSelectedDisplay = () => {
      if (selectedDisplay.value) {
        removeDisplayTopic(selectedDisplay.value)
      }
    }

    const duplicateSelectedDisplay = () => {
      if (!selectedDisplay.value) return
      const source = selectedDisplay.value
      const copy = createDisplayTopic(source.name, source.messageType, source.visible)
      displayTopics.value.push(copy)
      emitDisplayTopicChange(copy.visible ? 'add' : 'hide', copy)
      selectedDisplayId.value = copy.id
    }

    const selectDisplay = (id) => {
      selectedDisplayId.value = id
    }

    const displayTypeLabel = (messageType) => {
      const parts = (messageType || '').split('/')
      return parts[parts.length - 1] || 'Display'
    }

    const displayLabel = (display) => {
      return display.name || displayTypeLabel(display.messageType)
    }

    const applyDisplayTopics = () => {
      displayTopics.value.forEach(display => {
        emitDisplayTopicChange(display.visible ? 'add' : 'hide', display)
      })
    }

    const applyDisplays = (displays) => {
      displayTopics.value.forEach(display => emitDisplayTopicChange('remove', display))
      const nextDisplays = Array.isArray(displays) && displays.length > 0
        ? displays
        : createDefaultDisplayTopics()
      displayTopics.value = nextDisplays
        .filter(display => display.name && display.messageType)
        .map(display => createDisplayTopic(display.name, display.messageType, display.visible !== false))
      selectedDisplayId.value = 'global'
      applyDisplayTopics()
    }

    const getDisplays = () => displayTopics.value.map(display => ({
      name: display.name,
      messageType: display.messageType,
      visible: display.visible
    }))

    const setFixedFrameSilently = (frameId) => {
      fixedFrame.value = frameId || 'map'
    }

    const setFixedFrame = (frameId) => {
      fixedFrame.value = frameId || 'map'
      updateFixedFrame()
    }

    expose({ applyDisplays, getDisplays, setFixedFrame, setFixedFrameSilently })

    const loadDefaultConfig = async () => {
      updateFixedFrame()
      applyDisplayTopics()
    }

    onMounted(async () => {
      await loadAvailableTopics()
      await loadDefaultConfig()
    })

    return {
      availableTopics,
      fixedFrame,
      displayTopics,
      selectedDisplay,
      selectedDisplayId,
      enabledDisplayCount,
      isCreateOpen,
      createMode,
      newDisplayTopic,
      newDisplayType,
      messageTypeOptions,
      selectDisplay,
      displayTypeLabel,
      displayLabel,
      updateFixedFrame,
      onNewDisplayTopicChange,
      openCreateDialog,
      selectTopic,
      selectDisplayType,
      addDisplayTopic,
      duplicateSelectedDisplay,
      rememberDisplayName,
      updateDisplayTopic,
      toggleDisplayTopic,
      toggleDisplayVisible,
      removeDisplayTopic,
      removeSelectedDisplay
    }
  }
}
</script>

<style scoped>
.rviz-displays {
  height: 100%;
  overflow-y: auto;
  padding: 0;
  background: #181818;
  color: #d7d7d7;
}

.displays-tree {
  border: 1px solid #3a3a3a;
  background: #202020;
  min-height: 100%;
}

.panel-caption {
  height: 32px;
  padding: 0 9px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(#303030, #262626);
  border-bottom: 1px solid #404040;
  color: #eeeeee;
  font-size: 12px;
  font-weight: 600;
}

.caption-subtitle {
  color: #8f98a3;
  font-size: 10px;
  font-weight: 400;
  margin-left: 8px;
}

.caption-count {
  color: #9a9a9a;
  font-size: 11px;
  font-weight: 400;
}

.tree-list {
  padding: 4px 0;
}

.tree-row {
  display: grid;
  grid-template-columns: 14px 10px 72px minmax(0, 1fr) 28px;
  align-items: center;
  gap: 6px;
  min-height: 28px;
  padding: 0 6px 0 8px;
  border-left: 3px solid transparent;
  cursor: default;
  font-size: 12px;
}

.global-row {
  grid-template-columns: 16px 12px minmax(0, 1fr) auto;
  color: #f0f0f0;
}

.tree-row:hover {
  background: #2a2f36;
}

.tree-row.selected {
  background: #234663;
  border-left-color: #68aee0;
}

.tree-row.disabled {
  color: #7f8790;
}

.tree-caret {
  color: #9aa4ad;
  font-size: 11px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #777;
}

.status-dot.ok {
  background: #42bf79;
}

.status-dot.muted {
  background: #5f6770;
}

.tree-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tree-value,
.display-kind {
  color: #9faab4;
  font-size: 11px;
}

.display-kind {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.visibility-button {
  width: 24px;
  height: 24px;
  padding: 0;
}

.property-row {
  display: grid;
  grid-template-columns: 96px minmax(0, 1fr);
  align-items: center;
  gap: 8px;
  min-height: 30px;
  padding: 3px 8px 3px 50px;
  color: #c8d0d8;
  font-size: 12px;
  border-left: 3px solid transparent;
}

.display-property {
  background: #1a1f25;
  border-left-color: #2a506f;
}

.global-property {
  background: #1d1d1d;
}

.property-row.read-only {
  color: #8d98a3;
}

.empty-displays {
  padding: 24px 12px;
  color: #7f8790;
  font-size: 12px;
  text-align: center;
}

.display-actions {
  display: flex;
  gap: 6px;
  justify-content: flex-start;
  padding: 6px;
  border-top: 1px solid #3a3a3a;
  background: #252525;
}

:deep(.el-switch) {
  --el-switch-on-color: #2fb36d;
  --el-switch-off-color: #5c6570;
}

:deep(.el-select .el-input__wrapper),
:deep(.el-input__wrapper) {
  background-color: #161a1f !important;
  border-color: #3a4652 !important;
  box-shadow: none !important;
}

:deep(.el-input__inner) {
  color: #e2e8f0 !important;
}

:deep(.el-button) {
  background: #303030;
  border-color: #4a4a4a !important;
  color: #d8d8d8;
}

:global(.rviz-create-dialog) {
  --el-dialog-bg-color: #202020;
  --el-dialog-title-font-size: 14px;
  border: 1px solid #4a4a4a;
}

:global(.rviz-create-dialog .el-dialog__header) {
  margin-right: 0;
  padding: 10px 12px;
  background: #2b2b2b;
  border-bottom: 1px solid #3a3a3a;
}

:global(.rviz-create-dialog .el-dialog__title) {
  color: #ededed;
}

:global(.rviz-create-dialog .el-dialog__body) {
  padding: 10px 12px;
  color: #d8d8d8;
}

:global(.rviz-create-dialog .el-dialog__footer) {
  padding: 8px 12px 12px;
}

.topic-browser,
.display-type-browser {
  height: 210px;
  overflow: auto;
  border: 1px solid #3a3a3a;
  background: #171717;
}

.topic-choice,
.type-choice {
  width: 100%;
  min-height: 34px;
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 2px;
  padding: 6px 8px;
  border: 0;
  border-bottom: 1px solid #2d2d2d;
  background: transparent;
  color: #dedede;
  text-align: left;
  cursor: pointer;
}

.topic-choice:hover,
.type-choice:hover {
  background: #2a2f36;
}

.topic-choice.active,
.type-choice.active {
  background: #234663;
}

.topic-choice small,
.type-choice small {
  overflow: hidden;
  color: #98a4af;
  font-size: 11px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.create-form {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 10px;
  margin-top: 10px;
}

.create-form label {
  display: grid;
  gap: 5px;
  color: #aeb8c2;
  font-size: 12px;
}

@media (max-width: 560px) {
  .create-form {
    grid-template-columns: 1fr;
  }
}
</style>
