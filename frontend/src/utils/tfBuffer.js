import * as THREE from 'three'

const normalizeFrame = (frame = '') => String(frame).replace(/^\/+/, '')

const transformToMatrix = (transform = {}) => {
  const translation = transform.translation || transform._translation || {}
  const rotation = transform.rotation || transform._rotation || {}
  const position = new THREE.Vector3(
    Number(translation.x ?? translation._x ?? 0),
    Number(translation.y ?? translation._y ?? 0),
    Number(translation.z ?? translation._z ?? 0)
  )
  const quaternion = new THREE.Quaternion(
    Number(rotation.x ?? rotation._x ?? 0),
    Number(rotation.y ?? rotation._y ?? 0),
    Number(rotation.z ?? rotation._z ?? 0),
    Number(rotation.w ?? rotation._w ?? 1)
  ).normalize()
  return new THREE.Matrix4().compose(position, quaternion, new THREE.Vector3(1, 1, 1))
}

export class TfBuffer {
  constructor() {
    this.transforms = new Map()
  }

  updateMessage(message, isStatic = false) {
    const transforms = message?.transforms || message?._transforms || []
    transforms.forEach(stamped => {
      const header = stamped.header || stamped._header || {}
      const parent = normalizeFrame(header.frame_id || header._frame_id)
      const child = normalizeFrame(stamped.child_frame_id || stamped._child_frame_id)
      const transform = stamped.transform || stamped._transform
      if (!parent || !child || !transform || parent === child) return
      this.transforms.set(child, {
        parent,
        matrix: transformToMatrix(transform),
        isStatic,
        updatedAt: Date.now()
      })
    })
  }

  lookupTransform(targetFrame, sourceFrame) {
    const target = normalizeFrame(targetFrame)
    const source = normalizeFrame(sourceFrame)
    if (!target || !source) return null
    if (target === source) return new THREE.Matrix4()

    const adjacency = new Map()
    const addEdge = (from, to, matrix) => {
      if (!adjacency.has(from)) adjacency.set(from, [])
      adjacency.get(from).push({ frame: to, matrix })
    }
    this.transforms.forEach(({ parent, matrix }, child) => {
      addEdge(child, parent, matrix)
      addEdge(parent, child, matrix.clone().invert())
    })

    const queue = [{ frame: source, matrix: new THREE.Matrix4() }]
    const visited = new Set([source])
    while (queue.length > 0) {
      const current = queue.shift()
      for (const edge of adjacency.get(current.frame) || []) {
        if (visited.has(edge.frame)) continue
        const matrix = edge.matrix.clone().multiply(current.matrix)
        if (edge.frame === target) return matrix
        visited.add(edge.frame)
        queue.push({ frame: edge.frame, matrix })
      }
    }
    return null
  }
}

export const frameIdFromMessage = message => {
  const header = message?.header || message?._header || {}
  return normalizeFrame(header.frame_id || header._frame_id)
}
