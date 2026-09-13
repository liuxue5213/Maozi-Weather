import { ref, watchEffect } from 'vue'

const STORAGE_KEY = 'maozi-theme'

const isDark = ref(localStorage.getItem(STORAGE_KEY) === 'dark')

watchEffect(() => {
  document.documentElement.classList.toggle('dark', isDark.value)
  localStorage.setItem(STORAGE_KEY, isDark.value ? 'dark' : 'light')
})

export function useTheme() {
  const toggle = () => {
    isDark.value = !isDark.value
  }
  return { isDark, toggle }
}

export { isDark }
