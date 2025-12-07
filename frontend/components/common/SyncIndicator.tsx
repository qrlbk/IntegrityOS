'use client'

import { useApp } from '@/contexts/AppContext'
import { motion, AnimatePresence } from 'framer-motion'
import { RefreshCw, CheckCircle2 } from 'lucide-react'
import { useEffect, useState } from 'react'

export default function SyncIndicator() {
  const app = useApp()
  const [isSyncing, setIsSyncing] = useState(false)
  const [lastSyncTime, setLastSyncTime] = useState<Date | null>(null)

  useEffect(() => {
    if (app.state.loading) {
      setIsSyncing(true)
    } else {
      setIsSyncing(false)
      if (app.state.lastUpdate) {
        setLastSyncTime(app.state.lastUpdate)
      }
    }
  }, [app.state.loading, app.state.lastUpdate])

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('ru-RU', { 
      hour: '2-digit', 
      minute: '2-digit',
      second: '2-digit'
    })
  }

  return (
    <AnimatePresence>
      {(isSyncing || lastSyncTime) && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          className="fixed bottom-4 right-4 z-50"
        >
          <div className="bg-white/90 backdrop-blur-xl rounded-xl shadow-lg border border-gray-200/50 px-4 py-2 flex items-center gap-3">
            {isSyncing ? (
              <>
                <RefreshCw className="w-4 h-4 text-blue-600 animate-spin" />
                <span className="text-sm font-medium text-gray-700">Синхронизация...</span>
              </>
            ) : lastSyncTime ? (
              <>
                <CheckCircle2 className="w-4 h-4 text-green-600" />
                <span className="text-sm font-medium text-gray-700">
                  Обновлено: {formatTime(lastSyncTime)}
                </span>
              </>
            ) : null}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

