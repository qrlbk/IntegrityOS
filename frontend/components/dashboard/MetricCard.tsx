'use client'

import { LucideIcon, TrendingUp, TrendingDown } from 'lucide-react'
import { motion } from 'framer-motion'
import { useTheme } from '@/contexts/ThemeContext'

interface MetricCardProps {
  title: string
  value: number | string
  icon: LucideIcon
  color: 'red' | 'blue' | 'green' | 'yellow' | 'purple'
  subtitle?: string
  trend?: 'up' | 'down'
  trendValue?: string
}

export default function MetricCard({ 
  title, 
  value, 
  icon: Icon, 
  color, 
  subtitle,
  trend,
  trendValue 
}: MetricCardProps) {
  // Принудительно используем светлые цветные фоны для белого фона страницы
  const colorConfig = {
    red: {
      bg: 'bg-red-50 border-red-200 shadow-md',
      border: 'border-red-200',
      iconBg: 'bg-red-500',
      text: 'text-red-600',
      accent: 'bg-red-500',
    },
    blue: {
      bg: 'bg-blue-50 border-blue-200 shadow-md',
      border: 'border-blue-200',
      iconBg: 'bg-blue-500',
      text: 'text-blue-600',
      accent: 'bg-blue-500',
    },
    green: {
      bg: 'bg-green-50 border-green-200 shadow-md',
      border: 'border-green-200',
      iconBg: 'bg-green-500',
      text: 'text-green-600',
      accent: 'bg-green-500',
    },
    yellow: {
      bg: 'bg-yellow-50 border-yellow-200 shadow-md',
      border: 'border-yellow-200',
      iconBg: 'bg-yellow-500',
      text: 'text-yellow-600',
      accent: 'bg-yellow-500',
    },
    purple: {
      bg: 'bg-purple-50 border-purple-200 shadow-md',
      border: 'border-purple-200',
      iconBg: 'bg-purple-500',
      text: 'text-purple-600',
      accent: 'bg-purple-500',
    },
  }

  const config = colorConfig[color]

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -4, scale: 1.02 }}
      transition={{ duration: 0.3 }}
      className={`relative ${config.bg} rounded-2xl border ${config.border} p-6 overflow-hidden group cursor-pointer transition-all duration-300`}
    >
      {/* Содержимое */}
      <div className="relative z-10">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <p className="text-sm font-semibold text-gray-700 mb-1">{title}</p>
            <div className="flex items-baseline gap-2">
              <motion.p
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: 0.1, type: "spring" }}
                className="text-4xl font-bold text-gray-900"
              >
                {typeof value === 'number' ? value.toLocaleString() : value}
              </motion.p>
              {trend && trendValue && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.2 }}
                  className={`flex items-center gap-1 text-xs font-semibold ${
                    trend === 'up' ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  {trend === 'up' ? (
                    <TrendingUp className="w-3 h-3" />
                  ) : (
                    <TrendingDown className="w-3 h-3" />
                  )}
                  <span>{trendValue}</span>
                </motion.div>
              )}
            </div>
            {subtitle && (
              <p className="text-xs text-gray-600 mt-2 font-medium">{subtitle}</p>
            )}
          </div>
          
          {/* Иконка */}
          <motion.div
            whileHover={{ scale: 1.05 }}
            className={`${config.iconBg} w-14 h-14 rounded-xl flex items-center justify-center shadow-md transition-shadow`}
          >
            <Icon className="w-7 h-7 text-white" />
          </motion.div>
        </div>
      </div>

      {/* Декоративная линия внизу */}
      <div className={`absolute bottom-0 left-0 right-0 h-1 ${config.accent} opacity-0 group-hover:opacity-100 transition-opacity duration-300`}></div>
    </motion.div>
  )
}
