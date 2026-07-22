import assert from 'node:assert/strict'
import test from 'node:test'

import {
  getTopicFrequencyState,
  parseNumericMessageFields,
  supportsDynamicChartFields
} from '../src/utils/chartTopics.js'


test('does not report an unmeasured topic as having no data', () => {
  assert.deepEqual(getTopicFrequencyState(null), {
    frequency: null,
    isActive: false,
    status: '未测量'
  })
  assert.deepEqual(getTopicFrequencyState(0), {
    frequency: 0,
    isActive: false,
    status: '无数据'
  })
  assert.deepEqual(getTopicFrequencyState(12.34), {
    frequency: 12.34,
    isActive: true,
    status: '12.3 Hz'
  })
})


test('accepts PX4 custom messages for dynamic chart field discovery', () => {
  assert.equal(
    supportsDynamicChartFields('px4_msgs/msg/VehicleLocalPosition'),
    true
  )
  assert.equal(supportsDynamicChartFields('sensor_msgs/msg/Image'), false)
})


test('discovers finite numeric fields in a PX4 local position message', () => {
  const fields = parseNumericMessageFields({
    timestamp: 1784695855641740,
    xy_valid: true,
    x: -0.0032550410833209753,
    y: 0.021456271409988403,
    z: 0.003593623172491789,
    delta_xy: [0.013063520193099976, -0.02457532286643982],
    ref_lat: null,
    vxy_max: null
  })

  const fieldPaths = fields.map(field => field.path)
  assert.ok(fieldPaths.includes('x'))
  assert.ok(fieldPaths.includes('y'))
  assert.ok(fieldPaths.includes('z'))
  assert.ok(fieldPaths.includes('xy_valid'))
  assert.ok(fieldPaths.includes('delta_xy_computed_avg'))
  assert.ok(!fieldPaths.includes('ref_lat'))
  assert.ok(!fieldPaths.includes('vxy_max'))
})
