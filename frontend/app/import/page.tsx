'use client'

import { motion } from 'framer-motion'
import FileUpload from '@/components/import/FileUpload'
import { useApp } from '@/contexts/AppContext'
import { useEffect } from 'react'

export default function ImportPage() {
  const app = useApp()

  // Обновляем данные после успешного импорта
  useEffect(() => {
    const handleImportSuccess = () => {
      app.refreshData()
    }

    window.addEventListener('importSuccess', handleImportSuccess as EventListener)
    return () => window.removeEventListener('importSuccess', handleImportSuccess as EventListener)
  }, [app])

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Хедер */}
      <motion.header
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="h-20 bg-white/80 backdrop-blur-xl border-b border-gray-200/50 flex items-center justify-between px-8 shadow-sm"
      >
        <div>
          <h1 className="text-2xl font-bold bg-gradient-to-r from-gray-900 via-gray-800 to-gray-900 bg-clip-text text-transparent">
            Импорт данных
          </h1>
          <div className="flex items-center gap-2 mt-1">
            <div className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse"></div>
            <p className="text-sm text-gray-500 font-medium">Главная > Импорт данных</p>
          </div>
        </div>
      </motion.header>

      {/* Контент */}
      <div className="flex-1 overflow-y-auto p-8 bg-gradient-to-b from-transparent to-gray-50/50">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="max-w-6xl mx-auto"
        >
          <FileUpload />
        </motion.div>
      </div>
    </div>
  )
}

