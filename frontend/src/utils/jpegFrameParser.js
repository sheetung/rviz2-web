const JPEG_START = [0xff, 0xd8]
const JPEG_END = [0xff, 0xd9]
const DEFAULT_MAX_BUFFER_BYTES = 20 * 1024 * 1024

const appendBytes = (left, right) => {
  if (left.length === 0) return right.slice()
  const combined = new Uint8Array(left.length + right.length)
  combined.set(left)
  combined.set(right, left.length)
  return combined
}

const findMarker = (bytes, marker, offset = 0) => {
  for (let index = offset; index <= bytes.length - marker.length; index += 1) {
    if (bytes[index] === marker[0] && bytes[index + 1] === marker[1]) return index
  }
  return -1
}

export const createJpegFrameParser = (onFrame, options = {}) => {
  const maxBufferBytes = options.maxBufferBytes ?? DEFAULT_MAX_BUFFER_BYTES
  let buffer = new Uint8Array()

  const push = (chunk) => {
    if (!chunk?.length) return 0
    buffer = appendBytes(buffer, chunk)
    let frameCount = 0

    while (buffer.length > 0) {
      const start = findMarker(buffer, JPEG_START)
      if (start < 0) {
        buffer = buffer.slice(Math.max(0, buffer.length - 1))
        break
      }
      if (start > 0) buffer = buffer.slice(start)

      const end = findMarker(buffer, JPEG_END, JPEG_START.length)
      if (end < 0) break

      const frameEnd = end + JPEG_END.length
      onFrame(buffer.slice(0, frameEnd))
      frameCount += 1
      buffer = buffer.slice(frameEnd)
    }

    if (buffer.length > maxBufferBytes) {
      buffer = new Uint8Array()
      throw new Error('JPEG frame exceeds the configured buffer limit')
    }
    return frameCount
  }

  const reset = () => {
    buffer = new Uint8Array()
  }

  return { push, reset }
}
