import test from 'node:test'
import assert from 'node:assert/strict'

import { createWebSocketUrl } from '../src/utils/websocketUrl.js'

test('websocket URL uses the configured backend port', () => {
  assert.equal(
    createWebSocketUrl(
      {
        protocol: 'http:',
        hostname: '192.168.1.66',
        host: '192.168.1.66:3000'
      },
      '8099'
    ),
    'ws://192.168.1.66:8099/ws'
  )
})

test('websocket URL uses secure same-origin transport for HTTPS', () => {
  assert.equal(
    createWebSocketUrl(
      {
        protocol: 'https:',
        hostname: 'rviz.example.com',
        host: 'rviz.example.com'
      },
      '8443'
    ),
    'wss://rviz.example.com:8443/ws'
  )
})

test('websocket URL falls back to the page port when no backend port is injected', () => {
  assert.equal(
    createWebSocketUrl(
      {
        protocol: 'http:',
        hostname: 'localhost',
        host: 'localhost:3000'
      },
      ''
    ),
    'ws://localhost:3000/ws'
  )
})
