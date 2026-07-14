import test from 'node:test'
import assert from 'node:assert/strict'

import {
  createSystemMessage,
  getSystemErrorMessage
} from '../src/composables/useSystemMessage.js'

test('system messages apply consistent defaults', () => {
  const messages = []
  const service = createSystemMessage(options => messages.push(options))

  service.success('保存成功')
  service.error('连接失败')

  assert.equal(messages[0].type, 'success')
  assert.equal(messages[0].duration, 2500)
  assert.equal(messages[0].showClose, false)
  assert.equal(messages[1].type, 'error')
  assert.equal(messages[1].duration, 5000)
  assert.equal(messages[1].showClose, true)
})

test('duplicate messages are suppressed inside the dedupe window', () => {
  const messages = []
  let currentTime = 1000
  const service = createSystemMessage(
    options => messages.push(options),
    { now: () => currentTime, dedupeWindowMs: 900 }
  )

  service.warning('暂无数据')
  service.warning('暂无数据')
  currentTime += 901
  service.warning('暂无数据')

  assert.equal(messages.length, 2)
})

test('backend and regular errors use one normalization rule', () => {
  assert.equal(
    getSystemErrorMessage({ response: { data: { detail: '相机不可达' } } }, '失败'),
    '相机不可达'
  )
  assert.equal(getSystemErrorMessage(new Error('网络错误'), '失败'), '网络错误')
  assert.equal(getSystemErrorMessage(null, '操作失败'), '操作失败')
})
