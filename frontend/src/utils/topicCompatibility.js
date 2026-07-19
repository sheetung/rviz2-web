export const normalizeRosMessageType = (messageType = '') => {
  const parts = String(messageType).trim().split('/').filter(Boolean)
  if (parts.length === 2) return `${parts[0]}/msg/${parts[1]}`
  return parts.join('/')
}

export const messageTypesAreCompatible = (left = '', right = '') => {
  const normalizedLeft = normalizeRosMessageType(left)
  const normalizedRight = normalizeRosMessageType(right)
  return Boolean(normalizedLeft && normalizedLeft === normalizedRight)
}

export const topicsMatchingMessageType = (topics = [], messageType = '') => {
  if (!normalizeRosMessageType(messageType)) return [...topics]
  return topics.filter(topic =>
    messageTypesAreCompatible(topic?.messageType, messageType)
  )
}

export const sourceFrameFromMissingTfError = (error = '') => {
  const match = String(error).match(/^缺少\s+(.+?)\s+→\s+(.+?)\s+的 TF$/)
  return match?.[1]?.trim() || ''
}

export const sourceFramesFromDisplayErrors = (displays = []) => {
  return [...new Set(
    displays
      .map(display => sourceFrameFromMissingTfError(display?.error))
      .filter(Boolean)
  )]
}
