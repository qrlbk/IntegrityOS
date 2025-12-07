'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  Settings, 
  Database, 
  Cpu, 
  Bell, 
  Globe, 
  Save, 
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Info
} from 'lucide-react'
import api from '@/lib/api'

interface SettingsData {
  database: {
    autoBackup: boolean
    backupInterval: number
  }
  ml: {
    autoTrain: boolean
    minSamples: number
    retrainInterval: number
  }
  notifications: {
    emailEnabled: boolean
    emailAddress: string
    criticalAlerts: boolean
  }
  system: {
    language: string
    timezone: string
    dateFormat: string
  }
}

export default function SettingsPage() {
  const [settings, setSettings] = useState<SettingsData>({
    database: {
      autoBackup: true,
      backupInterval: 24,
    },
    ml: {
      autoTrain: true,
      minSamples: 100,
      retrainInterval: 7,
    },
    notifications: {
      emailEnabled: false,
      emailAddress: '',
      criticalAlerts: true,
    },
    system: {
      language: 'ru',
      timezone: 'Asia/Almaty',
      dateFormat: 'DD.MM.YYYY',
    },
  })

  const [saving, setSaving] = useState(false)
  const [saveStatus, setSaveStatus] = useState<'success' | 'error' | null>(null)
  const [mlStatus, setMlStatus] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Загружаем статус ML модели
    loadMLStatus()
  }, [])

  const loadMLStatus = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/ml/status`)
      if (response.ok) {
        const data = await response.json()
        // Получаем дополнительную информацию из мониторинга
        try {
          const monitorResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/ml/monitor/metrics`)
          if (monitorResponse.ok) {
            const monitorData = await monitorResponse.json()
            setMlStatus({
              ...data,
              labeled_samples: monitorData.labeled_diagnostics || 0,
              total_samples: monitorData.total_diagnostics || 0,
            })
          } else {
            setMlStatus(data)
          }
        } catch {
          setMlStatus(data)
        }
      }
    } catch (error) {
      console.error('Ошибка загрузки статуса ML:', error)
    }
  }

  const handleSave = async () => {
    setSaving(true)
    setSaveStatus(null)

    try {
      // Здесь можно добавить API для сохранения настроек
      // Пока просто симулируем сохранение
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      setSaveStatus('success')
      setTimeout(() => setSaveStatus(null), 3000)
    } catch (error) {
      setSaveStatus('error')
      setTimeout(() => setSaveStatus(null), 3000)
    } finally {
      setSaving(false)
    }
  }

  const handleMLRetrain = async () => {
    setSaving(true)
    setSaveStatus(null)
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/ml/train`, {
        method: 'POST',
      })
      
      if (response.ok) {
        const data = await response.json()
        if (data.trained) {
          setSaveStatus('success')
          await loadMLStatus()
        } else {
          setError(`Модель не обучена: ${data.message || 'недостаточно данных'}`)
          setSaveStatus('error')
        }
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Ошибка при обучении модели' }))
        setError(errorData.detail || 'Ошибка при обучении модели')
        setSaveStatus('error')
      }
    } catch (error) {
      setError('Ошибка соединения с сервером')
      setSaveStatus('error')
    } finally {
      setSaving(false)
      setTimeout(() => {
        setSaveStatus(null)
        setError(null)
      }, 5000)
    }
  }

  return (
    <>
      <div className="flex flex-col h-full overflow-hidden">
        {/* Хедер */}
        <motion.header
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="h-20 bg-white/80 backdrop-blur-xl border-b border-gray-200/50 flex items-center justify-between px-8 shadow-sm"
      >
          <div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-gray-900 via-gray-800 to-gray-900 bg-clip-text text-transparent">
              Настройки
            </h1>
            <div className="flex items-center gap-2 mt-1">
              <div className="w-1.5 h-1.5 rounded-full bg-purple-500 animate-pulse"></div>
              <p className="text-sm text-gray-500 font-medium">Главная > Настройки</p>
            </div>
          </div>
        </motion.header>

        {/* Контент */}
        <div className="flex-1 overflow-y-auto p-8 bg-gradient-to-b from-transparent to-gray-50/50">
          <div className="max-w-5xl mx-auto space-y-6">
            {/* Статус сохранения */}
            {(saveStatus || error) && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`p-4 rounded-xl border-2 ${
                  saveStatus === 'success'
                    ? 'bg-green-50 border-green-200 text-green-700'
                    : 'bg-red-50 border-red-200 text-red-700'
                } flex items-center gap-3`}
              >
                {saveStatus === 'success' ? (
                  <>
                    <CheckCircle2 className="w-5 h-5" />
                    <span className="font-semibold">Настройки сохранены!</span>
                  </>
                ) : (
                  <>
                    <AlertCircle className="w-5 h-5" />
                    <div className="flex-1">
                      <span className="font-semibold">Ошибка</span>
                      {error && <p className="text-sm mt-1">{error}</p>}
                    </div>
                  </>
                )}
              </motion.div>
            )}

            {/* База данных */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-white/80 backdrop-blur-xl rounded-2xl border border-gray-200/50 shadow-xl shadow-gray-900/5 p-6"
            >
              <div className="flex items-center gap-3 mb-6">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center shadow-lg">
                  <Database className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-gray-900">База данных</h2>
                  <p className="text-sm text-gray-500">Настройки резервного копирования</p>
                </div>
              </div>

              <div className="space-y-4">
                <label className="flex items-center justify-between p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors cursor-pointer">
                  <div>
                    <span className="font-semibold text-gray-900">Автоматическое резервное копирование</span>
                    <p className="text-sm text-gray-500">Регулярное создание резервных копий базы данных</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={settings.database.autoBackup}
                    onChange={(e) => setSettings({
                      ...settings,
                      database: { ...settings.database, autoBackup: e.target.checked }
                    })}
                    className="w-5 h-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </label>

                <div className="p-4 bg-gray-50 rounded-xl">
                  <label className="block mb-2 font-semibold text-gray-900">
                    Интервал резервного копирования (часы)
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="168"
                    value={settings.database.backupInterval}
                    onChange={(e) => setSettings({
                      ...settings,
                      database: { ...settings.database, backupInterval: parseInt(e.target.value) || 24 }
                    })}
                    className="w-full px-4 py-2 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>
            </motion.div>

            {/* ML Модель */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="bg-white/80 backdrop-blur-xl rounded-2xl border border-gray-200/50 shadow-xl shadow-gray-900/5 p-6"
            >
              <div className="flex items-center gap-3 mb-6">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center shadow-lg">
                  <Cpu className="w-6 h-6 text-white" />
                </div>
                <div className="flex-1">
                  <h2 className="text-xl font-bold text-gray-900">ML Модель</h2>
                  <p className="text-sm text-gray-500">Настройки машинного обучения</p>
                </div>
                {mlStatus && (
                  <div className={`px-4 py-2 rounded-lg font-semibold text-sm ${
                    mlStatus.is_trained 
                      ? 'bg-green-100 text-green-700' 
                      : 'bg-yellow-100 text-yellow-700'
                  }`}>
                    {mlStatus.is_trained ? 'Обучена' : 'Не обучена'}
                  </div>
                )}
              </div>

              {mlStatus && (
                <div className="mb-6 p-4 bg-gray-50 rounded-xl">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">Размерченных данных:</span>
                      <span className="ml-2 font-semibold text-gray-900">{mlStatus.labeled_samples || 0}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Всего диагностик:</span>
                      <span className="ml-2 font-semibold text-gray-900">{mlStatus.total_samples || 0}</span>
                    </div>
                  </div>
                  <button
                    onClick={handleMLRetrain}
                    disabled={saving}
                    className="mt-4 px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:from-purple-700 hover:to-pink-700 transition-all font-semibold disabled:opacity-50 flex items-center gap-2"
                  >
                    <RefreshCw className={`w-4 h-4 ${saving ? 'animate-spin' : ''}`} />
                    Переобучить модель
                  </button>
                </div>
              )}

              <div className="space-y-4">
                <label className="flex items-center justify-between p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors cursor-pointer">
                  <div>
                    <span className="font-semibold text-gray-900">Автоматическое обучение</span>
                    <p className="text-sm text-gray-500">Автоматически обучать модель при наличии новых данных</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={settings.ml.autoTrain}
                    onChange={(e) => setSettings({
                      ...settings,
                      ml: { ...settings.ml, autoTrain: e.target.checked }
                    })}
                    className="w-5 h-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </label>

                <div className="p-4 bg-gray-50 rounded-xl">
                  <label className="block mb-2 font-semibold text-gray-900">
                    Минимальное количество образцов для обучения
                  </label>
                  <input
                    type="number"
                    min="10"
                    max="10000"
                    value={settings.ml.minSamples}
                    onChange={(e) => setSettings({
                      ...settings,
                      ml: { ...settings.ml, minSamples: parseInt(e.target.value) || 100 }
                    })}
                    className="w-full px-4 py-2 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>
            </motion.div>

            {/* Уведомления */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="bg-white/80 backdrop-blur-xl rounded-2xl border border-gray-200/50 shadow-xl shadow-gray-900/5 p-6"
            >
              <div className="flex items-center gap-3 mb-6">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-orange-500 to-red-500 flex items-center justify-center shadow-lg">
                  <Bell className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-gray-900">Уведомления</h2>
                  <p className="text-sm text-gray-500">Настройки оповещений</p>
                </div>
              </div>

              <div className="space-y-4">
                <label className="flex items-center justify-between p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors cursor-pointer">
                  <div>
                    <span className="font-semibold text-gray-900">Email уведомления</span>
                    <p className="text-sm text-gray-500">Отправлять уведомления на email</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={settings.notifications.emailEnabled}
                    onChange={(e) => setSettings({
                      ...settings,
                      notifications: { ...settings.notifications, emailEnabled: e.target.checked }
                    })}
                    className="w-5 h-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </label>

                {settings.notifications.emailEnabled && (
                  <div className="p-4 bg-gray-50 rounded-xl">
                    <label className="block mb-2 font-semibold text-gray-900">Email адрес</label>
                    <input
                      type="email"
                      value={settings.notifications.emailAddress}
                      onChange={(e) => setSettings({
                        ...settings,
                        notifications: { ...settings.notifications, emailAddress: e.target.value }
                      })}
                      placeholder="example@mail.com"
                      className="w-full px-4 py-2 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                )}

                <label className="flex items-center justify-between p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors cursor-pointer">
                  <div>
                    <span className="font-semibold text-gray-900">Критические оповещения</span>
                    <p className="text-sm text-gray-500">Уведомления о критических дефектах</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={settings.notifications.criticalAlerts}
                    onChange={(e) => setSettings({
                      ...settings,
                      notifications: { ...settings.notifications, criticalAlerts: e.target.checked }
                    })}
                    className="w-5 h-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </label>
              </div>
            </motion.div>

            {/* Система */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="bg-white/80 backdrop-blur-xl rounded-2xl border border-gray-200/50 shadow-xl shadow-gray-900/5 p-6"
            >
              <div className="flex items-center gap-3 mb-6">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-gray-500 to-gray-600 flex items-center justify-center shadow-lg">
                  <Globe className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-gray-900">Система</h2>
                  <p className="text-sm text-gray-500">Общие настройки системы</p>
                </div>
              </div>

              <div className="space-y-4">
                <div className="p-4 bg-gray-50 rounded-xl">
                  <label className="block mb-2 font-semibold text-gray-900">Язык</label>
                  <select
                    value={settings.system.language}
                    onChange={(e) => setSettings({
                      ...settings,
                      system: { ...settings.system, language: e.target.value }
                    })}
                    className="w-full px-4 py-2 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="ru">Русский</option>
                    <option value="kz">Қазақша</option>
                    <option value="en">English</option>
                  </select>
                </div>

                <div className="p-4 bg-gray-50 rounded-xl">
                  <label className="block mb-2 font-semibold text-gray-900">Часовой пояс</label>
                  <select
                    value={settings.system.timezone}
                    onChange={(e) => setSettings({
                      ...settings,
                      system: { ...settings.system, timezone: e.target.value }
                    })}
                    className="w-full px-4 py-2 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="Asia/Almaty">Asia/Almaty (UTC+6)</option>
                    <option value="Europe/Moscow">Europe/Moscow (UTC+3)</option>
                    <option value="UTC">UTC</option>
                  </select>
                </div>

                <div className="p-4 bg-gray-50 rounded-xl">
                  <label className="block mb-2 font-semibold text-gray-900">Формат даты</label>
                  <select
                    value={settings.system.dateFormat}
                    onChange={(e) => setSettings({
                      ...settings,
                      system: { ...settings.system, dateFormat: e.target.value }
                    })}
                    className="w-full px-4 py-2 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="DD.MM.YYYY">DD.MM.YYYY</option>
                    <option value="YYYY-MM-DD">YYYY-MM-DD</option>
                    <option value="MM/DD/YYYY">MM/DD/YYYY</option>
                  </select>
                </div>
              </div>
            </motion.div>

            {/* Кнопка сохранения */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              className="flex justify-end"
            >
              <button
                onClick={handleSave}
                disabled={saving}
                className="px-8 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl hover:from-blue-700 hover:to-purple-700 transition-all font-semibold shadow-lg shadow-blue-500/25 hover:shadow-xl disabled:opacity-50 flex items-center gap-3"
              >
                {saving ? (
                  <>
                    <RefreshCw className="w-5 h-5 animate-spin" />
                    Сохранение...
                  </>
                ) : (
                  <>
                    <Save className="w-5 h-5" />
                    Сохранить настройки
                  </>
                )}
              </button>
            </motion.div>
          </div>
        </div>
      </div>
    </>
  )
}

