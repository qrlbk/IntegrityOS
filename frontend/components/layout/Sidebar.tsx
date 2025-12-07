'use client'

import { usePathname } from 'next/navigation'
import Link from 'next/link'
import { LayoutDashboard, Upload, FileText, Settings, Activity, Sparkles } from 'lucide-react'
import { motion } from 'framer-motion'
import { useLanguage } from '@/contexts/LanguageContext'

export default function Sidebar() {
  const pathname = usePathname()
  const { t } = useLanguage()

  const menuItems = [
    {
      name: t('dashboard'),
      href: '/',
      icon: LayoutDashboard,
      active: pathname === '/',
      gradient: 'from-blue-500 to-cyan-500',
    },
    {
      name: t('newImport'),
      href: '/import',
      icon: Upload,
      active: pathname === '/import',
      gradient: 'from-purple-500 to-pink-500',
    },
    {
      name: t('reports'),
      href: '/report',
      icon: FileText,
      active: pathname === '/report',
      gradient: 'from-orange-500 to-red-500',
    },
    {
      name: t('settings'),
      href: '/settings',
      icon: Settings,
      active: pathname === '/settings',
      gradient: 'from-gray-500 to-gray-600',
    },
  ]

  return (
    <aside className="fixed left-0 top-0 h-full w-72 bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900 border-r border-slate-700/50 backdrop-blur-xl flex flex-col z-50 shadow-2xl">
      {/* Логотип/Заголовок с эффектом */}
      <div className="relative p-6 border-b border-slate-700/50 overflow-hidden">
        {/* Анимированный фон */}
        <div className="absolute inset-0 bg-gradient-to-r from-blue-600/10 via-purple-600/10 to-pink-600/10 animate-pulse"></div>
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(59,130,246,0.1),transparent_70%)]"></div>
        
        <div className="relative flex items-center gap-4">
          <motion.div
            whileHover={{ scale: 1.1, rotate: 5 }}
            whileTap={{ scale: 0.95 }}
            className="relative"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 rounded-2xl blur-xl opacity-50 animate-pulse"></div>
            <div className="relative w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-2xl">
              <Activity className="w-7 h-7 text-white" />
              <div className="absolute -top-1 -right-1">
                <Sparkles className="w-4 h-4 text-yellow-400 animate-pulse" />
              </div>
            </div>
          </motion.div>
          <div>
            <h2 className="text-white font-bold text-xl bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
              IntegrityOS
            </h2>
            <p className="text-slate-400 text-xs font-medium mt-0.5">{t('monitoringSystem')}</p>
          </div>
        </div>
      </div>

      {/* Меню с анимациями */}
      <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
        {menuItems.map((item, index) => {
          const Icon = item.icon
          return (
            <motion.div
              key={item.href}
              initial={{ x: -20, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ delay: index * 0.1 }}
            >
              <Link href={item.href}>
                <motion.div
                  whileHover={{ x: 4, scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className={`group relative flex items-center gap-4 px-4 py-3.5 rounded-xl transition-all duration-300 ${
                    item.active
                      ? 'bg-gradient-to-r from-slate-800 to-slate-700/50 text-white shadow-lg shadow-blue-500/20 border border-slate-600/50'
                      : 'text-slate-400 hover:bg-slate-800/50 hover:text-white'
                  }`}
                >
                  {/* Активный индикатор */}
                  {item.active && (
                    <motion.div
                      layoutId="activeIndicator"
                      className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-10 bg-gradient-to-b from-blue-500 to-purple-500 rounded-r-full shadow-lg shadow-blue-500/50"
                    />
                  )}
                  
                  {/* Иконка с градиентом */}
                  <div className={`relative ${item.active ? `bg-gradient-to-br ${item.gradient}` : 'bg-slate-700/50'} w-10 h-10 rounded-lg flex items-center justify-center transition-all duration-300 group-hover:scale-110`}>
                    <Icon className="w-5 h-5 text-white" />
                    {item.active && (
                      <div className="absolute inset-0 bg-white/20 rounded-lg blur-sm"></div>
                    )}
                  </div>
                  
                  <span className="font-semibold text-sm flex-1">{item.name}</span>
                  
                  {/* Анимированная точка для активного элемента */}
                  {item.active && (
                    <motion.div
                      animate={{ scale: [1, 1.2, 1] }}
                      transition={{ repeat: Infinity, duration: 2 }}
                      className="w-2 h-2 rounded-full bg-blue-400 shadow-lg shadow-blue-400/50"
                    />
                  )}
                </motion.div>
              </Link>
            </motion.div>
          )
        })}
      </nav>

      {/* Нижняя часть с эффектом */}
      <div className="p-4 border-t border-slate-700/50 bg-gradient-to-t from-slate-900 to-transparent">
        <motion.div
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          <Link
            href="/settings"
            className="flex items-center gap-3 px-4 py-3 rounded-xl text-slate-400 hover:bg-slate-800/50 hover:text-white transition-all duration-300 group"
          >
            <div className="w-10 h-10 rounded-lg bg-slate-700/50 group-hover:bg-gradient-to-br group-hover:from-slate-600 group-hover:to-slate-700 flex items-center justify-center transition-all duration-300 group-hover:rotate-90">
              <Settings className="w-5 h-5" />
            </div>
            <span className="font-semibold text-sm">{t('settings')}</span>
          </Link>
        </motion.div>
      </div>
    </aside>
  )
}
