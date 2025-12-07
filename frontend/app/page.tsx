'use client'

import { useEffect, useState } from 'react'
import dynamic from 'next/dynamic'
import { fetchObjects, fetchStatsSummary, PipelineObject, StatsSummary } from '@/lib/api'
import { AlertTriangle, Activity, TrendingUp } from 'lucide-react'
import MetricCard from '@/components/dashboard/MetricCard'
import FiltersPanel from '@/components/dashboard/FiltersPanel'
import DefectsTable from '@/components/dashboard/DefectsTable'
import EventsFeed from '@/components/dashboard/EventsFeed'
import ChatAssistant from '@/components/ai/ChatAssistant'
import TopRisks from '@/components/charts/TopRisks'
import MethodsDistribution from '@/components/charts/MethodsDistribution'
import CriticalityDistribution from '@/components/charts/CriticalityDistribution'
import DefectsTimeline from '@/components/charts/DefectsTimeline'
import ThemeToggle from '@/components/common/ThemeToggle'
import LanguageToggle from '@/components/common/LanguageToggle'
import { motion } from 'framer-motion'
import { useMapContext } from '@/contexts/MapContext'
import { useApp } from '@/contexts/AppContext'
import { useAutoRefresh } from '@/hooks/useAutoRefresh'
import SyncIndicator from '@/components/common/SyncIndicator'
import { useLanguage } from '@/contexts/LanguageContext'
import { useTheme } from '@/contexts/ThemeContext'

// Динамический импорт карты (без SSR)
const MapWrapper = dynamic(() => import('@/components/map/MapWrapper'), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-full bg-gradient-to-br from-gray-50 to-gray-100 text-gray-500">
      <div className="text-lg font-medium">Загрузка карты...</div>
    </div>
  ),
})

function HomeContent() {
  const app = useApp()
  const mapContext = useMapContext()
  const { t } = useLanguage()
  const { theme } = useTheme()
  
  // Автоматическое обновление данных каждую минуту
  useAutoRefresh(60000)
  
  // Светлая тема как на других страницах
  const headerBgClass = 'bg-white/80 backdrop-blur-xl border-gray-200/50'

  // Синхронизируем фильтры между AppContext и MapContext
  useEffect(() => {
    const handleFilterChange = (event: CustomEvent) => {
      app.setFilters(event.detail)
    }

    window.addEventListener('mapFilterChanged', handleFilterChange as EventListener)
    return () => window.removeEventListener('mapFilterChanged', handleFilterChange as EventListener)
  }, [app])

  // Синхронизируем фильтры из AppContext в MapContext
  useEffect(() => {
    if (mapContext && app.state.filters !== mapContext.currentFilter) {
      mapContext.setFilter(app.state.filters)
    }
  }, [app.state.filters, mapContext])

  const { state, filteredObjects, criticalCount, totalDefects } = app
  const { stats } = state
  
  const mediumCount = stats?.criticality.medium || 0
  const normalCount = stats?.criticality.normal || filteredObjects.filter((o) => o.status === 'Normal').length
  const activeDefects = stats?.active_defects || totalDefects
  const repairsThisYear = stats?.repairs_this_year || 0

  // Белый фон как на других страницах
  const pageBgClass = 'bg-gradient-to-br from-gray-50 via-white to-gray-50'

  return (
    <div className={`flex flex-col h-full overflow-hidden`}>
        {/* Хедер с градиентом */}
        <motion.header
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className={`h-20 ${headerBgClass} border-b flex items-center justify-between px-8 shadow-sm`}
        >
          <div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-gray-900 via-gray-800 to-gray-900 bg-clip-text text-transparent">
              {t('dashboard')}
            </h1>
            <div className="flex items-center gap-2 mt-1">
              <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></div>
              <p className="text-sm text-gray-500 font-medium">
                {t('dashboard')}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3 relative z-[100]">
            <LanguageToggle />
            <ThemeToggle />
            <motion.div
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
              className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 flex items-center justify-center cursor-pointer shadow-lg hover:shadow-xl transition-all"
            >
              <span className="text-xs font-bold text-white">PM</span>
            </motion.div>
          </div>
        </motion.header>

        {/* Контент с прокруткой */}
        <div className="flex-1 overflow-y-auto p-8 space-y-8 bg-gradient-to-b from-transparent to-gray-50/50">
          {/* Карточки метрик */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
          >
            <MetricCard
              title={t('activeDefects')}
              value={activeDefects}
              icon={AlertTriangle}
              color="red"
              subtitle={`${criticalCount} ${t('critical')}`}
              trend={stats?.trends?.defects?.direction || undefined}
              trendValue={stats?.trends?.defects?.value || undefined}
            />
            <MetricCard
              title={t('highRisk')}
              value={criticalCount}
              icon={AlertTriangle}
              color="red"
              subtitle={t('requireAttention')}
            />
            <MetricCard
              title={t('examinations')}
              value={stats?.total_diagnostics || 0}
              icon={Activity}
              color="blue"
              subtitle={t('totalDiagnostics')}
              trend={stats?.trends?.diagnostics?.direction || undefined}
              trendValue={stats?.trends?.diagnostics?.value || undefined}
            />
            <MetricCard
              title={t('repairsThisYear')}
              value={repairsThisYear}
              icon={TrendingUp}
              color="green"
              subtitle={t('completedThisYear')}
            />
          </motion.div>

          {/* Фильтры */}
          <FiltersPanel />

          {/* Основной контент: карта и боковая панель */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Карта - занимает 2 колонки */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.3 }}
              className="lg:col-span-2"
            >
              <div className="bg-white/90 backdrop-blur-xl rounded-2xl shadow-xl shadow-gray-900/5 border border-gray-200/50 overflow-hidden h-[600px]">
                <MapWrapper />
              </div>
            </motion.div>

            {/* Боковая панель: события */}
            <div className="space-y-6">
              <EventsFeed />
            </div>
          </div>

          {/* Виджеты дашборда согласно ТЗ */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="grid grid-cols-1 lg:grid-cols-2 gap-6"
          >
            {/* Топ-5 рисков */}
            <TopRisks />

            {/* Распределение по критичности */}
            <CriticalityDistribution />
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="grid grid-cols-1 lg:grid-cols-2 gap-6"
          >
            {/* Распределение дефектов по методам */}
            <MethodsDistribution />

            {/* Динамика дефектов по годам */}
            <DefectsTimeline />
          </motion.div>

          {/* Таблица дефектов */}
          <DefectsTable objects={filteredObjects} />
        </div>

      {/* AI Assistant */}
      <ChatAssistant />
      
      {/* Индикатор синхронизации */}
      <SyncIndicator />
    </div>
  )
}

export default function Home() {
  return <HomeContent />
}
