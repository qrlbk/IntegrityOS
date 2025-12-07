'use client'

import { useEffect, useContext } from 'react'
import { useMap } from 'react-leaflet'
import { MapContext, MapFlyToOptions } from '@/contexts/MapContext'

// Глобальная переменная для хранения refs маркеров (временное решение)
// В идеале это должно быть через контекст, но для простоты используем window
declare global {
  interface Window {
    leafletMarkerRefs?: Map<number, any>
  }
}

// Компонент для регистрации функции flyTo в контексте
export default function MapFlyTo() {
  const map = useMap()
  const context = useContext(MapContext)

  useEffect(() => {
    if (!context) {
      // Если контекст недоступен, просто выходим
      return
    }

    // Регистрируем функцию flyTo в контексте
    const flyToFunction = (options: MapFlyToOptions) => {
      const zoom = options.zoom || 14
      const duration = options.duration || 1.5

      map.flyTo([options.lat, options.lon], zoom, {
        duration: duration,
        easeLinearity: 0.25,
      })

      // Открываем попап для объекта, если указан objectId
      if (options.objectId && window.leafletMarkerRefs) {
        setTimeout(() => {
          const markerRef = window.leafletMarkerRefs.get(options.objectId!)
          if (markerRef) {
            // Открываем попап через react-leaflet API
            const leafletLayer = markerRef.leafletElement || markerRef
            if (leafletLayer && leafletLayer.getPopup) {
              const popup = leafletLayer.getPopup()
              if (popup) {
                popup.openOn(map)
              }
            } else if (leafletLayer && leafletLayer.openPopup) {
              leafletLayer.openPopup()
            }
          }
        }, duration * 1000)
      }
    }

    context.registerFlyTo(flyToFunction)

    return () => {
      // Cleanup
    }
  }, [map, context])

  return null
}

