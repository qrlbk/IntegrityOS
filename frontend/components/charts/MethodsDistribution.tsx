'use client'

import { useEffect, useState } from 'react'
import { fetchMethodsDistribution, MethodDistribution } from '@/lib/api'
import { BarChart3, MapPin } from 'lucide-react'
import { useMapContext } from '@/contexts/MapContext'
import { useLanguage } from '@/contexts/LanguageContext'

export default function MethodsDistribution() {
  const [data, setData] = useState<MethodDistribution[]>([])
  const [loading, setLoading] = useState(true)
  const { t } = useLanguage()
  
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
        const result = await fetchMethodsDistribution()
        setData(result)
      } catch (error) {
        console.error('Ошибка загрузки распределения по методам:', error)
        // Данные для демо
        setData([
          { method: 'VIK', total: 500, defects: 120, percentage: 24 },
          { method: 'MFL', total: 400, defects: 80, percentage: 20 },
          { method: 'UTWM', total: 300, defects: 60, percentage: 20 },
          { method: 'UT', total: 200, defects: 40, percentage: 20 },
          { method: 'EC', total: 100, defects: 20, percentage: 20 },
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

  const maxTotal = Math.max(...data.map(d => d.total), 1)

  return (
    <div className={`${bgClass} border rounded-2xl p-6 shadow-lg`}>
      <div className="flex items-center gap-2 mb-4">
        <BarChart3 className="w-5 h-5 text-blue-500" />
        <h3 className={`text-lg font-semibold ${textClass}`}>{t('methodsDistribution')}</h3>
      </div>
      <div className="space-y-3">
        {data.map((item) => {
          const isActive = mapContext && mapContext.currentFilter?.method === item.method
          return (
            <div
              key={item.method}
              onClick={() => {
                if (!mapContext) return
                if (isActive) {
                  mapContext.setFilter(null)
                } else {
                  mapContext.setFilter({ method: item.method })
                }
              }}
              className={`space-y-1 p-2 rounded-lg transition-all ${
                mapContext ? 'cursor-pointer' : ''
              } ${
                isActive ? 'bg-blue-500/20 border border-blue-500/50' : mapContext ? hoverBgClass : ''
              }`}
              title={mapContext ? (isActive ? t('clickToResetFilter') : t('clickToFilter')) : undefined}
            >
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-2">
                  <span className={`text-sm font-medium ${isActive ? 'text-blue-600' : textClass}`}>
                    {item.method}
                  </span>
                  {isActive && <MapPin className="w-3 h-3 text-blue-500" />}
                </div>
                <span className={`text-sm ${isActive ? 'text-blue-600' : textClass}`}>
                  {item.defects} / {item.total} ({item.percentage}%)
                </span>
              </div>
              <div className={`w-full ${barBgClass} rounded-full h-2`}>
                <div
                  className="bg-blue-500 h-2 rounded-full transition-all"
                  style={{ width: `${(item.total / maxTotal) * 100}%` }}
                />
              </div>
              <div className={`w-full ${barBgClass} rounded-full h-2 -mt-2`}>
                <div
                  className={`h-2 rounded-full transition-all ${isActive ? 'bg-red-400' : 'bg-red-500'}`}
                  style={{ width: `${(item.defects / maxTotal) * 100}%` }}
                />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

