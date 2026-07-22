export const markerLifetimeMilliseconds = (marker) => {
  const seconds = Number(marker?.lifetime?.sec || 0)
  const nanoseconds = Number(marker?.lifetime?.nanosec || 0)
  const lifetime = seconds * 1000 + nanoseconds / 1e6
  return Number.isFinite(lifetime) && lifetime > 0 ? lifetime : 0
}

export const markerTransformTimestamp = (marker, messageTimestamp) => (
  marker?.frame_locked ? null : messageTimestamp
)

export const refreshMarkerGroupTransforms = (group, transformMarker) => {
  let firstError = ''

  group?.children?.forEach((object) => {
    const marker = object.userData?.originalMessage
    if (!marker) return
    const error = transformMarker(marker, object) || ''
    if (!firstError && error) firstError = error
  })

  return firstError
}
