export const createWebSocketUrl = (location, backendPort) => {
  const protocol = location?.protocol === 'https:' ? 'wss:' : 'ws:'
  const hostname = location?.hostname || 'localhost'
  const port = String(backendPort || '').trim()
  const authority = port ? `${hostname}:${port}` : (location?.host || hostname)
  return `${protocol}//${authority}/ws`
}
