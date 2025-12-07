'use client'

import { useEffect, useState } from 'react'
import { fetchTopRisks, TopRisk } from '@/lib/api'
import { AlertTriangle, MapPin } from 'lucide-react'
import { useMapContext } from '@/contexts/MapContext'
import { useLanguage } from '@/contexts/LanguageContext'

export default function TopRisks() {
  const [data, setData] = useState<TopRisk[]>([])
  const [loading, setLoading] = useState(true)
  const { t } = useLanguage()
  
  // Безопасное использование контекста
  let mapContext: ReturnType<typeof useMapContext> | null = null
  try {
    mapContext = useMapContext()
  } catch (e) {
    // Контекст недоступен - компонент будет работать без интерактивности
  }

  useEffect(() => {
    const loadData = async () => {
      try {
        const result = await fetchTopRisks(5)
        setData(result)
      } catch (error) {
        console.error('Ошибка загрузки топ-рисков:', error)
        // Данные для демо
        setData([
          { object_id: 1, object_name: 'MT-01-Section-0042', object_type: 'pipeline_section', lat: 47.1, lon: 51.9, high_defects_count: 5 },
          { object_id: 2, object_name: 'MT-02-Compressor-12', object_type: 'compressor', lat: 51.1, lon: 71.4, high_defects_count: 4 },
          { object_id: 3, object_name: 'MT-03-Section-0089', object_type: 'pipeline_section', lat: 43.2, lon: 76.8, high_defects_count: 3 },
        ])
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [])

  // Принудительно используем светлую тему для белого фона
  const bgClass = 'bg-white border-gray-200 shadow-lg'
  const textClass = 'text-gray-900'
  const textSecondaryClass = 'text-gray-600'
  const cardBgClass = 'bg-gray-50 hover:bg-gray-100 border border-gray-200'

  if (loading) {
    return (
      <div className={`${bgClass} border rounded-2xl p-6 shadow-lg`}>
        <p className={textSecondaryClass}>{t('loading')}</p>
      </div>
    )
  }

  if (data.length === 0) {
    return (
      <div className={`${bgClass} border rounded-2xl p-6 shadow-lg`}>
        <div className="flex items-center gap-2 mb-4">
          <AlertTriangle className="w-5 h-5 text-red-500" />
          <h3 className={`text-lg font-semibold ${textClass}`}>{t('topRisks')}</h3>
        </div>
        <p className={textSecondaryClass}>{t('noData')}</p>
      </div>
    )
  }

  return (
    <div className={`${bgClass} border rounded-2xl p-6 shadow-lg`}>
      <div className="flex items-center gap-2 mb-4">
        <AlertTriangle className="w-5 h-5 text-red-500" />
        <h3 className={`text-lg font-semibold ${textClass}`}>{t('topRisks')}</h3>
      </div>
      <div className="space-y-3">
        {data.map((risk, index) => (
          <div
            key={risk.object_id}
            onClick={() => {
              if (mapContext) {
                mapContext.flyTo({
                  lat: risk.lat,
                  lon: risk.lon,
                  zoom: 14,
                  objectId: risk.object_id,
                  duration: 1.5,
                })
              }
            }}
            className={`flex items-center justify-between p-3 ${cardBgClass} rounded-lg transition-colors group ${
              mapContext ? 'cursor-pointer' : ''
            }`}
            title={mapContext ? t('clickToShowOnMap') : undefined}
          >
            <div className="flex items-center gap-3 flex-1">
              <div className="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center group-hover:bg-red-200 transition-colors">
                <span className="text-red-600 font-bold text-sm">{index + 1}</span>
              </div>
              <div className="flex-1">
                <p className={`${textClass} font-medium text-sm group-hover:text-blue-500 transition-colors`}>
                  {risk.object_name}
                </p>
                <p className={textSecondaryClass + ' text-xs'}>{risk.object_type}</p>
              </div>
            </div>
            <div className="text-right flex items-center gap-2">
              <div>
                <p className="text-red-500 font-bold">{risk.high_defects_count}</p>
                <p className={`${textSecondaryClass} text-xs`}>{t('critical')}</p>
              </div>
              <MapPin className="w-4 h-4 text-blue-500 opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

