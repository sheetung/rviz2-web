import assert from 'node:assert/strict'
import test from 'node:test'

import {
  messageTypesAreCompatible,
  normalizeRosMessageType,
  sourceFrameFromMissingTfError,
  sourceFramesFromDisplayErrors,
  topicsMatchingMessageType
} from '../src/utils/topicCompatibility.js'


test('normalizes canonical and legacy ROS message type names', () => {
  assert.equal(
    normalizeRosMessageType('sensor_msgs/PointCloud2'),
    'sensor_msgs/msg/PointCloud2'
  )
  assert.equal(
    normalizeRosMessageType('sensor_msgs/msg/PointCloud2'),
    'sensor_msgs/msg/PointCloud2'
  )
  assert.equal(
    messageTypesAreCompatible(
      'sensor_msgs/PointCloud2',
      'sensor_msgs/msg/PointCloud2'
    ),
    true
  )
})


test('filters display topic choices to the existing display message type', () => {
  const topics = [
    { name: '/ouster/points', messageType: 'sensor_msgs/msg/PointCloud2' },
    { name: '/mid360/lidar', messageType: 'sensor_msgs/PointCloud2' },
    { name: '/ouster/imu', messageType: 'sensor_msgs/msg/Imu' },
    { name: '/pose', messageType: 'geometry_msgs/msg/PoseStamped' }
  ]

  assert.deepEqual(
    topicsMatchingMessageType(topics, 'sensor_msgs/msg/PointCloud2')
      .map(topic => topic.name),
    ['/ouster/points', '/mid360/lidar']
  )
})


test('extracts the source frame from a missing TF status', () => {
  assert.equal(
    sourceFrameFromMissingTfError('缺少 os_sensor → map 的 TF'),
    'os_sensor'
  )
  assert.equal(sourceFrameFromMissingTfError('点云为空或数据格式无效'), '')
})


test('collects unique source frames from display TF errors', () => {
  assert.deepEqual(
    sourceFramesFromDisplayErrors([
      { error: '缺少 os_sensor → map 的 TF' },
      { error: '缺少 os_sensor → odom 的 TF' },
      { error: '缺少 mid360_frame → map 的 TF' },
      { error: '点云为空或数据格式无效' }
    ]),
    ['os_sensor', 'mid360_frame']
  )
})
