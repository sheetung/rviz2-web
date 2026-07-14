<template>
  <section
    ref="overlayRef"
    class="rtsp-video-overlay"
    :class="{ 'is-ready': isReady }"
    :style="overlayStyle"
    @pointerdown.stop
    @mousedown.stop
    @click.stop
  >
    <div class="video-actions">
      <button
        type="button"
        title="编辑网络流地址"
        aria-label="编辑网络流地址"
        @pointerdown.stop
        @click.stop="$emit('edit')"
      >
        <el-icon><Edit /></el-icon>
      </button>
      <button
        type="button"
        title="重新连接"
        aria-label="重新连接"
        @pointerdown.stop
        @click.stop="$emit('reconnect')"
      >
        <el-icon><Refresh /></el-icon>
      </button>
      <button
        type="button"
        title="关闭视频"
        aria-label="关闭视频"
        @pointerdown.stop
        @click.stop="$emit('close')"
      >
        <el-icon><Close /></el-icon>
      </button>
    </div>

    <div class="video-content" @pointerdown="startDrag">
      <img
        :src="streamUrl"
        alt="RTSP 相机实时视频"
        draggable="false"
        @load="onStreamLoaded"
        @error="onStreamError"
      />
    </div>

    <span
      class="resize-handle resize-bottom-left"
      title="拖动调整大小"
      @pointerdown.stop="startResize($event, 'bottom-left')"
    ></span>
    <span
      class="resize-handle resize-bottom-right"
      title="拖动调整大小"
      @pointerdown.stop="startResize($event, 'bottom-right')"
    ></span>
  </section>
</template>

<script>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { Close, Edit, Refresh } from '@element-plus/icons-vue'

const DEFAULT_WIDTH = 360
const DEFAULT_HEIGHT = 240
const MIN_WIDTH = 240
const MIN_HEIGHT = 160
const EDGE_GAP = 14

export default {
  name: 'RtspVideoOverlay',
  components: { Close, Edit, Refresh },
  props: {
    streamUrl: {
      type: String,
      required: true
    },
    layoutConfig: {
      type: Object,
      default: () => ({})
    }
  },
  emits: ['close', 'edit', 'reconnect', 'ready', 'stream-error', 'layout-change'],
  setup(props, { emit, expose }) {
    const overlayRef = ref(null)
    const x = ref(0)
    const y = ref(0)
    const width = ref(DEFAULT_WIDTH)
    const height = ref(DEFAULT_HEIGHT)
    const isReady = ref(false)
    let interaction = null
    let parentResizeObserver = null

    const overlayStyle = computed(() => ({
      left: `${x.value}px`,
      top: `${y.value}px`,
      width: `${width.value}px`,
      height: `${height.value}px`
    }))

    const parentBounds = () => {
      const parent = overlayRef.value?.parentElement
      return {
        width: parent?.clientWidth || window.innerWidth,
        height: parent?.clientHeight || window.innerHeight
      }
    }

    const clampLayout = () => {
      const bounds = parentBounds()
      const minWidth = Math.min(MIN_WIDTH, bounds.width)
      const minHeight = Math.min(MIN_HEIGHT, bounds.height)
      width.value = Math.max(minWidth, Math.min(width.value, bounds.width))
      height.value = Math.max(minHeight, Math.min(height.value, bounds.height))
      x.value = Math.max(0, Math.min(x.value, bounds.width - width.value))
      y.value = Math.max(0, Math.min(y.value, bounds.height - height.value))
    }

    const placeAtBottomRight = () => {
      const bounds = parentBounds()
      width.value = Math.min(DEFAULT_WIDTH, Math.max(MIN_WIDTH, bounds.width - EDGE_GAP * 2))
      height.value = Math.min(DEFAULT_HEIGHT, Math.max(MIN_HEIGHT, bounds.height - EDGE_GAP * 2))
      x.value = bounds.width - width.value - EDGE_GAP
      y.value = bounds.height - height.value - EDGE_GAP
      clampLayout()
    }

    const getLayout = () => ({
      x: Math.round(x.value),
      y: Math.round(y.value),
      width: Math.round(width.value),
      height: Math.round(height.value)
    })

    const applyConfiguredLayout = (layout = {}) => {
      const configuredWidth = Number(layout.width)
      const configuredHeight = Number(layout.height)
      const configuredX = Number(layout.x)
      const configuredY = Number(layout.y)
      width.value = Number.isFinite(configuredWidth) ? configuredWidth : DEFAULT_WIDTH
      height.value = Number.isFinite(configuredHeight) ? configuredHeight : DEFAULT_HEIGHT
      if (layout.x !== null && layout.x !== undefined && Number.isFinite(configuredX)
        && layout.y !== null && layout.y !== undefined && Number.isFinite(configuredY)) {
        x.value = configuredX
        y.value = configuredY
        clampLayout()
      } else {
        placeAtBottomRight()
      }
    }

    const stopInteraction = () => {
      const layoutChanged = Boolean(interaction)
      interaction = null
      window.removeEventListener('pointermove', handlePointerMove)
      window.removeEventListener('pointerup', stopInteraction)
      window.removeEventListener('pointercancel', stopInteraction)
      document.body.style.userSelect = ''
      document.body.style.cursor = ''
      if (layoutChanged) emit('layout-change', getLayout())
    }

    const beginInteraction = (event, type, direction = '') => {
      if (event.button !== 0) return
      event.preventDefault()
      interaction = {
        type,
        direction,
        pointerX: event.clientX,
        pointerY: event.clientY,
        x: x.value,
        y: y.value,
        width: width.value,
        height: height.value
      }
      window.addEventListener('pointermove', handlePointerMove)
      window.addEventListener('pointerup', stopInteraction)
      window.addEventListener('pointercancel', stopInteraction)
      document.body.style.userSelect = 'none'
      document.body.style.cursor = type === 'drag'
        ? 'grabbing'
        : direction === 'bottom-left' ? 'nesw-resize' : 'nwse-resize'
    }

    const startDrag = (event) => {
      if (event.target.closest('.video-actions')) return
      beginInteraction(event, 'drag')
    }

    const startResize = (event, direction) => {
      beginInteraction(event, 'resize', direction)
    }

    function handlePointerMove(event) {
      if (!interaction) return
      event.preventDefault()
      const bounds = parentBounds()
      const deltaX = event.clientX - interaction.pointerX
      const deltaY = event.clientY - interaction.pointerY

      if (interaction.type === 'drag') {
        x.value = interaction.x + deltaX
        y.value = interaction.y + deltaY
        clampLayout()
        return
      }

      const maxHeight = Math.max(MIN_HEIGHT, bounds.height - interaction.y)
      height.value = Math.max(
        Math.min(MIN_HEIGHT, bounds.height),
        Math.min(interaction.height + deltaY, maxHeight)
      )

      if (interaction.direction === 'bottom-left') {
        const rightEdge = interaction.x + interaction.width
        const maxWidth = Math.max(MIN_WIDTH, rightEdge)
        width.value = Math.max(
          Math.min(MIN_WIDTH, bounds.width),
          Math.min(interaction.width - deltaX, maxWidth)
        )
        x.value = rightEdge - width.value
      } else {
        const maxWidth = Math.max(MIN_WIDTH, bounds.width - interaction.x)
        width.value = Math.max(
          Math.min(MIN_WIDTH, bounds.width),
          Math.min(interaction.width + deltaX, maxWidth)
        )
      }
      clampLayout()
    }

    const onStreamLoaded = () => {
      isReady.value = true
      emit('ready')
    }

    const onStreamError = () => {
      isReady.value = false
      emit('stream-error')
    }

    onMounted(async () => {
      await nextTick()
      applyConfiguredLayout(props.layoutConfig)
      const parent = overlayRef.value?.parentElement
      if (parent && typeof ResizeObserver !== 'undefined') {
        parentResizeObserver = new ResizeObserver(clampLayout)
        parentResizeObserver.observe(parent)
      }
    })

    watch(
      () => props.streamUrl,
      () => { isReady.value = false }
    )

    watch(
      () => props.layoutConfig,
      (layout) => applyConfiguredLayout(layout),
      { deep: true }
    )

    onBeforeUnmount(() => {
      stopInteraction()
      parentResizeObserver?.disconnect()
    })

    expose({ getLayout })

    return {
      overlayRef,
      overlayStyle,
      isReady,
      startDrag,
      startResize,
      onStreamLoaded,
      onStreamError
    }
  }
}
</script>

<style scoped>
.rtsp-video-overlay {
  position: absolute;
  z-index: 20;
  min-width: 240px;
  min-height: 160px;
  display: flex;
  overflow: hidden;
  opacity: 0;
  pointer-events: none;
  background: transparent;
  transition: opacity 0.16s ease;
}

.rtsp-video-overlay.is-ready {
  opacity: 1;
  pointer-events: auto;
}

.video-actions {
  position: absolute;
  z-index: 5;
  top: 6px;
  right: 6px;
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 2px;
  opacity: 0;
  pointer-events: none;
  border-radius: var(--radius-sm);
  background: rgba(0, 0, 0, 0.58);
  transition: opacity 0.15s ease;
}

.rtsp-video-overlay:hover .video-actions,
.rtsp-video-overlay:focus-within .video-actions {
  opacity: 1;
  pointer-events: auto;
}

.video-actions button {
  width: 24px;
  height: 24px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.78);
  background: transparent;
  border: 0;
  border-radius: var(--radius-sm);
  cursor: pointer;
}

.video-actions button:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.16);
}

.video-content {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  cursor: grab;
  touch-action: none;
}

.video-content:active {
  cursor: grabbing;
}

.video-content img {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: contain;
  pointer-events: none;
  user-select: none;
}

.resize-handle {
  position: absolute;
  bottom: 0;
  z-index: 2;
  width: 18px;
  height: 18px;
  opacity: 0;
  touch-action: none;
  transition: opacity 0.15s ease;
}

.rtsp-video-overlay:hover .resize-handle {
  opacity: 0.72;
}

.resize-bottom-left {
  left: 0;
  cursor: nesw-resize;
}

.resize-bottom-right {
  right: 0;
  cursor: nwse-resize;
}

.resize-bottom-right::after {
  content: '';
  position: absolute;
  right: 3px;
  bottom: 3px;
  width: 8px;
  height: 8px;
  border-right: 2px solid rgba(255, 255, 255, 0.55);
  border-bottom: 2px solid rgba(255, 255, 255, 0.55);
}
</style>
