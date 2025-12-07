'use client'

import { AppProvider } from '@/contexts/AppContext'
import { ThemeProvider } from '@/contexts/ThemeContext'
import { LanguageProvider } from '@/contexts/LanguageContext'
import { MapProvider } from '@/contexts/MapContext'
import Sidebar from '@/components/layout/Sidebar'

export default function ClientLayout({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider>
      <LanguageProvider>
        <AppProvider>
          <MapProvider>
            <div className="flex h-screen bg-gradient-to-br from-gray-50 via-white to-gray-50">
              {/* Фиксированный сайдбар */}
              <Sidebar />
              {/* Контент справа с отступом */}
              <div className="flex-1 ml-72 flex flex-col overflow-hidden">
                {children}
              </div>
            </div>
          </MapProvider>
        </AppProvider>
      </LanguageProvider>
    </ThemeProvider>
  )
}

