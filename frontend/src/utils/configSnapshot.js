const canonicalize = (value) => {
  if (Array.isArray(value)) {
    return value.map(canonicalize)
  }

  if (value && typeof value === 'object') {
    return Object.keys(value)
      .sort()
      .reduce((result, key) => {
        if (value[key] !== undefined) {
          result[key] = canonicalize(value[key])
        }
        return result
      }, {})
  }

  return value
}

export const createConfigFingerprint = (config) => JSON.stringify(canonicalize(config || {}))
