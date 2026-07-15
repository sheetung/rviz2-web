import test from 'node:test'
import assert from 'node:assert/strict'

import { createJpegFrameParser } from '../src/utils/jpegFrameParser.js'

const bytes = (...values) => new Uint8Array(values)

test('extracts multiple JPEG frames from one MJPEG chunk', () => {
  const frames = []
  const parser = createJpegFrameParser(frame => frames.push([...frame]))

  const count = parser.push(bytes(
    0x2d, 0x2d, 0x66, 0xff, 0xd8, 0x01, 0xff, 0xd9,
    0x0d, 0x0a, 0xff, 0xd8, 0x02, 0x03, 0xff, 0xd9
  ))

  assert.equal(count, 2)
  assert.deepEqual(frames, [
    [0xff, 0xd8, 0x01, 0xff, 0xd9],
    [0xff, 0xd8, 0x02, 0x03, 0xff, 0xd9]
  ])
})

test('keeps split JPEG markers and frames between chunks', () => {
  const frames = []
  const parser = createJpegFrameParser(frame => frames.push([...frame]))

  assert.equal(parser.push(bytes(0x00, 0xff)), 0)
  assert.equal(parser.push(bytes(0xd8, 0x10, 0x11, 0xff)), 0)
  assert.equal(parser.push(bytes(0xd9)), 1)
  assert.deepEqual(frames[0], [0xff, 0xd8, 0x10, 0x11, 0xff, 0xd9])
})

test('reset discards an incomplete frame', () => {
  const frames = []
  const parser = createJpegFrameParser(frame => frames.push([...frame]))

  parser.push(bytes(0xff, 0xd8, 0x01))
  parser.reset()
  parser.push(bytes(0xff, 0xd8, 0x02, 0xff, 0xd9))

  assert.deepEqual(frames, [[0xff, 0xd8, 0x02, 0xff, 0xd9]])
})
