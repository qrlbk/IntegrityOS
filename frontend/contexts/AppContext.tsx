'use client'

import { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react'
import { fetchObjects, fetchStatsSummary, PipelineObject, StatsSummary } from '@/lib/api'
import { MapFilter } from './MapContext'

interface AppState {
  objects: PipelineObject[]
  stats: StatsSummary | null
  filters: MapFilter | null
  loading: boolean
  lastUpdate: Date | null
}

interface AppContextType {
  // Состояние
  state: AppState
  
  // Действия
  setFilters: (filters: MapFilter | null) => void
  refreshData: () => Promise<void>
  updateObjects: (objects: PipelineObject[]) => void
  
  // Вычисляемые значения
  filteredObjects: PipelineObject[]
  criticalCount: number
  totalDefects: number
}

const AppContext = createContext<AppContextType | undefined>(undefined)

export function AppProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AppState>({
    objects: [],
    stats: null,
    filters: null,
    loading: true,
    lastUpdate: null,
  })

  // Загрузка данных
  const loadData = useCallback(async (filters?: MapFilter | null) => {
    setState(prev => ({ ...prev, loading: true }))
    
    try {
      const [objectsData, statsData] = await Promise.all([
        fetchObjects(filters || undefined),
        fetchStatsSummary().catch(() => null)
      ])
      
      setState(prev => ({
        ...prev,
        objects: objectsData,
        stats: statsData,
        filters: filters || null,
        loading: false,
        lastUpdate: new Date(),
      }))
    } catch (error) {
      console.error('Ошибка загрузки данных:', error)
      setState(prev => ({ ...prev, loading: false }))
    }
  }, [])

  // Первоначальная загрузка
  useEffect(() => {
    loadData()
  }, [loadData])

  // Обновление фильтров
  const setFilters = useCallback((filters: MapFilter | null) => {
    setState(prev => ({ ...prev, filters }))
    loadData(filters)
  }, [loadData])

  // Обновление данных
  const refreshData = useCallback(async () => {
    await loadData(state.filters)
  }, [loadData, state.filters])

  // Обновление объектов напрямую
  const updateObjects = useCallback((objects: PipelineObject[]) => {
    setState(prev => ({ ...prev, objects }))
  }, [])

  // Вычисляемые значения
  const filteredObjects = state.objects.filter(obj => {
    if (!state.filters) return true
    
    if (state.filters.pipeline_id && obj.pipeline_id !== state.filters.pipeline_id) {
      return false
    }
    
    if (state.filters.risk_level) {
      // Фильтруем по risk_level, если он есть у объекта
      if (obj.risk_level) {
        if (obj.risk_level !== state.filters.risk_level) return false
      } else {
        // Если risk_level нет, используем status как fallback
        const isCritical = obj.status === 'Critical'
        if (state.filters.risk_level === 'high' && !isCritical) return false
        if (state.filters.risk_level === 'medium' && isCritical) return false
        if (state.filters.risk_level === 'normal' && isCritical) return false
      }
    }
    
    return true
  })

  const criticalCount = state.stats?.criticality.high || 
    filteredObjects.filter(o => o.status === 'Critical').length

  const totalDefects = state.stats?.total_defects || 
    filteredObjects.filter(o => o.status === 'Critical').length

  const value: AppContextType = {
    state,
    setFilters,
    refreshData,
    updateObjects,
    filteredObjects,
    criticalCount,
    totalDefects,
  }

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>
}

export function useApp() {
  const context = useContext(AppContext)
  if (context === undefined) {
    throw new Error('useApp must be used within an AppProvider')
  }
  return context
}

