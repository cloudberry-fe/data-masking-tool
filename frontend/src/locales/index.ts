import { createI18n } from 'vue-i18n'
import en from './en'
import zh from './zh'

// 获取存储的语言或浏览器语言
function getDefaultLocale(): string {
  const stored = localStorage.getItem('locale')
  if (stored) {
    return stored
  }

  // 浏览器语言
  const browserLang = navigator.language.toLowerCase()
  if (browserLang.startsWith('zh')) {
    return 'zh'
  }

  return 'en'  // 默认英文
}

const i18n = createI18n({
  legacy: false,
  locale: getDefaultLocale(),
  fallbackLocale: 'en',
  messages: {
    en,
    zh,
  },
})

export default i18n

export function setLocale(locale: string): void {
  localStorage.setItem('locale', locale)
  i18n.global.locale.value = locale as any
  document.querySelector('html')?.setAttribute('lang', locale)
}

export function getLocale(): string {
  return i18n.global.locale.value as string
}

export const LOCALES = [
  { code: 'en', name: 'English', flag: '🇺🇸' },
  { code: 'zh', name: '中文', flag: '🇨🇳' },
]
