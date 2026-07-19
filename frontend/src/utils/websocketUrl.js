const browserBaseUrl = (location) => {
  if (location?.origin) return location.origin
  const protocol = location?.protocol || 'http:'
  const authority = location?.host || location?.hostname || 'localhost'
  return `${protocol}//${authority}`
}

export const createApiBaseUrl = (location, explicitBackendUrl = '') => {
  const explicit = String(explicitBackendUrl || '').trim()
  if (!explicit) return '/api/v1'

  const url = new URL(explicit, browserBaseUrl(location))
  if (url.protocol === 'ws:') url.protocol = 'http:'
  if (url.protocol === 'wss:') url.protocol = 'https:'
  url.pathname = `${url.pathname.replace(/\/$/, '')}/api/v1`
  url.search = ''
  url.hash = ''
  return url.toString().replace(/\/$/, '')
}

export const createWebSocketUrl = (location, explicitBackendUrl = '') => {
  const protocol = location?.protocol === 'https:' ? 'wss:' : 'ws:'
  const hostname = location?.hostname || 'localhost'
  const sameOriginAuthority = location?.host || hostname
  const explicit = String(explicitBackendUrl || '').trim()

  if (!explicit) return `${protocol}//${sameOriginAuthority}/ws`

  const url = new URL(explicit, `${protocol}//${sameOriginAuthority}`)
  url.protocol = url.protocol === 'https:' || url.protocol === 'wss:' ? 'wss:' : 'ws:'
  url.pathname = `${url.pathname.replace(/\/$/, '')}/ws`
  url.search = ''
  url.hash = ''
  return url.toString()
}
