'use client'

import { useState, useEffect } from 'react'
import { Calendar, Plus, Filter, X } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useMapContext } from '@/contexts/MapContext'
import { useApp } from '@/contexts/AppContext'
import { fetchObjects } from '@/lib/api'

export default function FiltersPanel() {
  const app = useApp()
  const [selectedPipeline, setSelectedPipeline] = useState('')
  const [selectedStatus, setSelectedStatus] = useState('')
  const [selectedMethod, setSelectedMethod] = useState('')
  const [showFilters, setShowFilters] = useState(true)
  const [availablePipelines, setAvailablePipelines] = useState<string[]>([])

  // Загружаем список доступных трубопроводов из AppContext
  useEffect(() => {
    const pipelines = [...new Set(app.state.objects.map(obj => obj.pipeline_id).filter(Boolean))] as string[]
    setAvailablePipelines(pipelines)
  }, [app.state.objects])

  const activeFiltersCount = [selectedPipeline, selectedStatus, selectedMethod].filter(Boolean).length

  const handleApplyFilters = async () => {
    try {
      const filters: any = {}
      
      if (selectedPipeline) {
        filters.pipeline_id = selectedPipeline
      }
      
      if (selectedMethod) {
        filters.method = selectedMethod
      }
      
      if (selectedStatus) {
        if (selectedStatus === 'critical') {
          filters.risk_level = 'high'
        } else if (selectedStatus === 'active') {
          filters.risk_level = 'medium'
        }
      }

      // Применяем фильтры через AppContext (который синхронизируется с MapContext)
      app.setFilters(filters)
    } catch (error) {
      console.error('Ошибка применения фильтров:', error)
    }
  }

  const handleClearFilters = () => {
    setSelectedPipeline('')
    setSelectedStatus('')
    setSelectedMethod('')
    
    // Очищаем фильтры через AppContext
    app.setFilters(null)
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-2xl border border-gray-200 shadow-lg p-5"
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-sky-500 flex items-center justify-center shadow-lg shadow-blue-400/30">
            <Filter className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-gray-900">Фильтры</h3>
            {activeFiltersCount > 0 && (
              <span className="text-xs text-gray-500">{activeFiltersCount} активных</span>
            )}
          </div>
        </div>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="text-gray-500 hover:text-blue-500 transition-colors"
        >
          {showFilters ? <X className="w-5 h-5" /> : <Plus className="w-5 h-5" />}
        </button>
      </div>

      <AnimatePresence>
        {showFilters && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="flex items-center gap-3 flex-wrap overflow-hidden"
          >
            {/* Трубопровод */}
            <select
              value={selectedPipeline}
              onChange={(e) => setSelectedPipeline(e.target.value)}
              className="px-4 py-2.5 bg-white border-2 border-gray-200 rounded-xl text-sm font-medium text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent hover:border-gray-300 transition-all cursor-pointer appearance-none bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAiIGhlaWdodD0iNiIgdmlld0JveD0iMCAwIDEwIDYiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xIDFMNSA1TDkgMSIgc3Ryb2tlPSIjOUI5Q0E1IiBzdHJva2Utd2lkdGg9IjEuNSIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=')] bg-no-repeat bg-right-3 pr-10"
            >
              <option value="">Все трубопроводы</option>
              {availablePipelines.map(pipeline => (
                <option key={pipeline} value={pipeline}>{pipeline}</option>
              ))}
            </select>

            {/* Статус */}
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="px-4 py-2.5 bg-white border-2 border-gray-200 rounded-xl text-sm font-medium text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent hover:border-gray-300 transition-all cursor-pointer appearance-none bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAiIGhlaWdodD0iNiIgdmlld0JveD0iMCAwIDEwIDYiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xIDFMNSA1TDkgMSIgc3Ryb2tlPSIjOUI5Q0E1IiBzdHJva2Utd2lkdGg9IjEuNSIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=')] bg-no-repeat bg-right-3 pr-10"
            >
              <option value="">Все статусы</option>
              <option value="critical">Критический</option>
              <option value="active">Активен</option>
              <option value="repaired">Исправлен</option>
            </select>

            {/* Метод */}
            <select
              value={selectedMethod}
              onChange={(e) => setSelectedMethod(e.target.value)}
              className="px-4 py-2.5 bg-white border-2 border-gray-200 rounded-xl text-sm font-medium text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent hover:border-gray-300 transition-all cursor-pointer appearance-none bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAiIGhlaWdodD0iNiIgdmlld0JveD0iMCAwIDEwIDYiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xIDFMNSA1TDkgMSIgc3Ryb2tlPSIjOUI5Q0E1IiBzdHJva2Utd2lkdGg9IjEuNSIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=')] bg-no-repeat bg-right-3 pr-10"
            >
              <option value="">Все методы</option>
              <option value="VIK">VIK</option>
              <option value="MFL">MFL</option>
              <option value="UTWM">UTWM</option>
              <option value="UT">UT</option>
              <option value="EC">EC</option>
              <option value="PVK">PVK</option>
              <option value="MPK">MPK</option>
              <option value="UZK">UZK</option>
              <option value="RGK">RGK</option>
              <option value="TVK">TVK</option>
              <option value="VIBRO">VIBRO</option>
              <option value="TFI">TFI</option>
              <option value="GEO">GEO</option>
            </select>

            {/* Кнопки */}
            <div className="flex items-center gap-2">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleApplyFilters}
                className="px-6 py-2.5 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl hover:from-blue-700 hover:to-purple-700 transition-all text-sm font-semibold shadow-lg shadow-blue-500/25 hover:shadow-xl hover:shadow-blue-500/40"
              >
                Применить
              </motion.button>
              
              {activeFiltersCount > 0 && (
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={handleClearFilters}
                  className="px-4 py-2.5 bg-gray-100 text-gray-700 rounded-xl hover:bg-gray-200 transition-all text-sm font-semibold"
                >
                  Сбросить
                </motion.button>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}
