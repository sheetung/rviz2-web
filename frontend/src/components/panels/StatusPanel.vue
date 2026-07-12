<template>
  <div class="status-panel" :class="{ 'status-panel--wide': wide }">
    <div class="status-grid">
      <!-- 连接状态 -->
      <div class="status-item connection" :class="connectionStatusClass">
        <div class="status-icon">
          <el-icon size="20" :color="connectionColor">
            <Link />
          </el-icon>
        </div>
        <div class="status-content">
          <div class="status-label">连接</div>
          <div class="status-value">{{ connectionData.status }}</div>
          <div class="status-extra">{{ connectionData.latency }}ms</div>
        </div>
      </div>
      
      <!-- 运行状态 -->
      <div class="status-item system" :class="systemStatusClass">
        <div class="status-icon">
          <el-icon size="20" :color="systemColor">
            <Setting />
          </el-icon>
        </div>
        <div class="status-content">
          <div class="status-label">系统</div>
          <div class="status-value">CPU {{ formatPercent(systemData.cpuUsage) }}</div>
          <div class="status-extra">
            内存 {{ formatPercent(systemData.memUsage) }} · 温度 {{ formatTemperature(systemData.temperature) }}
          </div>
        </div>
      </div>
      
      <!-- 模式状态 -->
      <div class="status-item mode" :class="modeStatusClass">
        <div class="status-icon">
          <el-icon size="20" :color="modeColor">
            <Monitor />
          </el-icon>
        </div>
        <div class="status-content">
          <div class="status-label">模式</div>
          <div class="status-value">{{ modeData.current }}</div>
          <div class="status-extra">{{ modeData.detail }}</div>
        </div>
      </div>
      
      <!-- 网络状态 -->
      <div class="status-item network" :class="networkStatusClass">
        <div class="status-icon">
          <el-icon size="20" :color="networkColor">
            <Connection />
          </el-icon>
        </div>
        <div class="status-content">
          <div class="status-label">网络</div>
          <div class="status-value">{{ networkData.status }}</div>
          <div class="status-extra">{{ networkData.signal }}%</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { 
  Monitor, 
  Setting,
  Link,
  Connection
} from '@element-plus/icons-vue'
import { useRosbridge } from '../../composables/useRosbridge'
import { useConnectionStore } from '../../composables/useConnectionStore'
import { rosApi } from '../../services/api'

export default {
  name: 'StatusPanel',
  components: {
    Monitor,
    Setting,
    Link,
    Connection
  },

  props: {

    compact: {

      type: Boolean,

      default: false

    },

    wide: {

      type: Boolean,

      default: false

    }

  },

  setup() {
    const rosbridge = useRosbridge()
    const connectionStore = useConnectionStore()
    
    // 状态数据
    const connectionData = ref({
      status: '已连接',
      latency: 25,
      quality: 'GOOD',
      packetsLost: 0
    })
    
    const systemData = ref({
      status: '运行中',
      uptime: '02:15:30',
      cpuUsage: 45,
      memUsage: 67,
      temperature: 42.5
    })
    
    const modeData = ref({
      current: '可视化',
      detail: '数据展示',
      mode: 'VIZ',
      subMode: 'DISPLAY'
    })
    
    const networkData = ref({
      status: '良好',
      signal: 85,
      bandwidth: '100 Mbps'
    })
    
    // 连接相关计算属性
    const connectionStatusClass = computed(() => {
      switch (connectionData.value.quality) {
        case 'GOOD': return 'status-good'
        case 'POOR': return 'status-warning'
        case 'DISCONNECTED': return 'status-critical'
        default: return 'status-inactive'
      }
    })
    
    const connectionColor = computed(() => {
      switch (connectionData.value.quality) {
        case 'GOOD': return 'var(--success)'
        case 'POOR': return 'var(--warning)'
        case 'DISCONNECTED': return 'var(--danger)'
        default: return 'var(--text-muted)'
      }
    })
    
    // 系统相关计算属性
    const systemStatusClass = computed(() => {
      const cpu = systemData.value.cpuUsage
      const mem = systemData.value.memUsage
      const temp = systemData.value.temperature
      
      if (cpu > 80 || mem > 80 || temp > 60) return 'status-critical'
      if (cpu > 60 || mem > 60 || temp > 50) return 'status-warning'
      return 'status-good'
    })
    
    const systemColor = computed(() => {
      const cpu = systemData.value.cpuUsage
      const mem = systemData.value.memUsage
      const temp = systemData.value.temperature
      
      if (cpu > 80 || mem > 80 || temp > 60) return 'var(--danger)'
      if (cpu > 60 || mem > 60 || temp > 50) return 'var(--warning)'
      return 'var(--success)'
    })
    
    // 模式相关计算属性
    const modeStatusClass = computed(() => {
      switch (modeData.value.mode) {
        case 'VIZ': return 'status-good'
        case 'DEBUG': return 'status-warning'
        case 'ERROR': return 'status-critical'
        default: return 'status-inactive'
      }
    })
    
    const modeColor = computed(() => {
      switch (modeData.value.mode) {
        case 'VIZ': return 'var(--success)'
        case 'DEBUG': return 'var(--warning)'
        case 'ERROR': return 'var(--danger)'
        default: return 'var(--text-muted)'
      }
    })
    
    // 网络相关计算属性
    const networkStatusClass = computed(() => {
      const signal = networkData.value.signal
      if (signal > 70) return 'status-good'
      if (signal > 40) return 'status-warning'
      return 'status-critical'
    })
    
    const networkColor = computed(() => {
      const signal = networkData.value.signal
      if (signal > 70) return 'var(--success)'
      if (signal > 40) return 'var(--warning)'
      return 'var(--danger)'
    })
    
    // 订阅状态相关主题
    let subscriptions = []
    let systemStatusTimer = null

    const toNumber = (value, fallback = 0) => {
      const number = Number(value)
      return Number.isFinite(number) ? number : fallback
    }

    const updateSystemMetrics = (statusData = {}) => {
      if (statusData.cpu_usage !== undefined) {
        systemData.value.cpuUsage = toNumber(statusData.cpu_usage)
      }
      if (statusData.memory_usage !== undefined) {
        systemData.value.memUsage = toNumber(statusData.memory_usage)
      }
      if (statusData.mem_usage !== undefined) {
        systemData.value.memUsage = toNumber(statusData.mem_usage)
      }
      if (statusData.cpu_temperature !== undefined) {
        systemData.value.temperature = statusData.cpu_temperature === null
          ? null
          : toNumber(statusData.cpu_temperature, null)
      }
      if (statusData.temperature !== undefined) {
        systemData.value.temperature = statusData.temperature === null
          ? null
          : toNumber(statusData.temperature, null)
      }
    }

    const fetchSystemStatus = async () => {
      try {
        const statusData = await rosApi.getSystemStatus()
        updateSystemMetrics(statusData)
      } catch (error) {
        console.warn('Failed to fetch system status:', error)
      }
    }
    
    const subscribeToStatus = () => {
      // 诊断信息
      subscriptions.push(rosbridge.subscribe('/diagnostics', 'diagnostic_msgs/msg/DiagnosticArray', (message) => {
        if (message.status && message.status.length > 0) {
          message.status.forEach(status => {
            if (status.level >= 2) {
              systemData.value.status = '异常'
            } else if (status.level === 1 && systemData.value.status !== '异常') {
              systemData.value.status = '警告'
            }
          })
        }
      }))
      
      // 系统状态
      subscriptions.push(rosbridge.subscribe('/system_status', 'std_msgs/msg/String', (message) => {
        try {
          const statusData = JSON.parse(message.data)
          updateSystemMetrics(statusData)
        } catch (error) {
          console.warn('Failed to parse system status:', error)
        }
      }))
    }
    
    // 实时运行时间追踪
    let uptimeTimer = null
    let connectionStatusTimer = null
    const startTime = Date.now()
    
    const startUptimeTracking = () => {
      uptimeTimer = setInterval(() => {
        const uptime = Date.now() - startTime
        const hours = Math.floor(uptime / 3600000)
        const minutes = Math.floor((uptime % 3600000) / 60000)
        const seconds = Math.floor((uptime % 60000) / 1000)
        
        systemData.value.uptime = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
      }, 1000)
    }
    
    // 监听连接状态
    const updateConnectionStatus = () => {
      if (connectionStore.isConnected) {
        connectionData.value.status = '已连接'
        connectionData.value.quality = 'GOOD'
      } else {
        connectionData.value.status = '未连接'
        connectionData.value.quality = 'DISCONNECTED'
        connectionData.value.latency = 0
      }
    }

    const formatPercent = (value) => {
      return `${Math.round(toNumber(value))}%`
    }

    const formatTemperature = (value) => {
      if (value === null || value === undefined || Number.isNaN(Number(value))) {
        return '--'
      }
      return `${Number(value).toFixed(1)}°C`
    }
    
    onMounted(() => {
      console.log('StatusPanel mounted - 使用真实ROS数据')
      subscribeToStatus()
      updateConnectionStatus()
      fetchSystemStatus()
      startUptimeTracking()
      
      // 监听连接状态变化
      connectionStatusTimer = setInterval(updateConnectionStatus, 5000)
      systemStatusTimer = setInterval(fetchSystemStatus, 3000)
    })
    
    onUnmounted(() => {
      subscriptions.forEach(subscription => {
        if (subscription) {
          rosbridge.unsubscribe(subscription)
        }
      })
      
      if (uptimeTimer) {
        clearInterval(uptimeTimer)
      }

      if (connectionStatusTimer) {
        clearInterval(connectionStatusTimer)
      }

      if (systemStatusTimer) {
        clearInterval(systemStatusTimer)
      }
    })
    
    return {
      connectionData,
      systemData,
      modeData,
      networkData,
      connectionStatusClass,
      connectionColor,
      systemStatusClass,
      systemColor,
      modeStatusClass,
      modeColor,
      networkStatusClass,
      networkColor,
      formatPercent,
      formatTemperature
    }
  }
}
</script>

<style scoped>
.status-panel {
  padding: 8px;
  font-size: 12px;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.status-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  flex: 1;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px;
  border-radius: 6px;
  border: 1px solid var(--border-subtle);
  background: var(--bg-subtle);
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
}

.status-item.status-good {
  border-color: var(--success);
  background: rgba(61, 214, 140, 0.1);
}

.status-item.status-warning {
  border-color: var(--warning);
  background: rgba(240, 180, 41, 0.1);
}

.status-item.status-critical {
  border-color: var(--danger);
  background: rgba(240, 113, 120, 0.1);
}

.status-item.status-inactive {
  border-color: var(--text-muted);
  background: rgba(130, 146, 163, 0.1);
  opacity: 0.7;
}

.status-icon {
  flex-shrink: 0;
}

.status-content {
  flex: 1;
  min-width: 0;
}

.status-label {
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 2px;
}

.status-value {
  font-weight: bold;
  color: var(--text-primary);
  font-size: 13px;
}

.status-extra {
  color: var(--text-secondary);
  font-size: 10px;
  margin-top: 1px;
}

.status-panel--wide {
  padding: 0;
  height: auto;
  display: block;
  align-items: center;
}

.status-panel--wide .status-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
  flex: none;
  min-width: 0;
}

.status-panel--wide .status-item {
  min-width: 0;
  padding: 7px 10px;
}

.status-panel--wide .status-icon {
  display: flex;
}

.status-panel--wide .status-label {
  color: var(--text-secondary);
}

.status-panel--wide .status-value {
  font-weight: 700;
  line-height: 1.2;
}

@media (max-width: 1100px) {
  .status-panel--wide .status-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .status-panel--wide .status-grid {
    grid-template-columns: 1fr;
  }
}
</style>
