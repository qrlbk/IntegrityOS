'use client'

import { useEffect, useState } from 'react'
import { fetchObjects, fetchStatsSummary, fetchTopRisks, fetchDiagnostics, PipelineObject, StatsSummary, TopRisk, Diagnostic } from '@/lib/api'
import dynamic from 'next/dynamic'

// Динамический импорт карты для мини-карты в отчете
const MapWrapper = dynamic(() => import('@/components/map/MapWrapper'), {
  ssr: false,
})

interface FullReportProps {
  includeMap?: boolean
}

export default function FullReport({ includeMap = true }: FullReportProps) {
  const [objects, setObjects] = useState<PipelineObject[]>([])
  const [stats, setStats] = useState<StatsSummary | null>(null)
  const [topRisks, setTopRisks] = useState<TopRisk[]>([])
  const [allDefects, setAllDefects] = useState<Array<{object: PipelineObject, diagnostic: Diagnostic}>>([])
  const [loading, setLoading] = useState(true)
  const [sortConfig, setSortConfig] = useState<{key: string, direction: 'asc' | 'desc'}>({key: 'ml_label', direction: 'desc'})

  useEffect(() => {
    const loadData = async () => {
      try {
        const [objectsData, statsData, risksData] = await Promise.all([
          fetchObjects(),
          fetchStatsSummary(),
          fetchTopRisks(10),
        ])
        setObjects(objectsData)
        setStats(statsData)
        setTopRisks(risksData)

        // Загружаем диагностики для всех объектов с дефектами (асинхронно, чтобы не блокировать UI)
        const objectsWithDefects = objectsData.filter((o) => o.status === 'Critical')
        const defectsData: Array<{object: PipelineObject, diagnostic: Diagnostic}> = []
        
        // Ограничиваем количество для производительности
        const objectsToProcess = objectsWithDefects.slice(0, 50)
        
        // Загружаем диагностики параллельно (по 10 за раз)
        const batchSize = 10
        for (let i = 0; i < objectsToProcess.length; i += batchSize) {
          const batch = objectsToProcess.slice(i, i + batchSize)
          const batchPromises = batch.map(async (obj) => {
            try {
              const diagnostics = await fetchDiagnostics(obj.id)
              const criticalDiagnostics = diagnostics
                .filter(d => d.defect_found && (d.ml_label === 'high' || d.ml_label === 'medium'))
                .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()) // Сортируем по дате, новые первыми
              
              if (criticalDiagnostics.length > 0) {
                return {
                  object: obj,
                  diagnostic: criticalDiagnostics[0] // Берем последнюю критическую диагностику
                }
              }
              return null
            } catch (error) {
              console.error(`Ошибка загрузки диагностик для объекта ${obj.id}:`, error)
              return null
            }
          })
          
          const batchResults = await Promise.all(batchPromises)
          defectsData.push(...batchResults.filter((item): item is {object: PipelineObject, diagnostic: Diagnostic} => item !== null))
        }
        
        setAllDefects(defectsData)
      } catch (error) {
        console.error('Ошибка загрузки данных для отчета:', error)
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [])

  useEffect(() => {
    // Автоматическая печать при загрузке
    const timer = setTimeout(() => {
      window.print()
    }, 1000)
    return () => clearTimeout(timer)
  }, [])

  const currentDate = new Date().toLocaleDateString('ru-RU', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })

  // Получаем все объекты с дефектами
  const objectsWithDefects = objects.filter((o) => o.status === 'Critical')
  const recommendedExcavations = topRisks.filter((risk) => risk.high_defects_count > 0)

  // Сортировка дефектов
  const sortedDefects = [...allDefects].sort((a, b) => {
    const aValue = a.diagnostic[sortConfig.key as keyof Diagnostic] || ''
    const bValue = b.diagnostic[sortConfig.key as keyof Diagnostic] || ''
    
    if (sortConfig.key === 'ml_label') {
      const order = { 'high': 3, 'medium': 2, 'normal': 1 }
      const aOrder = order[a.diagnostic.ml_label as keyof typeof order] || 0
      const bOrder = order[b.diagnostic.ml_label as keyof typeof order] || 0
      return sortConfig.direction === 'asc' ? aOrder - bOrder : bOrder - aOrder
    }
    
    if (typeof aValue === 'number' && typeof bValue === 'number') {
      return sortConfig.direction === 'asc' ? aValue - bValue : bValue - aValue
    }
    
    const aStr = String(aValue).toLowerCase()
    const bStr = String(bValue).toLowerCase()
    if (sortConfig.direction === 'asc') {
      return aStr < bStr ? -1 : aStr > bStr ? 1 : 0
    } else {
      return aStr > bStr ? -1 : aStr < bStr ? 1 : 0
    }
  })

  if (loading) {
    return (
      <div className="p-8 max-w-6xl mx-auto bg-white text-black">
        <p>Загрузка данных для отчета...</p>
      </div>
    )
  }

  return (
    <div className="print-document p-8 max-w-6xl mx-auto bg-white text-black">
      {/* Шапка документа */}
      <div className="text-center mb-8 border-b-2 border-black pb-4">
        <h1 className="text-3xl font-bold mb-2">ОТЧЕТ О ТЕХНИЧЕСКОМ СОСТОЯНИИ</h1>
        <p className="text-lg">магистральных трубопроводов</p>
        <p className="text-sm mt-2">Дата формирования: {currentDate}</p>
      </div>

      {/* Общая статистика */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold mb-4">1. Общая статистика</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <div className="border border-gray-800 p-4 text-center">
            <p className="text-sm text-gray-600 mb-1">Всего объектов</p>
            <p className="text-2xl font-bold">{stats?.total_objects || objects.length}</p>
          </div>
          <div className="border border-gray-800 p-4 text-center">
            <p className="text-sm text-gray-600 mb-1">Диагностик</p>
            <p className="text-2xl font-bold">{stats?.total_diagnostics || 0}</p>
          </div>
          <div className="border border-gray-800 p-4 text-center">
            <p className="text-sm text-gray-600 mb-1">Дефектов</p>
            <p className="text-2xl font-bold text-red-600">{stats?.total_defects || 0}</p>
          </div>
          <div className="border border-gray-800 p-4 text-center">
            <p className="text-sm text-gray-600 mb-1">% дефектов</p>
            <p className="text-2xl font-bold">{stats?.defects_percentage.toFixed(1) || 0}%</p>
          </div>
        </div>

        {/* Распределение по критичности */}
        {stats && (
          <div className="border border-gray-800 p-4">
            <h3 className="text-lg font-semibold mb-3">Распределение по критичности</h3>
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center">
                <p className="text-sm text-gray-600 mb-1">Высокий риск</p>
                <p className="text-xl font-bold text-red-600">{stats.criticality.high}</p>
              </div>
              <div className="text-center">
                <p className="text-sm text-gray-600 mb-1">Средний риск</p>
                <p className="text-xl font-bold text-yellow-600">{stats.criticality.medium}</p>
              </div>
              <div className="text-center">
                <p className="text-sm text-gray-600 mb-1">Норма</p>
                <p className="text-xl font-bold text-green-600">{stats.criticality.normal}</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Таблица дефектов */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold mb-4">2. Таблица дефектов</h2>
        <div className="mb-4 text-sm text-gray-600">
          <p>Всего дефектов: {sortedDefects.length} | Сортировка: {sortConfig.key === 'ml_label' ? 'Критичность' : sortConfig.key} ({sortConfig.direction === 'asc' ? 'по возрастанию' : 'по убыванию'})</p>
        </div>
        <div className="border border-gray-800 overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="bg-gray-200">
                <th className="border border-gray-800 p-2 text-left">№</th>
                <th 
                  className="border border-gray-800 p-2 text-left cursor-pointer hover:bg-gray-300"
                  onClick={() => setSortConfig({key: 'ml_label', direction: sortConfig.key === 'ml_label' && sortConfig.direction === 'desc' ? 'asc' : 'desc'})}
                >
                  Критичность {sortConfig.key === 'ml_label' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                </th>
                <th className="border border-gray-800 p-2 text-left">Объект</th>
                <th className="border border-gray-800 p-2 text-left">Тип</th>
                <th className="border border-gray-800 p-2 text-left">Метод</th>
                <th 
                  className="border border-gray-800 p-2 text-left cursor-pointer hover:bg-gray-300"
                  onClick={() => setSortConfig({key: 'date', direction: sortConfig.key === 'date' && sortConfig.direction === 'desc' ? 'asc' : 'desc'})}
                >
                  Дата {sortConfig.key === 'date' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                </th>
                <th 
                  className="border border-gray-800 p-2 text-left cursor-pointer hover:bg-gray-300"
                  onClick={() => setSortConfig({key: 'param1', direction: sortConfig.key === 'param1' && sortConfig.direction === 'desc' ? 'asc' : 'desc'})}
                >
                  Параметр 1 {sortConfig.key === 'param1' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                </th>
                <th className="border border-gray-800 p-2 text-left">Описание</th>
              </tr>
            </thead>
            <tbody>
              {sortedDefects.length > 0 ? (
                sortedDefects.slice(0, 100).map((item, index) => {
                  const getCriticalityColor = (label?: string | null) => {
                    if (label === 'high') return 'text-red-600 font-bold'
                    if (label === 'medium') return 'text-yellow-600 font-semibold'
                    return 'text-green-600'
                  }
                  
                  const getCriticalityText = (label?: string | null) => {
                    if (label === 'high') return 'ВЫСОКИЙ'
                    if (label === 'medium') return 'СРЕДНИЙ'
                    return 'НОРМА'
                  }
                  
                  return (
                    <tr key={`${item.object.id}-${item.diagnostic.diag_id}`} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                      <td className="border border-gray-800 p-2">{index + 1}</td>
                      <td className="border border-gray-800 p-2">
                        <span className={getCriticalityColor(item.diagnostic.ml_label)}>
                          {getCriticalityText(item.diagnostic.ml_label)}
                        </span>
                      </td>
                      <td className="border border-gray-800 p-2">{item.object.name}</td>
                      <td className="border border-gray-800 p-2">{item.object.type}</td>
                      <td className="border border-gray-800 p-2">{item.diagnostic.method}</td>
                      <td className="border border-gray-800 p-2 text-sm">
                        {new Date(item.diagnostic.date).toLocaleDateString('ru-RU')}
                      </td>
                      <td className="border border-gray-800 p-2 text-sm">
                        {item.diagnostic.param1 !== null && item.diagnostic.param1 !== undefined 
                          ? item.diagnostic.param1.toFixed(2) 
                          : '-'}
                      </td>
                      <td className="border border-gray-800 p-2 text-sm max-w-xs truncate" title={item.diagnostic.defect_description || ''}>
                        {item.diagnostic.defect_description || '-'}
                      </td>
                    </tr>
                  )
                })
              ) : (
                <tr>
                  <td colSpan={8} className="border border-gray-800 p-4 text-center text-gray-500">
                    Дефектов не обнаружено
                  </td>
                </tr>
              )}
            </tbody>
          </table>
          {sortedDefects.length > 100 && (
            <p className="p-2 text-sm text-gray-600 text-center">
              Показано 100 из {sortedDefects.length} дефектов
            </p>
          )}
        </div>
      </div>

      {/* Рекомендуемые раскопки */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold mb-4">3. Рекомендуемые раскопки</h2>
        <p className="text-sm text-gray-600 mb-4">
          Объекты с высоким уровнем критичности, требующие немедленного вмешательства
        </p>
        {recommendedExcavations.length > 0 ? (
          <div className="border border-gray-800">
            <table className="w-full border-collapse">
              <thead>
                <tr className="bg-red-100">
                  <th className="border border-gray-800 p-2 text-left">№</th>
                  <th className="border border-gray-800 p-2 text-left">Объект</th>
                  <th className="border border-gray-800 p-2 text-left">Тип</th>
                  <th className="border border-gray-800 p-2 text-left">Координаты</th>
                  <th className="border border-gray-800 p-2 text-left">Критических дефектов</th>
                  <th className="border border-gray-800 p-2 text-left">Приоритет</th>
                </tr>
              </thead>
              <tbody>
                {recommendedExcavations.map((risk, index) => (
                  <tr key={risk.object_id} className={index % 2 === 0 ? 'bg-gray-50' : ''}>
                    <td className="border border-gray-800 p-2">{index + 1}</td>
                    <td className="border border-gray-800 p-2 font-semibold">{risk.object_name}</td>
                    <td className="border border-gray-800 p-2">{risk.object_type}</td>
                    <td className="border border-gray-800 p-2 text-sm">
                      {risk.lat.toFixed(6)}, {risk.lon.toFixed(6)}
                    </td>
                    <td className="border border-gray-800 p-2 text-center">
                      <span className="text-red-600 font-bold text-lg">{risk.high_defects_count}</span>
                    </td>
                    <td className="border border-gray-800 p-2">
                      <span className="bg-red-600 text-white px-2 py-1 rounded text-sm font-semibold">
                        ВЫСОКИЙ
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="border border-gray-800 p-4 text-center text-gray-500">
            Объектов, требующих раскопок, не обнаружено
          </div>
        )}
      </div>

      {/* Карта участка */}
      {includeMap && (
        <div className="mb-8">
          <h2 className="text-2xl font-bold mb-4">4. Карта участка</h2>
          <div className="border border-gray-800" style={{ height: '400px', width: '100%' }}>
            <MapWrapper />
          </div>
          <p className="text-sm text-gray-600 mt-2">
            Красные маркеры - объекты с критическими дефектами, зеленые - нормальные
          </p>
        </div>
      )}

      {/* Заключение */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold mb-4">5. Заключение</h2>
        <div className="border border-gray-800 p-4">
          <p className="mb-2">
            На основании проведенного анализа технического состояния магистральных трубопроводов выявлено:
          </p>
          <ul className="list-disc list-inside space-y-1 mb-4">
            <li>Всего объектов: {stats?.total_objects || objects.length}</li>
            <li>Объектов с дефектами: {objectsWithDefects.length}</li>
            <li>Критических объектов: {stats?.criticality.high || 0}</li>
            <li>Рекомендуется раскопка: {recommendedExcavations.length} объектов</li>
          </ul>
          <p className="font-semibold">
            Рекомендации: Необходимо провести немедленное обследование объектов из раздела "Рекомендуемые раскопки"
            для предотвращения аварийных ситуаций.
          </p>
        </div>
      </div>

      {/* Подписи */}
      <div className="mt-12">
        <div className="flex justify-between mb-8">
          <div className="w-1/2">
            <p className="mb-2 border-t-2 border-black pt-2">Составил отчет:</p>
            <p className="text-sm text-gray-600 mt-8">Подпись: _________________</p>
          </div>
          <div className="w-1/2 ml-4">
            <p className="mb-2 border-t-2 border-black pt-2">Утвердил:</p>
            <p className="text-sm text-gray-600 mt-8">Подпись: _________________</p>
          </div>
        </div>
        <div className="text-right text-sm text-gray-600">
          <p>Дата формирования: {currentDate}</p>
        </div>
      </div>

      {/* Кнопка закрытия (не печатается) */}
      <div className="no-print mt-8 text-center">
        <button
          onClick={() => window.close()}
          className="bg-gray-600 text-white px-6 py-2 rounded hover:bg-gray-700"
        >
          Закрыть окно
        </button>
      </div>
    </div>
  )
}


