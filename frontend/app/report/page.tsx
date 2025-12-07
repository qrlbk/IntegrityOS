'use client'

import dynamic from 'next/dynamic'
import FullReport from '@/components/print/FullReport'
import { motion } from 'framer-motion'

// Динамический импорт для избежания проблем с SSR
const FullReportDynamic = dynamic(() => import('@/components/print/FullReport'), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-gray-50 to-white">
      <div className="text-lg font-medium text-gray-600">Загрузка отчета...</div>
    </div>
  ),
})

export default function ReportPage() {
  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      className="flex-1 overflow-y-auto h-full"
    >
      <div className="min-h-full bg-white">
        <FullReportDynamic includeMap={true} />
      </div>
    </motion.div>
  )
}
