import assert from 'node:assert/strict'
import test from 'node:test'

import { createPinia, setActivePinia } from 'pinia'

import { useConnectionStore } from '../src/composables/useConnectionStore.js'

test('keeps reconnecting on a fixed interval until explicitly disconnected', async () => {
  const originalWebSocket = globalThis.WebSocket
  const originalSetTimeout = globalThis.setTimeout
  const originalClearTimeout = globalThis.clearTimeout
  const originalWarn = console.warn
  const sockets = []
  const timers = new Map()
  let nextTimerId = 0

  class FakeWebSocket {
    static OPEN = 1

    constructor(url) {
      this.url = url
      this.readyState = 0
      sockets.push(this)
    }

    close() {
      this.readyState = 3
    }
  }

  globalThis.WebSocket = FakeWebSocket
  globalThis.setTimeout = (callback, delay) => {
    const timerId = ++nextTimerId
    timers.set(timerId, { callback, delay })
    return timerId
  }
  globalThis.clearTimeout = (timerId) => timers.delete(timerId)
  console.warn = () => {}

  const runNextTimer = () => {
    const [timerId, timer] = timers.entries().next().value
    timers.delete(timerId)
    timer.callback()
    return timer.delay
  }

  try {
    setActivePinia(createPinia())
    const store = useConnectionStore()
    store.reconnectInterval = 25

    await store.connect()
    assert.equal(sockets.length, 1)

    for (let attempt = 1; attempt <= 7; attempt++) {
      sockets.at(-1).onclose({ code: attempt === 1 ? 1000 : 1006 })
      assert.equal(store.reconnectAttempts, attempt)
      assert.equal(timers.size, 1)
      assert.equal(runNextTimer(), 25)
      assert.equal(sockets.length, attempt + 1)
    }

    sockets.at(-1).onclose({ code: 1006 })
    assert.equal(timers.size, 1)
    store.disconnect()
    assert.equal(timers.size, 0)
    assert.equal(store.reconnectAttempts, 0)
  } finally {
    globalThis.WebSocket = originalWebSocket
    globalThis.setTimeout = originalSetTimeout
    globalThis.clearTimeout = originalClearTimeout
    console.warn = originalWarn
  }
})
