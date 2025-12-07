'use client'

import dynamic from 'next/dynamic'

// Динамический импорт карты (Leaflet требует window, поэтому отключаем SSR)
const LeafletMap = dynamic(() => import('./LeafletMap'), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-full bg-gradient-to-br from-gray-50 to-gray-100 text-gray-500">
      <div className="text-lg font-medium">Загрузка карты...</div>
    </div>
  ),
})

export default function MapWrapper() {
  return <LeafletMap />
}

