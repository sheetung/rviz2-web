export const getThemeColor = (tokenName) => {
  if (typeof window === 'undefined') return ''
  return window.getComputedStyle(document.documentElement)
    .getPropertyValue(tokenName)
    .trim()
}
