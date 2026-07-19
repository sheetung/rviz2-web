/**
 * API 客户端服务
 * 提供与后端 API 的通信接口
 */

import axios from 'axios'
import { createApiBaseUrl } from '../utils/websocketUrl'

// 创建 axios 实例
const browserLocation = typeof window === 'undefined' ? null : window.location
const api = axios.create({
  baseURL: createApiBaseUrl(
    browserLocation,
    import.meta.env.VITE_BACKEND_PUBLIC_URL
  ),
  timeout: 10000,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json'
  }
})

let authenticationPromise = null

const requestAccessToken = () => {
  if (typeof window === 'undefined') return ''
  return window.prompt('请输入 RVizWeb 访问令牌')?.trim() || ''
}

export const ensureAuthenticated = async () => {
  if (authenticationPromise) return authenticationPromise

  authenticationPromise = (async () => {
    const status = await api.get('/auth/status')
    if (status.authenticated) return true
    if (!status.required) {
      throw new Error('服务仅允许从本机访问')
    }

    const accessToken = requestAccessToken()
    if (!accessToken) throw new Error('未提供访问令牌')
    const result = await api.post('/auth/session', { access_token: accessToken })
    if (!result.authenticated) throw new Error('访问令牌验证失败')
    return true
  })()

  try {
    return await authenticationPromise
  } finally {
    authenticationPromise = null
  }
}

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    console.error('API Error:', error)
    
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
 * RVizWeb config file API
 */
export const configApi = {
  listConfigs: () => api.get('/configs'),
  getConfig: (name) => api.get(`/configs/${encodeURIComponent(name)}`),
  saveConfig: (name, config) => api.post(
    `/configs/${encodeURIComponent(name)}`,
    { name, config }
  ),
  deleteConfig: (name) => api.delete(`/configs/${encodeURIComponent(name)}`)
}

/**
 * RTSP camera video API
 */
export const videoApi = {
  getStatus: () => api.get('/video/status'),
  createSession: (sourceUrl) => api.post(
    '/video/sessions',
    { source_url: sourceUrl },
    { timeout: 35000 }
  ),
  deleteSession: (sessionId) => api.delete(`/video/sessions/${encodeURIComponent(sessionId)}`),
  getStreamUrl: (sessionId) => api.getUri({
    url: `/video/stream/${encodeURIComponent(sessionId)}`,
    params: { t: Date.now() }
  })
}

export default api
