/**
 * API 客户端服务
 * 提供与后端 API 的通信接口
 */

import axios from 'axios'

// 创建 axios 实例
const api = axios.create({
  baseURL: '/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

const configWriteHeaders = import.meta.env.VITE_CONFIG_API_TOKEN
  ? { 'X-Config-Token': import.meta.env.VITE_CONFIG_API_TOKEN }
  : {}

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 可以在这里添加认证 token
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    console.error('API Error:', error)
    
    // 处理不同的错误状态
    if (error.response) {
      switch (error.response.status) {
        case 401:
          // 未授权
          break
        case 403:
          // 禁止访问
          break
        case 404:
          // 未找到
          break
        case 500:
          // 服务器错误
          break
        default:
          break
      }
    }
    
    return Promise.reject(error)
  }
)

/**
 * ROS API 接口
 */
export const rosApi = {
  // 获取主题列表
  getTopics: () => api.get('/topics'),
  
  // 获取特定主题信息
  getTopicInfo: (topicName) => api.get('/topic-info', { params: { topic_name: topicName } }),
  
  // 订阅主题
  subscribeTopic: (topicName, messageType) => api.post('/topics/subscribe', {
    topic: topicName,
    message_type: messageType
  }),
  
  // 取消订阅主题
  unsubscribeTopic: (topicName) => api.post('/topics/unsubscribe', {
    topic: topicName
  }),
  
  // 发布消息到主题
  publishMessage: (topicName, messageType, message) => api.post('/topics/publish', {
    topic: topicName,
    message_type: messageType,
    msg: message
  }),
  
  // 获取主题频率
  getTopicFrequencies: () => api.get('/topics/frequencies'),
  
  // 获取节点列表
  getNodes: () => api.get('/nodes'),
  
  // 获取特定节点信息
  getNodeInfo: (nodeName) => api.get(`/nodes/${encodeURIComponent(nodeName)}`),
  
  // 获取系统状态
  getSystemStatus: () => api.get('/status')
}

/**
 * 可视化 API 接口
 */
export const vizApi = {
  // 获取可视化状态
  getVisualizationState: () => api.get('/visualization/state'),
  
  // 更新相机设置
  updateCameraSettings: (settings) => api.post('/visualization/camera', settings),
  
  // 更新渲染设置
  updateRenderSettings: (settings) => api.post('/visualization/render', settings),
  
  // 获取可用插件列表
  getAvailablePlugins: () => api.get('/visualization/plugins'),
  
  // 启用插件
  enablePlugin: (pluginId) => api.post(`/visualization/plugins/${pluginId}/enable`),
  
  // 禁用插件
  disablePlugin: (pluginId) => api.post(`/visualization/plugins/${pluginId}/disable`),
  
  // 添加可视化对象
  addVisualizationObject: (objectData) => api.post('/visualization/objects/add', objectData),
  
  // 移除可视化对象
  removeVisualizationObject: (objectId) => api.delete(`/visualization/objects/${objectId}`)
}

/**
 * 默认导出 API 实例
 */

/**
 * RVizWeb config file API
 */
export const configApi = {
  listConfigs: () => api.get('/configs'),
  getConfig: (name) => api.get(`/configs/${encodeURIComponent(name)}`),
  saveConfig: (name, config) => api.post(
    `/configs/${encodeURIComponent(name)}`,
    { name, config },
    { headers: configWriteHeaders }
  ),
  deleteConfig: (name) => api.delete(
    `/configs/${encodeURIComponent(name)}`,
    { headers: configWriteHeaders }
  )
}

export default api
