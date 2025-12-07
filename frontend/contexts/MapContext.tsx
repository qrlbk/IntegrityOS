'use client'

import { createContext, useContext, useState, ReactNode, useRef, useCallback } from 'react'

export interface MapFlyToOptions {
  lat: number
  lon: number
  zoom?: number
  objectId?: number
  duration?: number
}

export interface MapFilter {
  method?: string
  criticality?: string
  risk_level?: 'normal' | 'medium' | 'high'
  pipelineId?: string
  pipeline_id?: string
  date_from?: string
  date_to?: string
  param1_min?: number
  param1_max?: number
  param2_min?: number
  param2_max?: number
  param3_min?: number
  param3_max?: number
  sort_by?: 'param1' | 'param2' | 'param3' | 'date'
  sort_order?: 'asc' | 'desc'
}

interface MapContextType {
  // Перемещение карты к координатам
  flyTo: (options: MapFlyToOptions) => void
  // Подсветка маркера
  highlightMarker: (objectId: number | null) => void
  // Фильтрация объектов
  setFilter: (filter: MapFilter | null) => void
  // Текущий фильтр
  currentFilter: MapFilter | null
  // Выделенный маркер
  highlightedMarker: number | null
  // Регистрация функции flyTo из карты
  registerFlyTo: (fn: (options: MapFlyToOptions) => void) => void
}

export const MapContext = createContext<MapContextType | undefined>(undefined)

export function MapProvider({ children }: { children: ReactNode }) {
  const [highlightedMarker, setHighlightedMarker] = useState<number | null>(null)
  const [currentFilter, setCurrentFilter] = useState<MapFilter | null>(null)
  const flyToRef = useRef<((options: MapFlyToOptions) => void) | null>(null)

  const registerFlyTo = useCallback((fn: (options: MapFlyToOptions) => void) => {
    flyToRef.current = fn
  }, [])

  const flyTo = useCallback((options: MapFlyToOptions) => {
    if (flyToRef.current) {
      flyToRef.current(options)
    }
    if (options.objectId) {
      setHighlightedMarker(options.objectId)
    }
  }, [])

  const highlightMarker = useCallback((objectId: number | null) => {
    setHighlightedMarker(objectId)
  }, [])

  const setFilter = useCallback((filter: MapFilter | null) => {
    setCurrentFilter(filter)
    // Сбрасываем подсветку при фильтрации
    setHighlightedMarker(null)
    
    // Уведомляем AppContext об изменении фильтров через событие
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('mapFilterChanged', { detail: filter }))
    }
  }, [])

  const value: MapContextType = {
    flyTo,
    highlightMarker,
    setFilter,
    currentFilter,
    highlightedMarker,
    registerFlyTo,
  }

  return <MapContext.Provider value={value}>{children}</MapContext.Provider>
}

export function useMapContext() {
  const context = useContext(MapContext)
  if (context === undefined) {
    throw new Error('useMapContext must be used within a MapProvider')
  }
  return context
}

