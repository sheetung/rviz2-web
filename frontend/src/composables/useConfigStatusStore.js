import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { createConfigFingerprint } from '../utils/configSnapshot'

export const useConfigStatusStore = defineStore('configStatus', () => {
  const currentConfigName = ref('')
  const lastSavedAt = ref(null)
  const currentFingerprint = ref(createConfigFingerprint({}))
  const savedFingerprint = ref(null)
  const configExists = ref(false)

  const isDirty = computed(() => {
    if (!currentConfigName.value) return false
    if (!configExists.value) return true
    return savedFingerprint.value !== null && currentFingerprint.value !== savedFingerprint.value
  })

  const updateCurrentConfig = (config) => {
    currentFingerprint.value = createConfigFingerprint(config)
  }

  const markLoaded = (name, config, modifiedAt) => {
    const fingerprint = createConfigFingerprint(config)
    currentConfigName.value = name || ''
    currentFingerprint.value = fingerprint
    savedFingerprint.value = fingerprint
    configExists.value = true
    lastSavedAt.value = modifiedAt || null
  }

  const markSaved = (name, config, modifiedAt) => {
    currentConfigName.value = name || ''
    savedFingerprint.value = createConfigFingerprint(config)
    configExists.value = true
    lastSavedAt.value = modifiedAt || null
  }

  const markDeleted = (name) => {
    if (name !== currentConfigName.value) return
    configExists.value = false
    lastSavedAt.value = null
  }

  return {
    currentConfigName,
    lastSavedAt,
    isDirty,
    updateCurrentConfig,
    markLoaded,
    markSaved,
    markDeleted
  }
})
