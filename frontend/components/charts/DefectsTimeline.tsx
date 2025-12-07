'use client'

import { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import axios from 'axios'
import { useLanguage } from '@/contexts/LanguageContext'

interface TimelineData {
  year: number
  total: number
  defects: number
  percentage: number
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function DefectsTimeline() {
  const [data, setData] = useState<TimelineData[]>([])
  const [loading, setLoading] = useState(true)
  const { t } = useLanguage()
  
  // Принудительно используем светлую тему для белого фона
  const bgClass = 'bg-white border-gray-200 shadow-lg'
  const textClass = 'text-gray-900'
  const textSecondaryClass = 'text-gray-600'

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/api/analytics/defects-timeline`)
        setData(response.data)
      } catch (error) {
        console.error('Ошибка загрузки данных графика:', error)
        // Данные для демо, если API не работает
        setData([
          { year: 2023, total: 500, defects: 120, percentage: 24 },
          { year: 2024, total: 600, defects: 180, percentage: 30 },
          { year: 2025, total: 700, defects: 250, percentage: 35.7 },
        ])
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  if (loading) {
    return (
      <div className={`${bgClass} border rounded-2xl p-6 shadow-lg`}>
        <p className={textSecondaryClass}>{t('loading')}</p>
      </div>
    )
  }

  const tooltipBg = '#FFFFFF'
  const tooltipBorder = '#E5E7EB'
  const tooltipText = '#111827'
  const gridColor = '#E5E7EB'
  const axisColor = '#6B7280'

  return (
    <div className={`${bgClass} border rounded-2xl p-6 shadow-lg`}>
      <h3 className={`text-xl font-bold ${textClass} mb-4`}>{t('defectsTimeline')}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
          <XAxis 
            dataKey="year" 
            stroke={axisColor}
            style={{ fontSize: '12px' }}
          />
          <YAxis 
            stroke={axisColor}
            style={{ fontSize: '12px' }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: tooltipBg,
              border: `1px solid ${tooltipBorder}`,
              borderRadius: '8px',
              color: tooltipText,
            }}
            labelStyle={{ color: axisColor }}
          />
          <Legend wrapperStyle={{ color: axisColor, fontSize: '12px' }} />
          <Line
            type="monotone"
            dataKey="defects"
            stroke="#EF4444"
            strokeWidth={3}
            name="Дефекты"
            dot={{ fill: '#EF4444', r: 4 }}
            activeDot={{ r: 6 }}
          />
          <Line
            type="monotone"
            dataKey="total"
            stroke="#60A5FA"
            strokeWidth={2}
            name="Всего диагностик"
            strokeDasharray="5 5"
            dot={{ fill: '#60A5FA', r: 3 }}
          />
        </LineChart>
      </ResponsiveContainer>
      <p className={`text-sm ${textSecondaryClass} mt-4`}>
        {data.length > 0 && `В ${data[data.length - 1]?.year} году обнаружено ${data[data.length - 1]?.defects} дефектов из ${data[data.length - 1]?.total} диагностик.`}
      </p>
    </div>
  )
}


