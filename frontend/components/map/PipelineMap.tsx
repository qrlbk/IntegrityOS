'use client'

import { useEffect, useState } from 'react'
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { apiClient, Object } from '@/lib/api'

// Фикс для иконок Leaflet в Next.js
delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
})

interface PipelineMapProps {
  filters: {
    pipelineId: string
    method: string
    riskLevel: string
  }
}

// Компонент для обновления карты при изменении фильтров
function MapUpdater({ filters }: PipelineMapProps) {
  const map = useMap()

  useEffect(() => {
    // Можно добавить логику автоматического зума к отфильтрованным объектам
  }, [filters, map])

  return null
}

export default function PipelineMap({ filters }: PipelineMapProps) {
  const [objects, setObjects] = useState<Object[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchObjects = async () => {
      setLoading(true)
      try {
        const data = await apiClient.getObjects({
          pipeline_id: filters.pipelineId || undefined,
          method: filters.method || undefined,
          risk_level: filters.riskLevel || undefined,
        })
        setObjects(data)
      } catch (error) {
        console.error('Ошибка загрузки объектов:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchObjects()
  }, [filters])

  // Цвет маркера в зависимости от уровня риска
  const getMarkerColor = (riskLevel?: string) => {
    switch (riskLevel) {
      case 'high':
        return 'red'
      case 'medium':
        return 'orange'
      case 'normal':
      default:
        return 'green'
    }
  }

  // Создаем кастомные иконки
  const createCustomIcon = (riskLevel?: string) => {
    const color = getMarkerColor(riskLevel)
    return L.divIcon({
      className: 'custom-marker',
      html: `<div style="
        background-color: ${color};
        width: 20px;
        height: 20px;
        border-radius: 50%;
        border: 2px solid white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
      "></div>`,
      iconSize: [20, 20],
      iconAnchor: [10, 10],
    })
  }

  // Центр карты - Казахстан
  const center: [number, number] = [48.0, 66.0]

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-lg">Загрузка данных...</div>
      </div>
    )
  }

  return (
    <MapContainer
      center={center}
      zoom={6}
      style={{ height: '100%', width: '100%' }}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <MapUpdater filters={filters} />
      {objects
        .filter((obj) => {
          // Не показываем объекты без валидных координат
          // Объекты с location_status="pending" не показываются на карте
          return obj.lat != null && obj.lon != null && 
                 obj.lat !== 0 && obj.lon !== 0 &&
                 !isNaN(obj.lat) && !isNaN(obj.lon) &&
                 obj.location_status !== "pending"
        })
        .map((obj) => (
        <Marker
          key={obj.object_id}
          position={[obj.lat, obj.lon]}
          icon={createCustomIcon(obj.risk_level)}
        >
          <Popup>
            <div className="p-2">
              <h3 className="font-bold">{obj.object_name}</h3>
              <p className="text-sm">Тип: {obj.object_type}</p>
              <p className="text-sm">Трасса: {obj.pipeline_id}</p>
              {obj.risk_level && (
                <p className="text-sm">
                  Риск: <span className="font-semibold">{obj.risk_level}</span>
                </p>
              )}
              {obj.last_diagnostic_date && (
                <p className="text-xs text-gray-500">
                  Последняя диагностика: {new Date(obj.last_diagnostic_date).toLocaleDateString('ru-RU')}
                </p>
              )}
            </div>
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  )
}

