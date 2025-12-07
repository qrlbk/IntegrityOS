'use client'

import { useEffect, useState } from 'react'
import { fetchCriticalityDistribution, CriticalityDistribution } from '@/lib/api'
import { PieChart, MapPin } from 'lucide-react'
import { useMapContext } from '@/contexts/MapContext'
import { useApp } from '@/contexts/AppContext'
import { useLanguage } from '@/contexts/LanguageContext'

export default function CriticalityDistribution() {
  const [data, setData] = useState<CriticalityDistribution[]>([])
  const [loading, setLoading] = useState(true)
  const { t } = useLanguage()
  const app = useApp()
  
  // Безопасное использование контекста
  let mapContext: ReturnType<typeof useMapContext> | null = null
  try {
    mapContext = useMapContext()
  } catch (e) {
    // Контекст недоступен - компонент будет работать без интерактивности
  }
  
  // Принудительно используем светлую тему для белого фона
  const bgClass = 'bg-white border-gray-200 shadow-lg'
  const textClass = 'text-gray-900'
  const textSecondaryClass = 'text-gray-600'
  const hoverBgClass = 'hover:bg-gray-50'
  const barBgClass = 'bg-gray-200'

  useEffect(() => {
    const loadData = async () => {
      try {
        const result = await fetchCriticalityDistribution()
        setData(result)
      } catch (error) {
        console.error('Ошибка загрузки распределения по критичности:', error)
        // Данные для демо
        setData([
          { label: 'normal', count: 1200, percentage: 66.7 },
          { label: 'medium', count: 400, percentage: 22.2 },
          { label: 'high', count: 200, percentage: 11.1 },
        ])
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [])

  if (loading) {
    return (
      <div className={`${bgClass} border rounded-2xl p-6 shadow-lg`}>
        <p className={textSecondaryClass}>{t('loading')}</p>
      </div>
    )
  }

  const getColor = (label: string) => {
    switch (label.toLowerCase()) {
      case 'high':
        return 'bg-red-500'
      case 'medium':
        return 'bg-yellow-500'
      case 'normal':
        return 'bg-green-500'
      default:
        return 'bg-gray-500'
    }
  }

  const getLabelText = (label: string) => {
    switch (label.toLowerCase()) {
      case 'high':
        return t('high')
      case 'medium':
        return t('medium')
      case 'normal':
        return t('normal')
      default:
        return label
    }
  }

  return (
    <div className={`${bgClass} border rounded-2xl p-6 shadow-lg`}>
      <div className="flex items-center gap-2 mb-4">
        <PieChart className="w-5 h-5 text-blue-500" />
        <h3 className={`text-lg font-semibold ${textClass}`}>{t('criticalityDistribution')}</h3>
      </div>
      <div className="space-y-3">
        {data.map((item) => {
          const criticalityKey = item.label.toLowerCase() as 'normal' | 'medium' | 'high'
          const isActive = app.state.filters?.risk_level === criticalityKey || 
                          (mapContext && (mapContext.currentFilter?.risk_level === criticalityKey || mapContext.currentFilter?.criticality === criticalityKey))
          return (
            <div
              key={item.label}
              onClick={() => {
                if (isActive) {
                  // Сбрасываем фильтр
                  app.setFilters(null)
                  if (mapContext) {
                    mapContext.setFilter(null)
                  }
                } else {
                  // Применяем фильтр
                  const filter = { risk_level: criticalityKey }
                  app.setFilters(filter)
                  if (mapContext) {
                    mapContext.setFilter(filter)
                  }
                }
              }}
              className={`space-y-1 p-2 rounded-lg transition-all ${
                mapContext ? 'cursor-pointer' : ''
              } ${
                isActive ? 'bg-blue-500/20 border border-blue-500/50' : mapContext ? hoverBgClass : ''
              }`}
              title={mapContext ? (isActive ? t('clickToResetFilter') : t('clickToShowRiskLevel')) : undefined}
            >
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-2">
                  <div className={`w-3 h-3 rounded-full ${getColor(item.label)}`} />
                  <span className={`text-sm font-medium ${isActive ? 'text-blue-600' : textClass}`}>
                    {getLabelText(item.label)}
                  </span>
                  {isActive && <MapPin className="w-3 h-3 text-blue-500" />}
                </div>
                <span className={`text-sm ${isActive ? 'text-blue-600' : textClass}`}>
                  {item.count} ({item.percentage}%)
                </span>
              </div>
              <div className={`w-full ${barBgClass} rounded-full h-2`}>
                <div
                  className={`${getColor(item.label)} h-2 rounded-full transition-all`}
                  style={{ width: `${item.percentage}%` }}
                />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

