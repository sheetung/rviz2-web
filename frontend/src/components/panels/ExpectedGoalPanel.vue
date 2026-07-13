<template>
  <div class="expected-goal-panel">
    <div class="goal-grid">
      <label>
        X
        <el-input-number
          v-model="localGoal.x"
          size="small"
          :step="0.1"
          :precision="2"
          controls-position="right"
          @input="emitGoalUpdate"
          @change="emitGoalUpdate"
        />
      </label>
      <label>
        Y
        <el-input-number
          v-model="localGoal.y"
          size="small"
          :step="0.1"
          :precision="2"
          controls-position="right"
          @input="emitGoalUpdate"
          @change="emitGoalUpdate"
        />
      </label>
      <label>
        Z
        <el-input-number
          v-model="localGoal.z"
          size="small"
          :step="0.1"
          :precision="2"
          controls-position="right"
          @input="emitGoalUpdate"
          @change="emitGoalUpdate"
        />
      </label>
    </div>

    <div class="goal-meta">
      <span class="meta-label">Topic</span>
      <el-input
        v-model="localGoal.topic"
        size="small"
        placeholder="目标话题"
        @change="emitGoalUpdate"
      />
      <span class="meta-sep"></span>
      <span class="meta-label">Frame</span>
      <strong>{{ fixedFrame || 'map' }}</strong>
      <span class="meta-sep"></span>
      <span class="meta-label">方向</span>
      <strong>+X</strong>
    </div>

    <div class="goal-actions">
      <el-button size="small" @click="resetGoal">重置</el-button>
      <el-button size="small" @click="previewGoal">展示</el-button>
      <el-button size="small" type="primary" @click="publishGoal">
        发布
      </el-button>
    </div>
  </div>
</template>

<script>
import { computed, reactive, watch } from 'vue'

const createDefaultGoal = () => ({
  topic: '',
  x: 0,
  y: 0,
  z: 0
})

const normalizeGoal = (goal) => ({
  topic: typeof goal?.topic === 'string' ? goal.topic.trim() : '',
  x: Number(goal?.x) || 0,
  y: Number(goal?.y) || 0,
  z: Number(goal?.z) || 0
})

export default {
  name: 'ExpectedGoalPanel',
  props: {
    goal: {
      type: Object,
      default: () => createDefaultGoal()
    },
    fixedFrame: {
      type: String,
      default: 'map'
    }
  },
  emits: ['goal-update', 'goal-preview', 'goal-publish'],
  setup(props, { emit }) {
    const localGoal = reactive(createDefaultGoal())
    const normalizedGoal = computed(() => normalizeGoal(localGoal))

    const syncFromProps = () => {
      const nextGoal = normalizeGoal(props.goal)
      localGoal.topic = nextGoal.topic
      localGoal.x = nextGoal.x
      localGoal.y = nextGoal.y
      localGoal.z = nextGoal.z
    }

    const emitGoalUpdate = () => {
      emit('goal-update', normalizedGoal.value)
    }

    const previewGoal = () => {
      const goal = normalizeGoal(localGoal)
      emit('goal-update', goal)
      emit('goal-preview', goal)
    }

    const publishGoal = () => {
      const goal = normalizeGoal(localGoal)
      emit('goal-update', goal)
      emit('goal-publish', goal)
    }

    const resetGoal = () => {
      localGoal.topic = ''
      localGoal.x = 0
      localGoal.y = 0
      localGoal.z = 0
      emitGoalUpdate()
    }

    watch(() => props.goal, syncFromProps, { deep: true, immediate: true })

    return {
      localGoal,
      normalizedGoal,
      emitGoalUpdate,
      previewGoal,
      publishGoal,
      resetGoal
    }
  }
}
</script>

<style scoped>
.expected-goal-panel {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 10px;
  background: var(--bg-elevated);
}

.goal-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.goal-grid label {
  display: grid;
  gap: 5px;
  color: var(--text-secondary);
  font-size: 12px;
}

.goal-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 8px;
  border: 1px solid var(--border-muted);
  border-radius: var(--radius-sm);
  background: var(--bg-input);
  color: var(--text-secondary);
  font-size: 12px;
}

.goal-meta .meta-label {
  flex: 0 0 auto;
  color: var(--text-muted);
  font-size: 11px;
}

.goal-meta strong {
  color: var(--text-primary);
  font-weight: 600;
  font-size: 12px;
}

.goal-meta .meta-sep {
  width: 1px;
  height: 14px;
  background: var(--border);
  flex: 0 0 auto;
  margin: 0 2px;
}

.goal-meta :deep(.el-input) {
  flex: 1;
  min-width: 80px;
}

.goal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: auto;
}

:deep(.el-input-number) {
  width: 100%;
}

:deep(.el-input__wrapper) {
  background-color: var(--bg-input) !important;
  border-color: var(--border) !important;
}

:deep(.el-input__inner) {
  color: var(--text-primary) !important;
}
</style>
