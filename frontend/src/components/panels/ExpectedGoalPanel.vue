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
          @change="emitGoalUpdate"
        />
      </label>
    </div>

    <div class="goal-meta">
      <span>Topic</span>
      <el-input
        v-model="localGoal.topic"
        size="small"
        placeholder="选择或输入目标话题"
        @change="emitGoalUpdate"
      />
      <span>Frame</span>
      <strong>{{ fixedFrame || 'map' }}</strong>
      <span>方向</span>
      <strong>+X</strong>
    </div>

    <div class="goal-actions">
      <el-button size="small" @click="resetGoal">重置</el-button>
      <el-button size="small" @click="$emit('goal-preview', normalizedGoal)">展示</el-button>
      <el-button size="small" type="primary" @click="$emit('goal-publish', normalizedGoal)">
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
  background: #101820;
}

.goal-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.goal-grid label {
  display: grid;
  gap: 5px;
  color: #9fb0c2;
  font-size: 12px;
}

.goal-meta {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 8px;
  align-items: center;
  padding: 8px;
  border: 1px solid #263442;
  background: #0d141c;
  color: #8394a7;
  font-size: 12px;
}

.goal-meta strong {
  color: #dce7f3;
  font-weight: 600;
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
  background-color: #0d141c !important;
  border-color: #2a3948 !important;
}

:deep(.el-input__inner) {
  color: #dce7f3 !important;
}
</style>
