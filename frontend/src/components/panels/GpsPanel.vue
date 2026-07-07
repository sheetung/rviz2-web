<template>
  <div class="position-panel">
    <div class="odom-selector">
      <span class="label">Odom:</span>
      <el-select
        v-model="selectedOdomTopic"
        filterable
        size="small"
        placeholder="选择 odom 话题"
        @visible-change="onOdomSelectVisibleChange"
        @change="onOdomTopicChange"
      >
        <el-option
          v-for="topic in availableOdomTopics"
          :key="topic.name"
          :label="topic.name"
          :value="topic.name"
        />
      </el-select>
    </div>

    <div class="position-info">
      <div class="info-row">
        <span class="label">X位置:</span>
        <span class="value">{{ positionData.x.toFixed(3) }}m</span>
      </div>
      <div class="info-row">
        <span class="label">Y位置:</span>
        <span class="value">{{ positionData.y.toFixed(3) }}m</span>
      </div>
      <div class="info-row">
        <span class="label">Z位置:</span>
        <span class="value">{{ positionData.z.toFixed(3) }}m</span>
      </div>
      <div class="info-row">
        <span class="label">朝向:</span>
        <span class="value">{{ positionData.yaw.toFixed(1) }}°</span>
      </div>
    </div>

    <div class="position-status">
      <div class="status-indicator" :class="positionStatusClass">
        <div class="status-dot"></div>
        <span>{{ positionStatusText }}</span>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRosbridge } from '../../composables/useRosbridge'
import { useConnectionStore } from '../../composables/useConnectionStore'
import { rosApi } from '../../services/api'

export default {
  name: 'PositionPanel',
  props: {
    currentOdomTopic: {
      type: String,
      default: ''
    }
  },
  emits: ['odom-topic-change'],
  setup(props, { emit }) {
    const rosbridge = useRosbridge()
    const connectionStore = useConnectionStore()
    const selectedOdomTopic = ref(props.currentOdomTopic || '')
    const availableTopics = ref([])
    const isLoadingTopics = ref(false)

    const positionData = ref({
      x: 0.0,
      y: 0.0,
      z: 0.0,
      yaw: 0.0,
      status: 'INACTIVE', // ACTIVE, INACTIVE, NO_DATA
      lastUpdate: null,
      sourceTopic: ''
    })

    const positionStatusClass = computed(() => {
      switch (positionData.value.status) {
        case 'ACTIVE':
          return 'status-active'
        case 'INACTIVE':
          return 'status-inactive'
        case 'NO_DATA':
          return 'status-no-fix'
        default:
          return 'status-inactive'
      }
    })

    const positionStatusText = computed(() => {
      switch (positionData.value.status) {
        case 'ACTIVE':
          return positionData.value.sourceTopic || '位置活跃'
        case 'INACTIVE':
          return '位置不活跃'
        case 'NO_DATA':
          return '无位置数据'
        default:
          return '位置未知状态'
      }
    })

    const subscriptions = []

    const availableOdomTopics = computed(() =>
      availableTopics.value.filter(topic => topic.messageType.includes('Odometry'))
    )

    const toNumber = (value, fallback = 0) => {
      const number = Number(value)
      return Number.isFinite(number) ? number : fallback
    }

    const extractPose = (message, type) => {
      if (type === 'nav_msgs/msg/Odometry') {
        const pose = message.pose || message._pose
        const poseData = pose?.pose || pose?._pose
        return {
          position: poseData?.position || poseData?._position,
          orientation: poseData?.orientation || poseData?._orientation
        }
      }

      if (type === 'geometry_msgs/msg/PoseStamped') {
        const pose = message.pose || message._pose
        return {
          position: pose?.position || pose?._position,
          orientation: pose?.orientation || pose?._orientation
        }
      }

      return { position: null, orientation: null }
    }

    const updatePositionFromMessage = (topic, type, message) => {
      const { position, orientation } = extractPose(message, type)

      if (!position) {
        console.warn('[PositionPanel] Failed to parse position from ' + topic, message)
        return
      }

      positionData.value.x = toNumber(position.x ?? position._x)
      positionData.value.y = toNumber(position.y ?? position._y)
      positionData.value.z = toNumber(position.z ?? position._z)
      positionData.value.status = 'ACTIVE'
      positionData.value.lastUpdate = new Date()
      positionData.value.sourceTopic = topic

      if (orientation) {
        const qx = toNumber(orientation.x ?? orientation._x)
        const qy = toNumber(orientation.y ?? orientation._y)
        const qz = toNumber(orientation.z ?? orientation._z)
        const qw = toNumber(orientation.w ?? orientation._w, 1)
        const yaw = Math.atan2(
          2 * (qw * qz + qx * qy),
          1 - 2 * (qy * qy + qz * qz)
        )
        positionData.value.yaw = yaw * 180 / Math.PI
      } else {
        positionData.value.yaw = 0.0
      }

      if (!updatePositionFromMessage._lastLogTime || Date.now() - updatePositionFromMessage._lastLogTime > 5000) {
        console.log('[PositionPanel] ' + topic + ' position: (' + positionData.value.x.toFixed(3) + ', ' + positionData.value.y.toFixed(3) + ', ' + positionData.value.z.toFixed(3) + ')')
        updatePositionFromMessage._lastLogTime = Date.now()
      }
    }

    const clearPositionSubscriptions = () => {
      subscriptions.forEach(({ topic, subscription }) => {
        try {
          rosbridge.unsubscribe(subscription || topic)
          console.log('[PositionPanel] unsubscribed: ' + topic)
        } catch (e) {
          console.warn('[PositionPanel] failed to unsubscribe ' + topic + ':', e)
        }
      })
      subscriptions.length = 0
    }

    const subscribeToPosition = () => {
      if (!connectionStore.isConnected) {
        positionData.value.status = 'INACTIVE'
        return
      }

      const topic = selectedOdomTopic.value
      if (!topic) {
        positionData.value.status = 'NO_DATA'
        positionData.value.sourceTopic = ''
        return
      }

      if (subscriptions.length > 0) {
        return
      }

      console.log('[PositionPanel] 订阅无人机 odom 位置信息: ' + topic)

      try {
        const type = 'nav_msgs/msg/Odometry'
        const subscription = rosbridge.subscribe(topic, type, (message) => {
          updatePositionFromMessage(topic, type, message)
        })

        if (subscription) {
          subscriptions.push({ topic, subscription })
          console.log('[PositionPanel] subscribed: ' + topic)
        }
      } catch (error) {
        console.warn('[PositionPanel] failed to subscribe ' + topic + ':', error)
      }

      if (subscriptions.length === 0) {
        positionData.value.status = 'NO_DATA'
      }
    }

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
        console.warn('[PositionPanel] HTTP加载话题失败，回退到websocket:', error)
        try {
          const [topicList, topicTypes] = await Promise.all([
            rosbridge.getTopics(),
            rosbridge.getTopicTypes()
          ])
          availableTopics.value = normalizeTopicList(topicList, topicTypes)
        } catch (wsError) {
          console.error('[PositionPanel] 加载话题列表失败:', wsError)
        }
      } finally {
        isLoadingTopics.value = false
      }
    }

    const onOdomSelectVisibleChange = (visible) => {
      if (visible) {
        loadAvailableTopics()
      }
    }

    const onOdomTopicChange = (topic) => {
      selectedOdomTopic.value = topic || ''
      emit('odom-topic-change', selectedOdomTopic.value)
      clearPositionSubscriptions()
      positionData.value.status = selectedOdomTopic.value ? 'NO_DATA' : 'INACTIVE'
      positionData.value.sourceTopic = ''
      subscribeToPosition()
    }

    const stopConnectionWatch = watch(
      () => connectionStore.isConnected,
      (isConnected) => {
        if (isConnected) {
          subscribeToPosition()
        } else {
          clearPositionSubscriptions()
          positionData.value.status = 'INACTIVE'
          positionData.value.sourceTopic = ''
        }
      },
      { immediate: true }
    )

    const stopTopicWatch = watch(
      () => props.currentOdomTopic,
      (topic) => {
        if ((topic || '') === selectedOdomTopic.value) return
        selectedOdomTopic.value = topic || ''
        clearPositionSubscriptions()
        subscribeToPosition()
      }
    )

    onMounted(() => {
      loadAvailableTopics()
    })

    onUnmounted(() => {
      console.log('[PositionPanel] 组件卸载 - 清理所有订阅')
      stopConnectionWatch()
      stopTopicWatch()
      clearPositionSubscriptions()
    })

    return {
      positionData,
      selectedOdomTopic,
      availableOdomTopics,
      positionStatusClass,
      positionStatusText,
      onOdomSelectVisibleChange,
      onOdomTopicChange
    }
  }
}
</script>

<style scoped>
.position-panel {
  padding: 8px 12px;
  font-size: 12px;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.position-info {
  flex: 1;
}

.odom-selector {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 3px;
}

.label {
  color: #666;
  font-weight: 500;
}

.value {
  font-family: monospace;
  font-weight: bold;
  color: #2c3e50;
}

.accuracy-good {
  color: #67c23a;
}

.accuracy-medium {
  color: #e6a23c;
}

.accuracy-poor {
  color: #f56c6c;
}

.position-status {
  margin-top: 8px;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-active .status-dot {
  background: #67c23a;
  box-shadow: 0 0 6px rgba(103, 194, 58, 0.6);
}

.status-inactive .status-dot {
  background: #909399;
}

.status-no-fix .status-dot {
  background: #f56c6c;
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0.3; }
}
</style>
