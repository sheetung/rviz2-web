const enabled = String(import.meta.env.VITE_DEBUG || '').toLowerCase() === 'true'

export const debugLog = (...args) => {
  if (enabled) console.debug(...args)
}

export const debugWarn = (...args) => {
  if (enabled) console.warn(...args)
}
