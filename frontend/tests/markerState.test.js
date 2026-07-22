import assert from 'node:assert/strict'
import test from 'node:test'

import {
  markerLifetimeMilliseconds,
  markerTransformTimestamp,
  refreshMarkerGroupTransforms
} from '../src/utils/markerState.js'

test('converts ROS marker lifetime without changing it during TF refresh', () => {
  const marker = { lifetime: { sec: 2, nanosec: 500_000_000 } }

  assert.equal(markerLifetimeMilliseconds(marker), 2500)
  assert.equal(markerLifetimeMilliseconds({}), 0)
})

test('frame-locked markers use the latest TF sample', () => {
  assert.equal(markerTransformTimestamp({ frame_locked: true }, 12_500), null)
  assert.equal(markerTransformTimestamp({ frame_locked: false }, 12_500), 12_500)
})

test('refreshes existing marker objects in place and preserves the first TF error', () => {
  const first = { userData: { originalMessage: { id: 1 } } }
  const second = { userData: { originalMessage: { id: 2 } } }
  const children = [first, second]
  const transformed = []

  const error = refreshMarkerGroupTransforms(
    { children },
    (marker, object) => {
      transformed.push([marker.id, object])
      return marker.id === 1 ? 'missing TF for marker 1' : ''
    }
  )

  assert.equal(error, 'missing TF for marker 1')
  assert.deepEqual(transformed, [[1, first], [2, second]])
  assert.deepEqual(children, [first, second])
})
