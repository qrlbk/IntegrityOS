'use client'

import { useState, useEffect } from 'react'
import { AlertCircle, CheckCircle2, Upload, Sparkles } from 'lucide-react'
import { motion } from 'framer-motion'
import { useApp } from '@/contexts/AppContext'
import { useMapContext } from '@/contexts/MapContext'

interface Event {
  date: string
  type: 'detected' | 'repaired' | 'uploaded'
  message: string
  objectId?: number
}

export default function EventsFeed() {
  const app = useApp()
  const mapContext = useMapContext()
  const [events, setEvents] = useState<Event[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadEvents = async () => {
      try {
        const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
        
        // Загружаем последние диагностики через API
        const response = await fetch(`${API_BASE_URL}/api/diagnostics?limit=10&sort_by=date&sort_order=desc`)
        if (!response.ok) throw new Error('Failed to fetch diagnostics')
        
        const diagnostics = await response.json()
        
        const recentEvents: Event[] = diagnostics.slice(0, 5).map((diag: any) => {
          const date = new Date(diag.date)
          
          if (diag.defect_found) {
            return {
              date: date.toLocaleDateString('ru-RU'),
              type: 'detected' as const,
              message: `Обнаружен дефект: ${diag.defect_description || 'Дефект найден'}`,
              objectId: diag.object_id,
            }
          } else if (diag.ml_label === 'normal') {
            return {
              date: date.toLocaleDateString('ru-RU'),
              type: 'repaired' as const,
              message: `Диагностика ${diag.method} - норма`,
              objectId: diag.object_id,
            }
          }
          return null
        }).filter(Boolean)
        
        setEvents(recentEvents)
      } catch (error) {
        console.error('Ошибка загрузки событий:', error)
        // Fallback на статические данные
        setEvents([
          {
            date: new Date().toLocaleDateString('ru-RU'),
            type: 'detected',
            message: 'Новые дефекты обнаружены',
          },
        ])
      } finally {
        setLoading(false)
      }
    }

    loadEvents()
    // Обновляем события каждые 30 секунд
    const interval = setInterval(loadEvents, 30000)
    return () => clearInterval(interval)
  }, [app.state.lastUpdate])

  const handleEventClick = (event: Event) => {
    // Если у события есть objectId, пытаемся найти объект и показать на карте
    if (event.objectId && mapContext) {
      // Ищем объект сначала в отфильтрованных, затем во всех загруженных объектах
      const object = app.filteredObjects.find(obj => obj.id === event.objectId) ||
                     app.state.objects.find(obj => obj.id === event.objectId)
      
      if (object && object.lat != null && object.lon != null && 
          object.lat !== 0 && object.lon !== 0 &&
          !isNaN(object.lat) && !isNaN(object.lon) &&
          object.location_status !== 'pending') {
        // Перемещаем карту к объекту
        mapContext.flyTo({
          lat: object.lat,
          lon: object.lon,
          zoom: 15,
          objectId: object.id,
          duration: 1.0,
        })
        // Подсвечиваем маркер
        mapContext.highlightMarker(object.id)
      }
    }
  }

  const getEventConfig = (type: Event['type']) => {
    switch (type) {
      case 'detected':
        return {
          icon: AlertCircle,
          gradient: 'from-orange-500 to-red-500',
          bg: 'bg-orange-50',
          border: 'border-orange-200',
          text: 'text-orange-700',
          dot: 'bg-orange-500',
          label: 'Обнаружен',
        }
      case 'repaired':
        return {
          icon: CheckCircle2,
          gradient: 'from-green-500 to-emerald-500',
          bg: 'bg-green-50',
          border: 'border-green-200',
          text: 'text-green-700',
          dot: 'bg-green-500',
          label: 'Устранен дефект',
        }
      case 'uploaded':
        return {
          icon: Upload,
          gradient: 'from-blue-500 to-cyan-500',
          bg: 'bg-blue-50',
          border: 'border-blue-200',
          text: 'text-blue-700',
          dot: 'bg-blue-500',
          label: 'Загружены',
        }
    }
  }

  if (loading) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="bg-white rounded-2xl border border-gray-200 shadow-xl shadow-gray-900/5 overflow-hidden"
      >
        <div className="p-8 text-center text-gray-500">Загрузка событий...</div>
      </motion.div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 }}
        className="bg-white rounded-2xl border border-gray-200 shadow-xl shadow-gray-900/5 overflow-hidden"
    >
      {/* Заголовок */}
      <div className="px-6 py-5 border-b border-gray-200 bg-gray-50/50">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 via-blue-500 to-sky-500 flex items-center justify-center shadow-lg shadow-blue-400/30">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-gray-900">События</h2>
            <p className="text-xs text-gray-500">Последние обновления</p>
          </div>
        </div>
      </div>

      {/* Список событий */}
      <div className="p-4 space-y-3">
        {events.length > 0 ? (
          events.map((event, index) => {
            const config = getEventConfig(event.type)
            const Icon = config.icon
            
            return (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                whileHover={{ x: 4, scale: 1.02 }}
                onClick={() => handleEventClick(event)}
                className={`group relative ${config.bg} border ${config.border} rounded-xl p-4 cursor-pointer transition-all hover:shadow-lg ${event.objectId ? 'hover:ring-2 hover:ring-blue-400' : ''}`}
                title={event.objectId ? 'Кликните, чтобы показать на карте' : undefined}
              >
                {/* Градиентный фон при hover */}
                <div className={`absolute inset-0 bg-gradient-to-r ${config.gradient} opacity-0 group-hover:opacity-10 rounded-xl transition-opacity duration-300`}></div>
                
                <div className="relative flex items-start gap-3">
                  {/* Анимированная точка */}
                  <motion.div
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ repeat: Infinity, duration: 2, delay: index * 0.2 }}
                    className={`w-3 h-3 rounded-full ${config.dot} shadow-lg flex-shrink-0 mt-1.5`}
                  />
                  
                  {/* Иконка */}
                  <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${config.gradient} flex items-center justify-center shadow-md group-hover:scale-110 transition-transform`}>
                    <Icon className="w-5 h-5 text-white" />
                  </div>
                  
                  {/* Контент */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`text-sm font-bold ${config.text}`}>{config.label}</span>
                      {event.objectId && (
                        <span className="text-xs text-blue-600 font-medium opacity-70 group-hover:opacity-100 transition-opacity">
                          📍 На карте
                        </span>
                      )}
                    </div>
                    <p className="text-sm font-medium text-gray-700 mb-2">{event.message}</p>
                    <div className="flex items-center gap-2">
                      <div className="w-1 h-1 rounded-full bg-gray-400"></div>
                      <p className="text-xs text-gray-500 font-medium">{event.date}</p>
                    </div>
                  </div>
                </div>
              </motion.div>
            )
          })
        ) : (
          <div className="p-8 text-center text-gray-500">
            <p className="text-sm">Событий пока нет</p>
          </div>
        )}
      </div>

      {/* Кнопка "Показать все" */}
      <div className="px-4 pb-4">
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className="w-full py-2.5 text-sm font-semibold text-gray-600 hover:text-gray-900 bg-gray-50 hover:bg-gray-100 rounded-lg transition-all border border-gray-200"
        >
          Показать все события
        </motion.button>
      </div>
    </motion.div>
  )
}
