import test from 'node:test'
import assert from 'node:assert/strict'

import { createWebSocketUrl } from '../src/utils/websocketUrl.js'

test('websocket URL follows the frontend origin and port', () => {
  assert.equal(
    createWebSocketUrl({ protocol: 'http:', host: '192.168.1.66:3000' }),
    'ws://192.168.1.66:3000/ws'
  )
})

test('websocket URL uses secure same-origin transport for HTTPS', () => {
  assert.equal(
    createWebSocketUrl({ protocol: 'https:', host: 'rviz.example.com' }),
    'wss://rviz.example.com/ws'
  )
})

test('websocket URL has a server-side fallback', () => {
  assert.equal(createWebSocketUrl(null), 'ws://localhost/ws')
})
