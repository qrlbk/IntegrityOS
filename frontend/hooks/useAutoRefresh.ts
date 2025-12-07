'use client'

import { useEffect, useRef } from 'react'
import { useApp } from '@/contexts/AppContext'

/**
 * Хук для автоматического обновления данных приложения
 */
export function useAutoRefresh(intervalMs: number = 60000) {
  const app = useApp()
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    // Автоматическое обновление каждые N секунд
    intervalRef.current = setInterval(() => {
      app.refreshData()
    }, intervalMs)

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [app, intervalMs])

  return {
    refresh: app.refreshData,
    lastUpdate: app.state.lastUpdate,
  }
}

