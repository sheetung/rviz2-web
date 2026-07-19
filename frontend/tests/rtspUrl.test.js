import test from 'node:test'
import assert from 'node:assert/strict'

import { sanitizeRtspUrlForStorage } from '../src/utils/rtspUrl.js'

test('RTSP credentials and query tokens are not persisted', () => {
  assert.deepEqual(
    sanitizeRtspUrlForStorage('rtsp://camera:secret@192.168.1.66/live?token=abc'),
    {
      sourceUrl: 'rtsp://192.168.1.66/live',
      containsSecrets: true
    }
  )
})

test('credential-free RTSP URLs remain persistable', () => {
  assert.deepEqual(
    sanitizeRtspUrlForStorage('rtsp://192.168.1.66/live'),
    {
      sourceUrl: 'rtsp://192.168.1.66/live',
      containsSecrets: false
    }
  )
})
