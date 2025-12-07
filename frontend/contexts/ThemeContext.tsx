'use client'

import { createContext, useContext, useEffect, useState, ReactNode } from 'react'

type Theme = 'light' | 'dark'

interface ThemeContextType {
  theme: Theme
  toggleTheme: () => void
  setTheme: (theme: Theme) => void
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme] = useState<Theme>('dark') // Всегда темная тема
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    // Всегда применяем темную тему
    const root = document.documentElement
    root.classList.add('dark')
    localStorage.setItem('theme', 'dark')
  }, [])

  const toggleTheme = () => {
    // Функция оставлена для совместимости, но ничего не делает
    // Тема всегда темная
  }

  const setTheme = (newTheme: Theme) => {
    // Функция оставлена для совместимости, но ничего не делает
    // Тема всегда темная
  }

  // Всегда возвращаем провайдер, даже если еще не смонтирован
  // Это предотвращает ошибки при использовании хука до инициализации
  return (
    <ThemeContext.Provider value={{ theme, toggleTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const context = useContext(ThemeContext)
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }
  return context
}

