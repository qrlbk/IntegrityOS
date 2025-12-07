'use client'

import { useState, useCallback } from 'react'
import { Upload, File, X, CheckCircle2, AlertCircle, Loader2, Database, Sparkles, Download, FileSpreadsheet } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

interface UploadResult {
  success: boolean
  pipelines_imported?: number
  objects_imported?: number
  objects_auto_created?: number
  objects_skipped?: number
  diagnostics_imported?: number
  diagnostics_skipped?: number
  ml_predictions_made?: number
  errors?: string[]
  error?: string
}

export default function FileUpload() {
  const [file1, setFile1] = useState<File | null>(null)
  const [file2, setFile2] = useState<File | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [clearExisting, setClearExisting] = useState(false)
  const [result, setResult] = useState<UploadResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const validateFile = (file: File): boolean => {
    const ext = file.name.split('.').pop()?.toLowerCase()
    const validExts = ['csv', 'xlsx', 'xls']
    
    if (!ext || !validExts.includes(ext)) {
      setError(`Неверный формат файла. Поддерживаются: CSV, XLSX, XLS`)
      return false
    }
    
    return true
  }

  const handleFileSelect = useCallback((file: File, fileNumber: 1 | 2) => {
    setError(null)
    setResult(null)
    
    if (validateFile(file)) {
      if (fileNumber === 1) {
        setFile1(file)
      } else {
        setFile2(file)
      }
    }
  }, [])

  const handleDrop = useCallback((e: React.DragEvent, fileNumber: 1 | 2) => {
    e.preventDefault()
    setIsDragging(false)
    
    const file = e.dataTransfer.files[0]
    if (file) {
      handleFileSelect(file, fileNumber)
    }
  }, [handleFileSelect])

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>, fileNumber: 1 | 2) => {
    const file = e.target.files?.[0]
    if (file) {
      handleFileSelect(file, fileNumber)
    }
  }, [handleFileSelect])

  const loadHackathonData = async () => {
    setIsUploading(true)
    setError(null)
    setResult(null)

    try {
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      
      const response = await fetch(`${API_BASE_URL}/api/import/hackathon?clear_existing=${clearExisting}`, {
        method: 'POST',
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Ошибка при импорте тестовых данных')
      }

      const data: UploadResult = await response.json()
      setResult(data)
      
      if (data.success) {
        // Уведомляем приложение об успешном импорте
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new CustomEvent('importSuccess'))
        }
        setTimeout(() => {
          window.location.href = '/'
        }, 2000)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Неизвестная ошибка при загрузке тестовых данных')
    } finally {
      setIsUploading(false)
    }
  }

  const handleUploadWithFiles = async (file1: File, file2: File | null, clear: boolean = false) => {
    setIsUploading(true)
    setError(null)
    setResult(null)

    try {
      const formData = new FormData()
      formData.append('file1', file1)
      if (file2) {
      formData.append('file2', file2)
      }

      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const url = `${API_BASE_URL}/api/import/upload?clear_existing=${clear}`
      const response = await fetch(url, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Ошибка при загрузке файлов')
      }

      const data: UploadResult = await response.json()
      setResult(data)
      
      if (data.success) {
        // Уведомляем приложение об успешном импорте
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new CustomEvent('importSuccess'))
        }
        setTimeout(() => {
          window.location.href = '/'
        }, 2000)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Неизвестная ошибка при загрузке файлов')
    } finally {
      setIsUploading(false)
    }
  }

  const handleUpload = async () => {
    // Можно загрузить только Diagnostics - объекты создадутся автоматически
    if (!file1) {
      setError('Пожалуйста, выберите хотя бы файл Diagnostics')
      return
    }

    // Если загружен только один файл, передаем только его (должен быть Diagnostics)
    if (!file2) {
      await handleUploadWithFiles(file1, null, clearExisting)
    } else {
    await handleUploadWithFiles(file1, file2, clearExisting)
    }
  }

  const FileDropZone = ({ 
    fileNumber, 
    file, 
    label 
  }: { 
    fileNumber: 1 | 2
    file: File | null
    label: string
  }) => (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`relative border-2 border-dashed rounded-xl p-6 transition-all ${
        isDragging
          ? 'border-blue-500 bg-blue-50/50'
          : file
          ? 'border-green-300 bg-green-50/30'
          : 'border-gray-300 hover:border-blue-400 bg-gray-50/50'
      }`}
      onDrop={(e) => handleDrop(e, fileNumber)}
      onDragOver={(e) => {
        e.preventDefault()
        setIsDragging(true)
      }}
      onDragLeave={() => setIsDragging(false)}
    >
      <input
        type="file"
        id={`file-${fileNumber}`}
        className="hidden"
        accept=".csv,.xlsx,.xls"
        onChange={(e) => handleFileInput(e, fileNumber)}
      />
      
      {file ? (
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-green-500 to-emerald-500 flex items-center justify-center shadow-lg">
              <File className="w-6 h-6 text-white" />
            </div>
            <div>
              <p className="font-semibold text-gray-900">{file.name}</p>
              <p className="text-sm text-gray-500">
                {(file.size / 1024).toFixed(2)} KB
              </p>
            </div>
          </div>
          <button
            onClick={() => fileNumber === 1 ? setFile1(null) : setFile2(null)}
            className="p-2 hover:bg-red-50 rounded-lg transition-colors text-red-500 hover:text-red-600"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      ) : (
        <label
          htmlFor={`file-${fileNumber}`}
          className="flex flex-col items-center justify-center cursor-pointer"
        >
          <div className="w-16 h-16 rounded-xl bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center mb-4 shadow-lg">
            <Upload className="w-8 h-8 text-white" />
          </div>
          <p className="font-semibold text-gray-900 mb-1">{label}</p>
          <p className="text-sm text-gray-500 text-center">
            Перетащите файл сюда или нажмите для выбора
          </p>
          <p className="text-xs text-gray-400 mt-2">
            Поддерживаются: CSV, XLSX, XLS
          </p>
        </label>
      )}
    </motion.div>
  )

  return (
    <div className="space-y-6">
      {/* Заголовок */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white/80 backdrop-blur-xl rounded-2xl border border-gray-200/50 shadow-xl shadow-gray-900/5 p-6"
      >
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-lg">
            <Database className="w-7 h-7 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Импорт данных</h2>
            <p className="text-sm text-gray-500">
              Загрузите Diagnostics (обязательно) и Objects (опционально). 
              Если Objects не указан, система автоматически создаст объекты с помощью AI/ML анализа.
            </p>
          </div>
        </div>
        
        {/* Кнопки скачивания шаблонов */}
        <div className="mt-6 pt-6 border-t border-gray-200">
          <div className="flex items-center gap-3 mb-3">
            <FileSpreadsheet className="w-5 h-5 text-blue-600" />
            <h3 className="text-lg font-semibold text-gray-900">Скачать шаблоны для заполнения</h3>
          </div>
          <p className="text-sm text-gray-600 mb-4">
            Используйте шаблоны для правильного заполнения отчетов. Они оптимизированы для ML и AI анализа.
          </p>
          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => {
                const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
                window.open(`${API_BASE_URL}/api/import/template/objects`, '_blank')
              }}
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-lg border border-blue-200 transition-all font-medium text-sm"
            >
              <Download className="w-4 h-4" />
              Шаблон Objects.csv
            </button>
            <button
              onClick={() => {
                const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
                window.open(`${API_BASE_URL}/api/import/template/diagnostics`, '_blank')
              }}
              className="inline-flex items-center gap-2 px-4 py-2 bg-purple-50 hover:bg-purple-100 text-purple-700 rounded-lg border border-purple-200 transition-all font-medium text-sm"
            >
              <Download className="w-4 h-4" />
              Шаблон Diagnostics.csv
            </button>
            <button
              onClick={() => {
                const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
                window.open(`${API_BASE_URL}/api/import/template/both`, '_blank')
              }}
              className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white rounded-lg shadow-md transition-all font-medium text-sm"
            >
              <Download className="w-4 h-4" />
              Скачать оба шаблона (ZIP)
            </button>
          </div>
          <div className="mt-3 p-3 bg-blue-50/50 rounded-lg border border-blue-100">
            <p className="text-xs text-blue-800">
              <strong>💡 Совет:</strong> Шаблоны содержат примеры заполнения и инструкции. 
              Чем детальнее вы заполните defect_description, тем точнее будет анализ AI и ML.
            </p>
          </div>
        </div>
      </motion.div>

      {/* Зоны загрузки файлов */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="bg-white/80 backdrop-blur-xl rounded-2xl border border-gray-200/50 shadow-xl shadow-gray-900/5 p-6 space-y-4"
      >
        <FileDropZone
          fileNumber={1}
          file={file1}
          label="Файл 1: Objects или Diagnostics"
        />
        
        <FileDropZone
          fileNumber={2}
          file={file2}
          label="Файл 2: Objects (опционально - можно оставить пустым)"
        />
      </motion.div>

      {/* Сообщения об ошибках */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="flex items-center gap-3 p-4 bg-red-50 border-2 border-red-200 rounded-xl text-red-700"
          >
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <p className="font-semibold">{error}</p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Результаты импорта */}
      <AnimatePresence>
        {result && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className={`p-6 rounded-xl border-2 ${
              result.success 
                ? 'bg-green-50 border-green-200' 
                : 'bg-red-50 border-red-200'
            }`}
          >
            {result.success ? (
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-green-500 to-emerald-500 flex items-center justify-center shadow-lg">
                    <CheckCircle2 className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <p className="text-xl font-bold text-green-700">Импорт выполнен успешно!</p>
                    <p className="text-sm text-green-600">Данные загружены в систему</p>
                  </div>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mt-4">
                  <div className="p-3 bg-white rounded-lg border border-green-200">
                    <p className="text-xs text-gray-500 mb-1">Трубопроводов</p>
                    <p className="text-2xl font-bold text-gray-900">{result.pipelines_imported || 0}</p>
                  </div>
                  <div className="p-3 bg-white rounded-lg border border-green-200">
                    <p className="text-xs text-gray-500 mb-1">Объектов</p>
                    <p className="text-2xl font-bold text-gray-900">{result.objects_imported || 0}</p>
                    {result.objects_auto_created ? (
                      <p className="text-xs text-blue-600 mt-1">✨ {result.objects_auto_created} создано автоматически</p>
                    ) : null}
                  </div>
                  <div className="p-3 bg-white rounded-lg border border-green-200">
                    <p className="text-xs text-gray-500 mb-1">Диагностик</p>
                    <p className="text-2xl font-bold text-gray-900">{result.diagnostics_imported || 0}</p>
                  </div>
                </div>
                {result.ml_predictions_made !== undefined && result.ml_predictions_made > 0 && (
                  <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                    <p className="text-sm font-semibold text-blue-700">
                      ML предсказаний: {result.ml_predictions_made}
                    </p>
                  </div>
                )}
                {result.errors && result.errors.length > 0 && (
                  <div className="p-3 bg-yellow-50 rounded-lg border border-yellow-200">
                    <p className="text-sm font-semibold text-yellow-700">
                      Предупреждений: {result.errors.length}
                    </p>
                  </div>
                )}
                <p className="text-sm text-gray-500 mt-4">
                  Перенаправление на главную страницу через 2 секунды...
                </p>
              </div>
            ) : (
              <div className="flex items-center gap-3">
                <AlertCircle className="w-6 h-6 text-red-600" />
                <div>
                  <p className="font-semibold text-red-700">Ошибка при импорте</p>
                  <p className="text-sm text-red-600">{result.error || 'Неизвестная ошибка'}</p>
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Опции и кнопки */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="bg-white/80 backdrop-blur-xl rounded-2xl border border-gray-200/50 shadow-xl shadow-gray-900/5 p-6 space-y-4"
      >
        {/* Опция очистки данных */}
        <label className="flex items-center gap-3 p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors cursor-pointer">
          <input
            type="checkbox"
            checked={clearExisting}
            onChange={(e) => setClearExisting(e.target.checked)}
            className="w-5 h-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <div>
            <span className="font-semibold text-gray-900">Очистить существующие данные</span>
            <p className="text-sm text-gray-500">Удалить все данные перед импортом новых</p>
          </div>
        </label>

        {/* Кнопка импорта файлов */}
        <button
          onClick={handleUpload}
          disabled={!file1 || !file2 || isUploading}
          className={`w-full py-4 px-6 rounded-xl font-semibold transition-all ${
            !file1 || !file2 || isUploading
              ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
              : 'bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:from-blue-700 hover:to-purple-700 shadow-lg shadow-blue-500/25 hover:shadow-xl'
          } flex items-center justify-center gap-3`}
        >
          {isUploading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Импорт данных...</span>
            </>
          ) : (
            <>
              <Upload className="w-5 h-5" />
              <span>Импортировать данные</span>
            </>
          )}
        </button>

        {/* Разделитель */}
        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-gray-200"></div>
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="px-4 bg-white text-gray-500">или</span>
          </div>
        </div>

        {/* Кнопка тестовых данных */}
        <button
          onClick={loadHackathonData}
          disabled={isUploading}
          className={`w-full py-4 px-6 rounded-xl font-semibold transition-all ${
            isUploading
              ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
              : 'bg-gradient-to-r from-green-600 to-emerald-600 text-white hover:from-green-700 hover:to-emerald-700 shadow-lg shadow-green-500/25 hover:shadow-xl'
          } flex items-center justify-center gap-3`}
        >
          {isUploading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Загрузка тестовых данных...</span>
            </>
          ) : (
            <>
              <Sparkles className="w-5 h-5" />
              <span>Загрузить тестовые данные хакатона</span>
            </>
          )}
        </button>
        <p className="text-xs text-gray-500 text-center">
          Автоматически импортирует Objects_hackathon.csv и Diagnostics_hackathon.csv из папки data/
        </p>
      </motion.div>
    </div>
  )
}
