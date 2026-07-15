import test from 'node:test'
import assert from 'node:assert/strict'

import { resizeFromTopLeft } from '../src/utils/videoOverlayLayout.js'

const resize = (layout, deltaX, deltaY) => resizeFromTopLeft({
  ...layout,
  aspectRatio: 1.5,
  deltaX,
  deltaY,
  minWidth: 240,
  minHeight: 160
})

test('top-left handle enlarges while keeping the opposite corner fixed', () => {
  const resized = resize({ x: 500, y: 300, width: 360, height: 240 }, -120, -80)

  assert.deepEqual(resized, { x: 380, y: 220, width: 480, height: 320 })
})

test('an enlarged video can be made smaller again', () => {
  const resized = resize({ x: 380, y: 220, width: 480, height: 320 }, 180, 120)

  assert.deepEqual(resized, { x: 560, y: 340, width: 300, height: 200 })
})

test('resize clamps to the minimum dimensions', () => {
  const resized = resize({ x: 500, y: 300, width: 360, height: 240 }, 500, 500)

  assert.deepEqual(resized, { x: 620, y: 380, width: 240, height: 160 })
})
