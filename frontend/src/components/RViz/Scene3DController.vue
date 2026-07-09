<template>
  <div class="scene3d-controller">
    <!-- 地图设置 -->
    <div class="control-section">
      <h4>地图设置</h4>
      <div class="map-controls">
        
        <div class="control-item">
          <label>地图文件:</label>
          <div class="file-controls">
            <el-input
              v-model="mapFilePath"
              placeholder="选择.yaml和.pgm文件（可多选）"
              size="small"
              readonly
            />
            <el-button @click="selectMapFile" size="small" type="primary">
              <el-icon><Folder /></el-icon>
              浏览
            </el-button>
          </div>
          <input
            ref="fileInput"
            type="file"
            accept=".yaml,.yml,.pgm"
            @change="onFileSelected"
            multiple
            style="display: none"
          />
        </div>
        
        <div class="control-item">
          <label>显示设置:</label>
          <div class="map-display-options">
            <div class="setting-toggle">
              <span>地图</span>
              <el-switch v-model="showMap" size="small" @change="updateMapSettings" />
            </div>
            <div class="setting-toggle">
              <span>网格</span>
              <el-switch v-model="showMapGrid" size="small" @change="updateMapSettings" />
            </div>
            <div class="setting-toggle">
              <span>原点</span>
              <el-switch v-model="showMapOrigin" size="small" @change="updateMapSettings" />
            </div>
          </div>
        </div>
        
        <div class="control-item">
          <label>地图透明度:</label>
          <el-slider 
            v-model="mapOpacity" 
            :min="0.1" 
            :max="1" 
            :step="0.1"
            @change="updateMapSettings"
            show-input
            input-size="small"
          />
        </div>
        
        <div class="control-buttons">
          <el-button @click="resetMapView" size="small">
            <el-icon><Refresh /></el-icon>
            重置视图
          </el-button>
          <el-button @click="centerOnMap" size="small" type="success">
            <el-icon><Aim /></el-icon>
            居中显示
          </el-button>
        </div>
      </div>
    </div>

    <!-- 位置信息设置 -->
    <div class="control-section">
      <h4>位置信息</h4>
      <div class="position-controls">
        <div class="control-item">
          <label>里程计主题:</label>
          <el-select 
            v-model="selectedOdomTopic" 
            @change="onOdomTopicChange"
            placeholder="选择里程计主题"
            size="small"
            style="width: 100%"
          >
            <el-option
              v-for="topic in availableOdomTopics"
              :key="topic.name"
              :label="topic.label"
              :value="topic.name"
            />
          </el-select>
        </div>
        
        <div class="control-item">
          <label>显示设置:</label>
          <div class="position-display-options">
            <div class="setting-toggle">
              <span>轨迹</span>
              <el-switch v-model="showTrajectory" size="small" @change="updatePositionSettings" />
            </div>
          </div>
        </div>
        
        <div class="control-item" v-if="showTrajectory">
          <label>轨迹长度:</label>
          <el-slider
            v-model="trajectoryLength"
            :min="10"
            :max="100"
            :step="10"
            @change="updateTrajectorySettings"
            show-input
            input-size="small"
          />
        </div>

        <div class="position-info" v-if="currentPose">
          <div class="info-row">
            <span class="label">位置 X:</span>
            <span class="value">{{ currentPose.position.x.toFixed(3) }}m</span>
          </div>
          <div class="info-row">
            <span class="label">位置 Y:</span>
            <span class="value">{{ currentPose.position.y.toFixed(3) }}m</span>
          </div>
          <div class="info-row">
            <span class="label">航向角:</span>
            <span class="value">{{ currentPose.yaw.toFixed(2) }}°</span>
          </div>
          <div class="info-row">
            <span class="label">线速度:</span>
            <span class="value">{{ currentVelocity.linear.toFixed(3) }}m/s</span>
          </div>
          <div class="info-row">
            <span class="label">角速度:</span>
            <span class="value">{{ currentVelocity.angular.toFixed(3) }}rad/s</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { Refresh, Aim, Folder } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useRosbridge } from '../../composables/useRosbridge'
import { ROS_TOPICS } from '../../config/rosTopics'

export default {
  name: 'Scene3DController',
  components: {
    Refresh, Aim, Folder
  },
  emits: [
    'map-topic-change',
    'map-file-change',
    'odom-topic-change',
    'settings-update',
    'camera-reset',
    'view-preset'
  ],
  setup(props, { emit }) {
    const rosbridge = useRosbridge()
    
    // 引用
    const fileInput = ref(null)
    
    // 地图设置
    const selectedMapTopic = ref('')
    const mapFilePath = ref('')
    const showMap = ref(true)
    const showMapGrid = ref(false)
    const showMapOrigin = ref(true)
    const mapOpacity = ref(0.8)
    
    // 位置信息设置
    const selectedOdomTopic = ref(ROS_TOPICS.odom)
    const showTrajectory = ref(true)
    const trajectoryLength = ref(100)

    // 全局设置
    const showGrid = ref(true)
    const showAxes = ref(true)
    
    // 可用主题列表
    const availableTopics = ref([])
    const availableMapTopics = computed(() =>
      availableTopics.value.filter(topic => 
        topic.messageType.includes('OccupancyGrid')
      ).map(topic => ({
        name: topic.name,
        label: topic.name.split('/').pop() || topic.name,
        messageType: topic.messageType
      }))
    )
    
    const availableOdomTopics = computed(() =>
      availableTopics.value.filter(topic => 
        topic.messageType.includes('Odometry')
      ).map(topic => ({
        name: topic.name,
        label: topic.name.split('/').pop() || topic.name,
        messageType: topic.messageType
      }))
    )

    // 当前状态
    const currentPose = ref(null)
    const currentVelocity = ref({
      linear: 0,
      angular: 0
    })

    const preferTopic = (topics, preferred, currentValue) => {
      if (preferred && topics.some(topic => topic.name === preferred)) {
        return preferred
      }
      return currentValue || (topics[0] && topics[0].name) || ''
    }

    // 方法定义
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

        console.log('加载可用主题:', availableTopics.value)
        // 自动选择 RViz2 默认主题
        selectedOdomTopic.value = preferTopic(availableOdomTopics.value, ROS_TOPICS.odom, selectedOdomTopic.value)
        selectedMapTopic.value = preferTopic(availableMapTopics.value, '', selectedMapTopic.value)

        if (selectedOdomTopic.value) {
          emit('odom-topic-change', selectedOdomTopic.value)
        }

      } catch (error) {
        console.error('加载主题列表失败:', error)
      }
    }

    // 事件处理
    const onMapTopicChange = (topic) => {
      console.log('地图主题切换:', topic)
      emit('map-topic-change', topic)
    }

    const selectMapFile = () => {
      fileInput.value?.click()
    }

    const onFileSelected = (event) => {
      const files = Array.from(event.target.files)
      if (files.length === 0) return

      // 分类文件类型
      const yamlFiles = files.filter(f => f.name.toLowerCase().endsWith('.yaml') || f.name.toLowerCase().endsWith('.yml'))
      const pgmFiles = files.filter(f => f.name.toLowerCase().endsWith('.pgm'))

      if (files.length === 1) {
        // 单文件选择，按原来的逻辑处理
        const file = files[0]
        mapFilePath.value = file.name
        emit('map-file-change', file)
        ElMessage.success(`已选择地图文件: ${file.name}`)
      } else if (yamlFiles.length === 1 && pgmFiles.length === 1) {
        // 同时选择了YAML和PGM文件
        const yamlFile = yamlFiles[0]
        const pgmFile = pgmFiles[0]

        mapFilePath.value = `${yamlFile.name} + ${pgmFile.name}`
        emit('map-files-change', { yamlFile, pgmFile })
        ElMessage.success(`已选择地图文件对: ${yamlFile.name} + ${pgmFile.name}`)
      } else {
        // 多文件但不是正确的组合
        ElMessage.warning('请选择一个YAML文件和一个PGM文件，或单独选择一个文件')
      }
    }

    const onOdomTopicChange = (topic) => {
      console.log('里程计主题切换:', topic)
      emit('odom-topic-change', topic)
      subscribeToOdom(topic)
    }

    const subscribeToOdom = (topic) => {
      console.log('订阅里程计数据:', topic)
      rosbridge.subscribe(topic, 'nav_msgs/msg/Odometry', (message) => {
        updatePoseFromOdom(message)
      })
    }

    const updatePoseFromOdom = (odomMessage) => {
      if (odomMessage.pose && odomMessage.pose.pose) {
        const pose = odomMessage.pose.pose
        const position = pose.position
        const orientation = pose.orientation
        
        // 计算航向角 (yaw)
        const yaw = Math.atan2(
          2 * (orientation.w * orientation.z + orientation.x * orientation.y),
          1 - 2 * (orientation.y * orientation.y + orientation.z * orientation.z)
        ) * 180 / Math.PI

        currentPose.value = {
          position: {
            x: position.x,
            y: position.y,
            z: position.z
          },
          yaw: yaw
        }
      }

      if (odomMessage.twist && odomMessage.twist.twist) {
        const twist = odomMessage.twist.twist
        currentVelocity.value = {
          linear: Math.sqrt(
            twist.linear.x * twist.linear.x +
            twist.linear.y * twist.linear.y +
            twist.linear.z * twist.linear.z
          ),
          angular: twist.angular.z
        }
      }
    }

    // 设置更新
    const updateMapSettings = () => {
      emit('settings-update', {
        type: 'map',
        showMap: showMap.value,
        opacity: mapOpacity.value,
        showGrid: showMapGrid.value,
        showOrigin: showMapOrigin.value
      })
    }

    const updatePositionSettings = () => {
      emit('settings-update', {
        type: 'position',
        showTrajectory: showTrajectory.value,
        trajectoryLength: trajectoryLength.value
      })
    }

    const updateTrajectorySettings = () => {
      // 统一使用 trajectoryLength 字段名，便于场景侧消费
      emit('settings-update', {
        type: 'trajectory',
        trajectoryLength: Math.max(10, Math.min(100, trajectoryLength.value))
      })
    }

    // 场景控制
    const resetMapView = () => {
      emit('settings-update', { type: 'map', action: 'reset' })
    }

    const centerOnMap = () => {
      emit('settings-update', { type: 'map', action: 'center' })
    }

    watch(() => selectedOdomTopic.value, (newTopic) => {
      if (newTopic) {
        onOdomTopicChange(newTopic)
      }
    }, { immediate: true })

    // 生命周期
    onMounted(async () => {
      await loadAvailableTopics()
    })

    return {
      // 引用
      fileInput,
      
      // 地图设置
      selectedMapTopic,
      mapFilePath,
      showMap,
      showMapGrid,
      showMapOrigin,
      mapOpacity,
      
      // 位置设置
      selectedOdomTopic,
      showTrajectory,
      trajectoryLength,
      currentPose,
      currentVelocity,
      
      // 全局设置
      showGrid,
      showAxes,
      
      // 可用主题
      availableMapTopics,
      availableOdomTopics,
      
      // 方法
      onMapTopicChange,
      selectMapFile,
      onFileSelected,
      onOdomTopicChange,
      updateMapSettings,
      updatePositionSettings,
      updateTrajectorySettings,
      resetMapView,
      centerOnMap,
    }
  }
}
</script>

<style scoped>
.scene3d-controller {
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

.display-options,
.position-display-options,
.map-display-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.setting-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 30px;
  padding: 6px 8px;
  background: #0d141c;
  border: 1px solid #22303d;
  border-radius: 6px;
  color: #cbd5e1;
  font-size: 12px;
}

.laser-settings,
.pointcloud-settings {
  background: rgba(15, 23, 42, 0.3);
  padding: 12px;
  border-radius: 6px;
}

.setting-row {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  color: #cbd5e1;
  font-size: 12px;
}

.point-size-row {
  display: grid;
  grid-template-columns: 76px minmax(0, 1fr) 96px;
  gap: 10px;
}

.point-size-input {
  width: 96px;
}

.file-controls {
  display: flex;
  gap: 8px;
  align-items: center;
}

.control-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 12px;
}

.position-info {
  background: rgba(15, 23, 42, 0.3);
  padding: 12px;
  border-radius: 6px;
  margin-top: 12px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.info-row .label {
  color: #94a3b8;
  font-size: 11px;
}

.info-row .value {
  color: #e2e8f0;
  font-size: 11px;
  font-family: monospace;
  font-weight: 600;
}

/* 深色主题覆盖 */
:deep(.el-radio-group) {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

:deep(.el-radio) {
  color: #cbd5e1 !important;
  margin-right: 0;
}

:deep(.el-select .el-input__wrapper) {
  background-color: rgba(15, 23, 42, 0.6) !important;
  border-color: rgba(148, 163, 184, 0.3) !important;
}

:deep(.el-input__wrapper) {
  background-color: rgba(15, 23, 42, 0.6) !important;
  border-color: rgba(148, 163, 184, 0.3) !important;
}

:deep(.el-input__inner) {
  color: #e2e8f0 !important;
}

:deep(.el-slider__runway) {
  background-color: rgba(148, 163, 184, 0.3) !important;
}

:deep(.el-slider__bar) {
  background-color: #409eff !important;
}

:deep(.el-button) {
  border-color: rgba(148, 163, 184, 0.3) !important;
}
</style>
