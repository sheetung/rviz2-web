import { ElMessage } from 'element-plus'

const MESSAGE_DEFAULTS = {
  success: { duration: 2500, showClose: false },
  info: { duration: 3000, showClose: false },
  warning: { duration: 4000, showClose: true },
  error: { duration: 5000, showClose: true }
}

const normalizeMessage = (message, fallback = '') => {
  if (typeof message === 'string') return message.trim() || fallback
  if (message === null || message === undefined) return fallback
  return String(message).trim() || fallback
}

export const getSystemErrorMessage = (error, fallback = '操作失败') => {
  const detail = error?.response?.data?.detail
  if (typeof detail === 'string' && detail.trim()) return detail.trim()
  if (Array.isArray(detail) && detail.length > 0) {
    const messages = detail
      .map(item => item?.msg || item?.message || '')
      .filter(Boolean)
    if (messages.length > 0) return messages.join('；')
  }
  return normalizeMessage(error?.message, fallback)
}

export const createSystemMessage = (adapter, options = {}) => {
  const now = options.now || (() => Date.now())
  const dedupeWindowMs = options.dedupeWindowMs ?? 900
  const recentMessages = new Map()

  const notify = (type, message, messageOptions = {}) => {
    const normalizedType = MESSAGE_DEFAULTS[type] ? type : 'info'
    const text = normalizeMessage(message)
    if (!text) return null

    const {
      dedupe = true,
      dedupeKey: customDedupeKey,
      ...elementOptions
    } = messageOptions
    const dedupeKey = customDedupeKey || `${normalizedType}:${text}`
    const currentTime = now()
    if (dedupe) {
      const previousTime = recentMessages.get(dedupeKey)
      if (previousTime !== undefined && currentTime - previousTime < dedupeWindowMs) {
        return null
      }
      recentMessages.set(dedupeKey, currentTime)
      if (recentMessages.size > 100) {
        const expiry = currentTime - dedupeWindowMs
        recentMessages.forEach((timestamp, key) => {
          if (timestamp < expiry) recentMessages.delete(key)
        })
      }
    }

    const defaults = MESSAGE_DEFAULTS[normalizedType]
    return adapter({
      ...elementOptions,
      type: normalizedType,
      message: text,
      duration: elementOptions.duration ?? defaults.duration,
      showClose: elementOptions.showClose ?? defaults.showClose,
      grouping: elementOptions.grouping ?? true
    })
  }

  const api = {
    notify,
    success: (message, messageOptions) => notify('success', message, messageOptions),
    info: (message, messageOptions) => notify('info', message, messageOptions),
    warning: (message, messageOptions) => notify('warning', message, messageOptions),
    error: (message, messageOptions) => notify('error', message, messageOptions),
    fromError: (error, fallback, messageOptions) => (
      notify('error', getSystemErrorMessage(error, fallback), messageOptions)
    ),
    getErrorMessage: getSystemErrorMessage
  }
  return api
}

export const systemMessage = createSystemMessage(options => ElMessage(options))

export const useSystemMessage = () => systemMessage
