export const resizeFromTopLeft = ({
  x,
  y,
  width,
  height,
  aspectRatio,
  deltaX,
  deltaY,
  minWidth,
  minHeight
}) => {
  const ratio = aspectRatio || width / height
  const rightEdge = x + width
  const bottomEdge = y + height
  const requestedWidth = Math.abs(deltaX) >= Math.abs(deltaY)
    ? width - deltaX
    : (height - deltaY) * ratio
  const maximumWidth = Math.min(rightEdge, bottomEdge * ratio)
  const minimumWidth = Math.min(Math.max(minWidth, minHeight * ratio), maximumWidth)
  const nextWidth = Math.max(minimumWidth, Math.min(requestedWidth, maximumWidth))
  const nextHeight = nextWidth / ratio

  return {
    x: rightEdge - nextWidth,
    y: bottomEdge - nextHeight,
    width: nextWidth,
    height: nextHeight
  }
}
