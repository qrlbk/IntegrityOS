'use client'

import { PipelineObject } from '@/lib/api'
import { motion } from 'framer-motion'
import { AlertCircle, CheckCircle2, Clock } from 'lucide-react'
import { useMapContext } from '@/contexts/MapContext'
import { useApp } from '@/contexts/AppContext'

interface DefectsTableProps {
  objects: PipelineObject[]
}

export default function DefectsTable({ objects }: DefectsTableProps) {
  const defects = objects.filter((obj) => obj.status === 'Critical')
  const mapContext = useMapContext()

  const handleRowClick = (object: PipelineObject) => {
    if (mapContext && (object.lat !== undefined && object.lat !== null) && (object.lon !== undefined && object.lon !== null)) {
      mapContext.flyTo({
        lat: object.lat,
        lon: object.lon,
        zoom: 15,
        objectId: object.id,
        duration: 1.0, // Быстрое перемещение (1 секунда)
      })
      // Подсвечиваем маркер
      mapContext.highlightMarker(object.id)
    }
  }

  const getRiskClass = (status: string) => {
    if (status === 'Critical') {
      return { 
        label: 'Высокий', 
        color: 'text-red-600', 
        dot: 'bg-red-500',
        bg: 'bg-red-50',
        border: 'border-red-200'
      }
    }
    return { 
      label: 'Низкий', 
      color: 'text-green-600', 
      dot: 'bg-green-500',
      bg: 'bg-green-50',
      border: 'border-green-200'
    }
  }

  const getStatusBadge = (status: string) => {
    if (status === 'Critical') {
      return {
        label: 'Активен',
        icon: AlertCircle,
        className: 'bg-red-100 text-red-700 border-red-200'
      }
    }
    return {
      label: 'Исправлен',
      icon: CheckCircle2,
      className: 'bg-green-100 text-green-700 border-green-200'
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3 }}
      className="bg-white rounded-2xl border border-gray-200 shadow-xl shadow-gray-900/5 overflow-hidden"
    >
      {/* Заголовок */}
      <div className="px-6 py-5 border-b border-gray-200 bg-gray-50/50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-orange-500 via-rose-500 to-amber-500 flex items-center justify-center shadow-lg shadow-orange-400/30">
              <AlertCircle className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-gray-900">Дефекты</h2>
              <p className="text-xs text-gray-500">Всего: {defects.length}</p>
            </div>
          </div>
          <button className="px-4 py-2 text-sm font-semibold text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-all">
            Экспорт
          </button>
        </div>
      </div>

      {/* Таблица */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-gradient-to-r from-gray-50 to-gray-100/50 border-b border-gray-200">
              <th className="px-6 py-4 text-left text-xs font-bold text-gray-600 uppercase tracking-wider">
                №
              </th>
              <th className="px-6 py-4 text-left text-xs font-bold text-gray-600 uppercase tracking-wider">
                Трубопровод
              </th>
              <th className="px-6 py-4 text-left text-xs font-bold text-gray-600 uppercase tracking-wider">
                Активен
              </th>
              <th className="px-6 py-4 text-left text-xs font-bold text-gray-600 uppercase tracking-wider">
                Статус
              </th>
              <th className="px-6 py-4 text-left text-xs font-bold text-gray-600 uppercase tracking-wider">
                Метод
              </th>
              <th className="px-6 py-4 text-left text-xs font-bold text-gray-600 uppercase tracking-wider">
                Класс риска
              </th>
              <th className="px-6 py-4 text-left text-xs font-bold text-gray-600 uppercase tracking-wider">
                Дата
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {defects.length > 0 ? (
              defects.slice(0, 10).map((defect, index) => {
                const riskClass = getRiskClass(defect.status)
                const statusBadge = getStatusBadge(defect.status)
                const StatusIcon = statusBadge.icon
                
                return (
                  <motion.tr
                    key={defect.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
                    whileHover={{ 
                      backgroundColor: 'rgba(59, 130, 246, 0.05)',
                      scale: 1.01,
                      transition: { duration: 0.2 }
                    }}
                    onClick={() => handleRowClick(defect)}
                    className="group cursor-pointer transition-all hover:shadow-md"
                  >
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm font-semibold text-gray-900">#{index + 1}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm font-semibold text-gray-900">
                        {defect.pipeline_id || 'TP-1'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold border ${statusBadge.className}`}>
                        <StatusIcon className="w-3 h-3" />
                        {statusBadge.label}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold border ${statusBadge.className}`}>
                        <StatusIcon className="w-3 h-3" />
                        {statusBadge.label}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-3 py-1.5 bg-blue-50 text-blue-700 rounded-lg text-xs font-semibold border border-blue-200">
                        MFL
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <motion.div
                        whileHover={{ scale: 1.1 }}
                        className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-bold ${riskClass.bg} ${riskClass.color} border ${riskClass.border}`}
                      >
                        <motion.div
                          animate={{ scale: [1, 1.2, 1] }}
                          transition={{ repeat: Infinity, duration: 2 }}
                          className={`w-2 h-2 rounded-full ${riskClass.dot} shadow-lg`}
                        />
                        {riskClass.label}
                      </motion.div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2 text-sm text-gray-600">
                        <Clock className="w-4 h-4 text-gray-400" />
                        {new Date().toLocaleDateString('ru-RU')}
                      </div>
                    </td>
                  </motion.tr>
                )
              })
            ) : (
              <tr>
                <td colSpan={7} className="px-6 py-12 text-center">
                  <div className="flex flex-col items-center gap-3">
                    <div className="w-16 h-16 rounded-full bg-gray-100 flex items-center justify-center">
                      <CheckCircle2 className="w-8 h-8 text-gray-400" />
                    </div>
                    <p className="text-sm font-medium text-gray-500">Дефектов не обнаружено</p>
                  </div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </motion.div>
  )
}
