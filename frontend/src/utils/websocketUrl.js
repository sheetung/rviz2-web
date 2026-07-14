export const createWebSocketUrl = (location) => {
  const protocol = location?.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = location?.host || 'localhost'
  return `${protocol}//${host}/ws`
}
