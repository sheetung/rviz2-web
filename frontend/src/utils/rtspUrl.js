export const sanitizeRtspUrlForStorage = (sourceUrl) => {
  const value = String(sourceUrl || '').trim()
  if (!value) return { sourceUrl: '', containsSecrets: false }

  try {
    const url = new URL(value)
    const containsSecrets = Boolean(
      url.username ||
      url.password ||
      url.search ||
      url.hash
    )
    url.username = ''
    url.password = ''
    url.search = ''
    url.hash = ''
    return {
      sourceUrl: url.toString(),
      containsSecrets
    }
  } catch {
    return { sourceUrl: '', containsSecrets: true }
  }
}
