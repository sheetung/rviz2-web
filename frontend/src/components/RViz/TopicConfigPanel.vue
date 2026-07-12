<template>
  <div class="topic-config-panel rviz-displays">
    <section class="displays-tree">
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

        <div class="property-row global-property">
          <span>Follow Frame</span>
          <el-select
            v-model="followFrame"
            filterable
            placeholder="None"
            size="small"
            @change="updateFollowFrame"
          >
            <el-option label="None" value="" />
            <el-option
              v-for="frameId in selectableFrameIds"
              :key="frameId"
              :label="frameId"
              :value="frameId"
            />
          </el-select>
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
            <span
              class="status-dot"
              :class="{ ok: display.visible && !display.error, error: !!display.error, muted: !display.visible }"
              :title="display.error || (display.visible ? '正常' : '已隐藏')"
            ></span>
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
            <span>Topic</span>
            <el-select
              v-model="display.name"
              filterable
              default-first-option
              size="small"
              @focus="rememberDisplayName(display)"
              @visible-change="onTopicSelectVisibleChange"
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

          <div v-if="selectedDisplayId === display.id && display.error" class="display-error">
            {{ display.error }}
          </div>

          <div
            v-if="selectedDisplayId === display.id && isPointCloudDisplay(display)"
            class="property-row display-property"
            @click.stop
          >
            <span>Point Size</span>
            <div class="display-setting-control">
              <el-slider
                v-model="display.config.pointSize"
                :min="0.01"
                :max="1"
                :step="0.01"
                @input="updateDisplayTopic(display)"
              />
              <el-input-number
                v-model="display.config.pointSize"
                :min="0.01"
                :max="1"
                :step="0.01"
                :precision="2"
                controls-position="right"
                size="small"
                @change="updateDisplayTopic(display)"
              />
            </div>
          </div>

          <div
            v-if="selectedDisplayId === display.id && isPathDisplay(display)"
            class="property-row display-property"
            @click.stop
          >
            <span>Line Width</span>
            <div class="display-setting-control">
              <el-slider
                v-model="display.config.lineWidth"
                :min="1"
                :max="20"
                :step="1"
                @input="updateDisplayTopic(display)"
              />
              <el-input-number
                v-model="display.config.lineWidth"
                :min="1"
                :max="20"
                :step="1"
                controls-position="right"
                size="small"
                @change="updateDisplayTopic(display)"
              />
            </div>
          </div>

          <div
            v-if="selectedDisplayId === display.id && isPathDisplay(display)"
            class="property-row display-property"
            @click.stop
          >
            <span>Color</span>
            <el-color-picker
              v-model="display.config.color"
              size="small"
              @change="updateDisplayTopic(display)"
            />
          </div>

          <div
            v-if="selectedDisplayId === display.id && isMarkerArrayDisplay(display)"
            class="property-row display-property"
            @click.stop
          >
            <span>Color</span>
            <el-color-picker
              v-model="display.config.color"
              clearable
              size="small"
              @change="updateDisplayTopic(display)"
            />
          </div>

          <div
            v-if="selectedDisplayId === display.id && isMarkerArrayDisplay(display)"
            class="property-row display-property"
            @click.stop
          >
            <span>Opacity</span>
            <div class="display-setting-control">
              <el-slider
                v-model="display.config.opacity"
                :min="0"
                :max="1"
                :step="0.05"
                @input="updateDisplayTopic(display)"
              />
              <el-input-number
                v-model="display.config.opacity"
                :min="0"
                :max="1"
                :step="0.05"
                :precision="2"
                controls-position="right"
                size="small"
                @change="updateDisplayTopic(display)"
              />
            </div>
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
      width="min(520px, calc(100vw - 32px))"
      append-to-body
      :show-close="false"
      class="rviz-create-dialog"
    >
      <el-tabs v-model="createMode" class="create-tabs">
        <el-tab-pane label="By topic" name="topic">
          <div class="topic-browser">
            <div class="topic-browser-toolbar">
              <span>{{ availableTopics.length }} topics</span>
              <el-button size="small" text :loading="isLoadingTopics" @click="loadAvailableTopics">
                Refresh
              </el-button>
            </div>
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
            <div v-if="!isLoadingTopics && availableTopics.length === 0" class="empty-topics">
              未读取到 ROS2 话题
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="By display type" name="type">
          <div class="display-type-browser">
            <button
              v-for="type in availableMessageTypes"
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

      <div v-if="createMode === 'type'" class="create-form create-form-single">
        <label>
          Topic
          <el-select
            v-model="newDisplayTopic"
            filterable
            allow-create
            default-first-option
            placeholder="选择或输入话题"
            size="small"
            @visible-change="onTopicSelectVisibleChange"
            @change="onNewDisplayTopicChange"
          >
            <el-option
              v-for="topic in topicsForSelectedType"
              :key="topic.name"
              :label="`${topic.name} (${topic.messageType})`"
              :value="topic.name"
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
import { Plus, CopyDocument, Delete, View, Hide } from '@element-plus/icons-vue'
import { useRosbridge } from '../../composables/useRosbridge'
import { getThemeColor } from '../../utils/theme'
import { rosApi } from '../../services/api'
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
    },
    frameIds: {
      type: Array,
      default: () => []
    }
  },
  emits: [
    'display-topic-change',
    'fixed-frame-change',
    'follow-frame-change'
  ],
  setup(props, { emit, expose }) {
    const rosbridge = useRosbridge()
    const availableTopics = ref([])
    const isLoadingTopics = ref(false)
    const fixedFrame = ref('map')
    const followFrame = ref('')
    const newDisplayTopic = ref('')
    const newDisplayType = ref('')
    const selectedDisplayId = ref('global')
    const isCreateOpen = ref(false)
    const createMode = ref('topic')
    let displayIdCounter = 0
    const isPathMessageType = (messageType = '') => {
      return messageType.includes('Path') || messageType.includes('PositionCommand')
    }

    const createDefaultDisplayConfig = (messageType) => {
      if ((messageType || '').includes('PointCloud2')) {
        return {
          pointSize: 0.03
        }
      }
      if (isPathMessageType(messageType || '')) {
        return {
          lineWidth: 2,
          color: getThemeColor('--axis-y')
        }
      }
      if ((messageType || '').includes('MarkerArray')) {
        return {
          color: '',
          opacity: 1
        }
      }
      return {}
    }

    const normalizeDisplayConfig = (messageType, config = {}) => ({
      ...createDefaultDisplayConfig(messageType),
      ...(config || {})
    })

    const createDisplayTopic = (name, messageType, visible = true, config = {}) => ({
      id: `display_${++displayIdCounter}`,
      name,
      messageType,
      visible,
      previousName: name,
      error: '',
      config: normalizeDisplayConfig(messageType, config)
    })
    const createDefaultDisplayTopics = () => [
      createDisplayTopic(ROS_TOPICS.pointCloud, 'sensor_msgs/msg/PointCloud2'),
      createDisplayTopic(ROS_TOPICS.odom, 'nav_msgs/msg/Odometry'),
      createDisplayTopic(ROS_TOPICS.goalMarker, 'visualization_msgs/msg/MarkerArray'),
      createDisplayTopic(ROS_TOPICS.path, 'nav_msgs/msg/Path'),
      createDisplayTopic(ROS_TOPICS.inflatedMap, 'sensor_msgs/msg/PointCloud2')
    ].filter(display => display.name)
    const displayTopics = ref(props.displays.length > 0
      ? props.displays.map(display => createDisplayTopic(display.name, display.messageType, display.visible !== false, display.config))
      : createDefaultDisplayTopics()
    )
    const selectedDisplay = computed(() =>
      displayTopics.value.find(display => display.id === selectedDisplayId.value) || null
    )
    const topicsForSelectedType = computed(() => {
      if (!newDisplayType.value) return availableTopics.value
      return availableTopics.value.filter(topic => topic.messageType === newDisplayType.value)
    })
    const availableMessageTypes = computed(() => {
      return [...new Set(
        availableTopics.value
          .map(topic => topic.messageType)
          .filter(messageType => messageType && messageType !== 'unknown')
      )].sort((a, b) => a.localeCompare(b))
    })
    const selectableFrameIds = computed(() => [...new Set([
      fixedFrame.value,
      ...props.frameIds
    ].filter(Boolean))].sort((left, right) => left.localeCompare(right)))

    const normalizeTopicList = (topicList = [], topicTypes = {}) => {
      return topicList.map(topicInfo => {
        const topicName = typeof topicInfo === 'string' ? topicInfo : topicInfo.name
        const messageType = typeof topicInfo === 'string'
          ? topicTypes[topicName]
          : (topicInfo.messageType || topicInfo.message_type || topicTypes[topicName])
        return {
          name: topicName,
          messageType: messageType || 'unknown'
        }
      })
        .filter(topic => topic.name)
        .sort((a, b) => a.name.localeCompare(b.name))
    }

    const loadAvailableTopics = async () => {
      if (isLoadingTopics.value) return
      isLoadingTopics.value = true
      try {
        const topicList = await rosApi.getTopics()
        availableTopics.value = normalizeTopicList(topicList)
      } catch (error) {
        console.warn('HTTP 加载主题列表失败，回退到 websocket:', error)
        try {
          const [topicList, topicTypes] = await Promise.all([
            rosbridge.getTopics(),
            rosbridge.getTopicTypes()
          ])
          availableTopics.value = normalizeTopicList(topicList, topicTypes)
        } catch (wsError) {
          console.error('加载主题列表失败:', wsError)
        }
      } finally {
        isLoadingTopics.value = false
        if (!availableMessageTypes.value.includes(newDisplayType.value)) {
          newDisplayType.value = availableMessageTypes.value[0] || ''
          newDisplayTopic.value = ''
        }
      }
    }

    const updateFixedFrame = () => {
      emit('fixed-frame-change', fixedFrame.value || 'map')
    }

    const updateFollowFrame = () => {
      emit('follow-frame-change', followFrame.value || '')
    }

    const emitDisplayTopicChange = (action, display, extra = {}) => {
      emit('display-topic-change', {
        action,
        display: {
          name: display.name,
          messageType: display.messageType,
          visible: display.visible,
          config: normalizeDisplayConfig(display.messageType, display.config)
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
      if (createMode.value === 'topic') {
        const selectedTopic = availableTopics.value.find(topic => topic.name === newDisplayTopic.value)
        if (selectedTopic?.messageType && selectedTopic.messageType !== 'unknown') {
          newDisplayType.value = selectedTopic.messageType
        }
      }
      if (!newDisplayTopic.value || !newDisplayType.value) {
        ElMessage.warning('请选择话题和消息类型')
        return
      }
      const existing = displayTopics.value.find(display => display.name === newDisplayTopic.value)
      if (existing) {
        existing.visible = true
        existing.messageType = newDisplayType.value
        existing.config = normalizeDisplayConfig(existing.messageType, existing.config)
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

    const openCreateDialog = async () => {
      isCreateOpen.value = true
      await loadAvailableTopics()
      createMode.value = availableTopics.value.length > 0 ? 'topic' : 'type'
      if (!availableMessageTypes.value.includes(newDisplayType.value)) {
        newDisplayType.value = availableMessageTypes.value[0] || ''
      }
    }

    const onTopicSelectVisibleChange = (visible) => {
      if (visible) {
        loadAvailableTopics()
      }
    }

    const selectTopic = (topic) => {
      newDisplayTopic.value = topic.name
      onNewDisplayTopicChange(topic.name)
    }

    const selectDisplayType = (type) => {
      newDisplayType.value = type
      const selectedTopic = availableTopics.value.find(topic => topic.name === newDisplayTopic.value)
      if (selectedTopic && selectedTopic.messageType !== type) {
        newDisplayTopic.value = ''
      }
    }

    const rememberDisplayName = (display) => {
      display.previousName = display.name
    }

    const updateDisplayTopic = (display) => {
      const selectedTopic = availableTopics.value.find(topic => topic.name === display.name)
      if (selectedTopic?.messageType && selectedTopic.messageType !== 'unknown') {
        display.messageType = selectedTopic.messageType
      }
      if (!display.name || !display.messageType) return
      display.config = normalizeDisplayConfig(display.messageType, display.config)
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
      const copy = createDisplayTopic(source.name, source.messageType, source.visible, source.config)
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

    const isPointCloudDisplay = (display) => (display.messageType || '').includes('PointCloud2')

    const isPathDisplay = (display) => isPathMessageType(display.messageType || '')

    const isMarkerArrayDisplay = (display) => (display.messageType || '').includes('MarkerArray')

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
        .map(display => createDisplayTopic(display.name, display.messageType, display.visible !== false, display.config))
      selectedDisplayId.value = 'global'
      applyDisplayTopics()
    }

    const getDisplays = () => displayTopics.value.map(display => ({
      name: display.name,
      messageType: display.messageType,
      visible: display.visible,
      config: normalizeDisplayConfig(display.messageType, display.config)
    }))

    const setFixedFrameSilently = (frameId) => {
      fixedFrame.value = frameId || 'map'
    }

    const setFixedFrame = (frameId) => {
      fixedFrame.value = frameId || 'map'
      updateFixedFrame()
    }


    const setFollowFrameSilently = (frameId) => {
      followFrame.value = frameId || ''
    }

    const setDisplayStatus = (topic, error = '') => {
      const display = displayTopics.value.find(item => item.name === topic)
      if (display) display.error = error
    }

    expose({ applyDisplays, getDisplays, setFixedFrame, setFixedFrameSilently, setFollowFrameSilently, setDisplayStatus })

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
      availableMessageTypes,
      fixedFrame,
      followFrame,
      selectableFrameIds,
      displayTopics,
      selectedDisplay,
      topicsForSelectedType,
      selectedDisplayId,
      isCreateOpen,
      isLoadingTopics,
      createMode,
      newDisplayTopic,
      newDisplayType,
      selectDisplay,
      displayTypeLabel,
      displayLabel,
      isPointCloudDisplay,
      isPathDisplay,
      isMarkerArrayDisplay,
      updateFixedFrame,
      updateFollowFrame,
      loadAvailableTopics,
      onNewDisplayTopicChange,
      onTopicSelectVisibleChange,
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
  min-height: 0;
  overflow: hidden;
  padding: 0;
  background: transparent;
  color: var(--text-primary);
}

.displays-tree {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  border: 0;
  background: transparent;
}

.tree-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
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
  color: var(--text-primary);
}

.tree-row:hover {
  background: var(--bg-hover);
}

.tree-row.selected {
  background: var(--accent-soft);
  border-left-color: var(--accent);
}

.tree-row.disabled {
  color: var(--text-muted);
}

.tree-caret {
  color: var(--text-secondary);
  font-size: 11px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--text-muted);
}

.status-dot.ok {
  background: var(--success);
}

.status-dot.muted {
  background: var(--text-muted);
}

.status-dot.error {
  background: var(--danger);
  box-shadow: 0 0 0 2px var(--danger-soft);
}

.display-error {
  margin: 2px 8px 6px 39px;
  color: var(--danger);
  font-size: 11px;
  line-height: 1.35;
  overflow-wrap: anywhere;
}

.tree-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tree-value,
.display-kind {
  color: var(--text-secondary);
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
  color: var(--text-primary);
  font-size: 12px;
  border-left: 3px solid transparent;
}

.display-property {
  background: var(--bg-elevated);
  border-left-color: var(--accent-soft);
}

.global-property {
  background: var(--bg-elevated);
}

.property-row.read-only {
  color: var(--text-muted);
}

.display-setting-control {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 96px;
  gap: 10px;
  align-items: center;
}

.display-setting-control :deep(.el-input-number) {
  width: 96px;
}

.empty-displays {
  padding: 24px 12px;
  color: var(--text-muted);
  font-size: 12px;
  text-align: center;
}

.display-actions {
  flex: 0 0 auto;
  display: flex;
  gap: 6px;
  justify-content: flex-start;
  padding: 6px;
  border-top: 1px solid var(--border);
  background: var(--bg-elevated);
}

:deep(.el-select .el-input__wrapper),
:deep(.el-input__wrapper) {
  background-color: var(--bg-input) !important;
  border-color: var(--scrollbar-thumb) !important;
  box-shadow: none !important;
}

:deep(.el-input__inner) {
  color: var(--text-primary) !important;
}

:deep(.el-button) {
  background: var(--bg-header);
  border-color: var(--border) !important;
  color: var(--text-primary);
}

:global(.rviz-create-dialog) {
  --el-dialog-bg-color: var(--bg-panel);
  --el-dialog-title-font-size: 14px;
  border: 1px solid var(--border);
}

:global(.rviz-create-dialog .el-dialog__header) {
  display: none;
}

:global(.rviz-create-dialog .el-dialog__body) {
  padding: 10px 12px;
  color: var(--text-primary);
}

:global(.rviz-create-dialog .el-dialog__footer) {
  padding: 8px 12px 12px;
}

.topic-browser,
.display-type-browser {
  height: 210px;
  overflow: auto;
  border: 1px solid var(--border);
  background: var(--bg-app);
}

.topic-browser-toolbar {
  position: sticky;
  top: 0;
  z-index: 1;
  min-height: 30px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 8px;
  border-bottom: 1px solid var(--border);
  background: var(--bg-panel);
  color: var(--text-secondary);
  font-size: 12px;
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
  border-bottom: 1px solid var(--border);
  background: transparent;
  color: var(--text-primary);
  text-align: left;
  cursor: pointer;
}

.topic-choice:hover,
.type-choice:hover {
  background: var(--bg-hover);
}

.topic-choice.active,
.type-choice.active {
  background: var(--accent-soft);
}

.topic-choice small,
.type-choice small {
  overflow: hidden;
  color: var(--text-secondary);
  font-size: 11px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.empty-topics {
  padding: 22px 8px;
  color: var(--text-muted);
  font-size: 12px;
  text-align: center;
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
  color: var(--text-secondary);
  font-size: 12px;
}

.create-form-single {
  grid-template-columns: 1fr;
}

@media (max-width: 560px) {
  .create-form {
    grid-template-columns: 1fr;
  }
}
</style>
