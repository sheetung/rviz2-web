import test from 'node:test'
import assert from 'node:assert/strict'

import { createConfigFingerprint } from '../src/utils/configSnapshot.js'

test('config fingerprints ignore object key order', () => {
  const first = { fixedFrame: 'map', scene: { showGrid: true, showAxes: false } }
  const second = { scene: { showAxes: false, showGrid: true }, fixedFrame: 'map' }

  assert.equal(createConfigFingerprint(first), createConfigFingerprint(second))
})

test('config fingerprints detect nested setting changes', () => {
  const saved = { displays: [{ name: '/points', visible: true }] }
  const changed = { displays: [{ name: '/points', visible: false }] }

  assert.notEqual(createConfigFingerprint(saved), createConfigFingerprint(changed))
})

test('config fingerprints detect point cloud render style changes', () => {
  const points = {
    displays: [{ name: '/map', config: { renderStyle: 'points', pointSize: 0.03 } }]
  }
  const boxes = {
    displays: [{ name: '/map', config: { renderStyle: 'boxes', boxSize: 0.1 } }]
  }

  assert.notEqual(createConfigFingerprint(points), createConfigFingerprint(boxes))
})
