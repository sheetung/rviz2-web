import test from 'node:test'
import assert from 'node:assert/strict'
import { createPinia, setActivePinia } from 'pinia'

import { useConfigStatusStore } from '../src/composables/useConfigStatusStore.js'

const createStore = () => {
  setActivePinia(createPinia())
  return useConfigStatusStore()
}

test('loaded configuration starts clean and becomes dirty after a change', () => {
  const store = createStore()
  store.markLoaded('default.rvizweb', { fixedFrame: 'map' }, '2026-07-13T08:00:00Z')

  assert.equal(store.isDirty, false)

  store.updateCurrentConfig({ fixedFrame: 'odom' })
  assert.equal(store.isDirty, true)
})

test('changes made while saving remain dirty after the earlier snapshot is saved', () => {
  const store = createStore()
  store.markLoaded('default.rvizweb', { fixedFrame: 'map' }, '2026-07-13T08:00:00Z')
  const submittedConfig = { fixedFrame: 'odom' }

  store.updateCurrentConfig(submittedConfig)
  store.updateCurrentConfig({ fixedFrame: 'world' })
  store.markSaved('default.rvizweb', submittedConfig, '2026-07-13T08:01:00Z')

  assert.equal(store.isDirty, true)
})

test('deleting the loaded configuration marks the in-memory settings dirty', () => {
  const store = createStore()
  store.markLoaded('default.rvizweb', { fixedFrame: 'map' }, '2026-07-13T08:00:00Z')

  store.markDeleted('default.rvizweb')

  assert.equal(store.currentConfigName, 'default.rvizweb')
  assert.equal(store.isDirty, true)
  assert.equal(store.lastSavedAt, null)
})
