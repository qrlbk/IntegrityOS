'use client'

import { usePathname } from 'next/navigation'
import { AppProvider } from '@/contexts/AppContext'
import { ThemeProvider } from '@/contexts/ThemeContext'
import { LanguageProvider } from '@/contexts/LanguageContext'
import { MapProvider } from '@/contexts/MapContext'
import Sidebar from '@/components/layout/Sidebar'

export default function ClientLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const isPrintPage = pathname?.startsWith('/print/')
  
  return (
    <ThemeProvider>
      <LanguageProvider>
        <AppProvider>
          <MapProvider>
            {isPrintPage ? (
              // Для страниц печати - без сайдбара и с возможностью скроллинга
              <div className="min-h-screen bg-white">
                {children}
              </div>
            ) : (
              // Для остальных страниц - стандартный layout с сайдбаром
              <div className="flex h-screen bg-gradient-to-br from-gray-50 via-white to-gray-50">
                {/* Фиксированный сайдбар */}
                <Sidebar />
                {/* Контент справа с отступом */}
                <div className="flex-1 ml-72 flex flex-col overflow-hidden">
                  {children}
                </div>
              </div>
            )}
          </MapProvider>
        </AppProvider>
      </LanguageProvider>
    </ThemeProvider>
  )
}

