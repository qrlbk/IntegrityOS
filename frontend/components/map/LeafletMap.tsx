'use client'

import { useEffect, useState, useMemo, useContext, useRef } from 'react'
import { MapContainer, TileLayer, CircleMarker, Popup, Polyline, useMap } from 'react-leaflet'
import L from 'leaflet'
import { fetchObjects, PipelineObject } from '@/lib/api'
import { MapContext } from '@/contexts/MapContext'
import { useApp } from '@/contexts/AppContext'
import MapFlyTo from './MapFlyTo'

// Фикс для иконок Leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
})

// Центр карты - Казахстан
const CENTER: [number, number] = [48.0, 66.0]
const DEFAULT_ZOOM = 6

// Компонент для настройки карты после монтирования
function MapConfigurator() {
  const map = useMap()

  useEffect(() => {
    // Настройка для лучшей работы с тачпадом
    const leafletMap = map

    // Включаем инерцию для плавного движения
    if (leafletMap.dragging) {
      leafletMap.dragging.enable()
    }

    // Настраиваем тач-зум для тачпада
    if (leafletMap.touchZoom) {
      leafletMap.touchZoom.enable()
    }

    // Включаем зум колесиком мыши
    if (leafletMap.scrollWheelZoom) {
      leafletMap.scrollWheelZoom.enable()
    }

    // Настраиваем инерцию для плавности
    leafletMap.options.inertia = true
    leafletMap.options.inertiaDeceleration = 2000 // Замедление (px/s²)
    leafletMap.options.inertiaMaxSpeed = 1500 // Максимальная скорость (px/s)

    // Улучшаем обработку тач-событий
    leafletMap.options.tap = true
    leafletMap.options.tapTolerance = 15 // Допуск для тапа (px)

    // Настройка для лучшей работы с тачпадом Mac
    leafletMap.options.bounceAtZoomLimits = true
    leafletMap.options.maxBoundsViscosity = 0.0 // Не прилипать к границам

    return () => {
      // Cleanup при размонтировании
    }
  }, [map])

  return null
}

export default function LeafletMap() {
  const app = useApp()
  const mapContext = useContext(MapContext)
  const [loading, setLoading] = useState(true)
  
  // Используем объекты из AppContext
  const objects = app.filteredObjects
  const filteredObjects = objects
  
  // Инициализируем глобальное хранилище для refs маркеров
  useEffect(() => {
    if (typeof window !== 'undefined' && !window.leafletMarkerRefs) {
      window.leafletMarkerRefs = new Map()
    }
    return () => {
      // Cleanup при размонтировании
      if (window.leafletMarkerRefs) {
        window.leafletMarkerRefs.clear()
      }
    }
  }, [])

  // Объекты загружаются через AppContext, просто обновляем loading
  useEffect(() => {
    if (app.state.objects.length > 0) {
      setLoading(false)
    }
  }, [app.state.objects])

  // Фильтрация теперь выполняется на сервере через API
  // Объекты уже отфильтрованы после загрузки

  // Группируем объекты по pipeline_id для отрисовки линий
  const objectsByPipeline = useMemo(() => {
    const grouped: Record<string, PipelineObject[]> = {}
    filteredObjects.forEach((obj) => {
      const pipelineId = obj.pipeline_id || 'unknown'
      if (!grouped[pipelineId]) {
        grouped[pipelineId] = []
      }
      grouped[pipelineId].push(obj)
    })

    // Сортируем объекты внутри каждой трубы по имени (для правильного порядка)
    Object.keys(grouped).forEach((pipelineId) => {
      grouped[pipelineId].sort((a, b) => {
        const numA = parseInt(a.name.match(/\d+/)?.[0] || '0')
        const numB = parseInt(b.name.match(/\d+/)?.[0] || '0')
        return numA - numB
      })
    })

    return grouped
  }, [filteredObjects])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-900 text-white">
        <div className="text-lg">Загрузка данных...</div>
      </div>
    )
  }

  return (
    <MapContainer
      center={CENTER}
      zoom={DEFAULT_ZOOM}
      style={{ height: '100%', width: '100%' }}
      className="z-0"
      // Настройки для работы с тачпадом
      dragging={true}
      touchZoom={true}
      doubleClickZoom={true}
      scrollWheelZoom={true}
      boxZoom={true}
      keyboard={true}
      zoomControl={true}
      // Настройки инерции для плавности
      inertia={true}
      inertiaDeceleration={2000}
      inertiaMaxSpeed={1500}
      // Настройки тач-событий
      tap={true}
      tapTolerance={15}
      // Другие настройки
      bounceAtZoomLimits={true}
      maxBoundsViscosity={0.0}
      preferCanvas={false}
    >
      <MapConfigurator />
      <MapFlyTo />
      {/* Светлая карта для современного дизайна */}
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
        url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
        subdomains="abcd"
        maxZoom={19}
      />

      {/* Отрисовываем линии для каждой трубы */}
      {Object.entries(objectsByPipeline).map(([pipelineId, pipelineObjects]) => {
        if (pipelineObjects.length < 2) return null

        // Фильтруем объекты с валидными координатами для отрисовки линий
        const validObjects = pipelineObjects.filter((obj) => 
          obj.lat != null && obj.lon != null && 
          obj.lat !== 0 && obj.lon !== 0 &&
          !isNaN(obj.lat) && !isNaN(obj.lon) &&
          obj.location_status !== "pending"
        )
        
        if (validObjects.length < 2) return null

        const positions = validObjects.map((obj) => [obj.lat, obj.lon] as [number, number])

        return (
          <Polyline
            key={`pipeline-${pipelineId}`}
            positions={positions}
            pathOptions={{
              color: '#60a5fa', // Синий цвет для линий
              weight: 2,
              opacity: 0.6,
            }}
          />
        )
      })}

      {/* Отрисовываем маркеры */}
      {filteredObjects
        .filter((obj) => {
          // Дополнительная проверка на frontend: не показываем объекты без валидных координат
          // Объекты с location_status="pending" или координатами null не показываются на карте
          return obj.lat != null && obj.lon != null && 
                 obj.lat !== 0 && obj.lon !== 0 &&
                 !isNaN(obj.lat) && !isNaN(obj.lon) &&
                 obj.location_status !== "pending"
        })
        .map((obj) => {
        const isCritical = obj.status === 'Critical'
        const isHighlighted = mapContext && mapContext.highlightedMarker === obj.id
        // Определяем цвет на основе risk_level в первую очередь, если доступен
        // Приоритет: risk_level > status
        let color = '#10b981' // По умолчанию зеленый
        if (obj.risk_level) {
          // Если есть risk_level, используем его
          if (obj.risk_level === 'high') {
            color = '#dc2626' // Красный для высокого риска
          } else if (obj.risk_level === 'medium') {
            color = '#eab308' // Желтый для среднего риска
          } else {
            color = '#10b981' // Зеленый для нормального
          }
        } else {
          // Если risk_level нет, используем status как fallback
          if (isCritical) {
            color = '#dc2626' // Красный для критических
          } else {
            color = '#10b981' // Зеленый для нормальных
          }
        }
        // Критические маркеры и маркеры высокого риска больше
        const isHighRisk = obj.risk_level === 'high' || (isCritical && !obj.risk_level)
        const radius = isHighlighted ? (isHighRisk ? 14 : 10) : (isHighRisk ? 10 : (obj.risk_level === 'medium' ? 8 : 6))

        return (
          <CircleMarker
            key={obj.id}
            center={[obj.lat, obj.lon]}
            radius={radius}
            pathOptions={{
              fillColor: color,
              color: isHighlighted ? '#fbbf24' : '#ffffff', // Желтая обводка для выделенных
              weight: isHighlighted ? 4 : (isHighRisk ? 3 : 2), // Толще обводка для выделенных
              opacity: 1,
              fillOpacity: isHighlighted ? 1 : (isHighRisk ? 0.9 : (obj.risk_level === 'medium' ? 0.85 : 0.8)), // Полностью непрозрачный для выделенных
            }}
            className={`${isHighRisk ? 'critical-marker' : (obj.risk_level === 'medium' ? 'medium-marker' : 'normal-marker')} ${isHighlighted ? 'highlighted-marker' : ''}`}
            ref={(ref) => {
              if (typeof window !== 'undefined' && window.leafletMarkerRefs) {
                if (ref) {
                  window.leafletMarkerRefs.set(obj.id, ref)
                } else {
                  window.leafletMarkerRefs.delete(obj.id)
                }
              }
            }}
          >
            <Popup>
              <div className="p-3 min-w-[220px]">
                <h3 className="font-bold text-base mb-2">{obj.name}</h3>
                <div className="space-y-1 text-sm mb-3">
                  <p>
                    <span className="font-semibold">Тип:</span> {obj.type}
                  </p>
                  <p>
                    <span className="font-semibold">Статус:</span>{' '}
                    <span
                      className={`font-bold ${
                        isCritical ? 'text-red-600' : (obj.risk_level === 'medium' ? 'text-yellow-600' : 'text-green-600')
                      }`}
                    >
                      {obj.status}
                    </span>
                  </p>
                  {obj.risk_level && (
                    <p>
                      <span className="font-semibold">Уровень риска:</span>{' '}
                      <span
                        className={`font-bold ${
                          obj.risk_level === 'high' ? 'text-red-600' : 
                          obj.risk_level === 'medium' ? 'text-yellow-600' : 
                          'text-green-600'
                        }`}
                      >
                        {obj.risk_level === 'high' ? 'Высокий' : 
                         obj.risk_level === 'medium' ? 'Средний' : 
                         'Низкий'}
                      </span>
                    </p>
                  )}
                  {obj.pipeline_id && (
                    <p>
                      <span className="font-semibold">Трасса:</span> {obj.pipeline_id}
                    </p>
                  )}
                </div>
                <button
                  className="w-full mt-2 bg-emerald-600 text-white px-3 py-1.5 rounded text-xs font-medium hover:bg-emerald-700 transition-colors"
                  onClick={() => {
                    window.open(`/print/${obj.id}`, '_blank', 'width=800,height=600')
                  }}
                >
                  📄 Скачать наряд-допуск (PDF)
                </button>
              </div>
            </Popup>
          </CircleMarker>
        )
      })}
    </MapContainer>
  )
}

