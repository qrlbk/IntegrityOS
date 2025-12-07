'use client'

import { createContext, useContext, useEffect, useState, ReactNode } from 'react'

export type Language = 'ru' | 'kz' | 'en'

interface LanguageContextType {
  language: Language
  setLanguage: (lang: Language) => void
  t: (key: string) => string
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined)

// Переводы
const translations: Record<Language, Record<string, string>> = {
  ru: {
    // Общие
    'loading': 'Загрузка...',
    'error': 'Ошибка',
    'close': 'Закрыть',
    'save': 'Сохранить',
    'cancel': 'Отмена',
    
    // Навигация
    'dashboard': 'Панель управления',
    'import': 'Новый импорт',
    'reports': 'Отчеты',
    'settings': 'Настройки',
    
    // Дашборд
    'topRisks': 'Топ-5 рисков',
    'methodsDistribution': 'Распределение по методам',
    'criticalityDistribution': 'Распределение по критичности',
    'defectsTimeline': 'Динамика дефектов',
    'activeDefects': 'Активные дефекты',
    'highRisk': 'Высокий риск',
    'examinations': 'Обследования',
    'repairsThisYear': 'Ремонты за год',
    'critical': 'критических',
    'requireAttention': 'Требуют внимания',
    'totalDiagnostics': 'Всего диагностик',
    'completedThisYear': 'Выполнено в этом году',
    'noData': 'Нет данных',
    'clickToShowOnMap': 'Кликните, чтобы показать на карте',
    'clickToFilter': 'Кликните, чтобы показать объекты этого метода на карте',
    'clickToResetFilter': 'Кликните, чтобы сбросить фильтр',
    'clickToShowRiskLevel': 'Кликните, чтобы показать объекты этого уровня риска на карте',
    
    // Критичность
    'normal': 'Норма',
    'medium': 'Средний риск',
    'high': 'Высокий риск',
    
    // Объекты
    'object': 'Объект',
    'type': 'Тип',
    'status': 'Статус',
    'coordinates': 'Координаты',
    'critical': 'КРИТИЧЕСКИЙ',
    'normalStatus': 'НОРМАЛЬНЫЙ',
    
    // Языки
    'language': 'Язык',
    'russian': 'Русский',
    'kazakh': 'Қазақша',
    'english': 'English',
    
    // Тема
    'theme': 'Тема',
    'light': 'Светлая',
    'dark': 'Темная',
    
    // Sidebar
    'newImport': 'Новый импорт',
    'monitoringSystem': 'Система мониторинга',
  },
  kz: {
    // Жалпы
    'loading': 'Жүктелуде...',
    'error': 'Қате',
    'close': 'Жабу',
    'save': 'Сақтау',
    'cancel': 'Болдырмау',
    
    // Навигация
    'dashboard': 'Басқару панелі',
    'import': 'Жаңа импорт',
    'reports': 'Есептер',
    'settings': 'Баптаулар',
    
    // Дашборд
    'topRisks': 'Топ-5 тәуекелдер',
    'methodsDistribution': 'Әдістер бойынша таралу',
    'criticalityDistribution': 'Критикалық деңгей бойынша таралу',
    'defectsTimeline': 'Ақаулар динамикасы',
    'activeDefects': 'Белсенді ақаулар',
    'highRisk': 'Жоғары тәуекел',
    'examinations': 'Тексерулер',
    'repairsThisYear': 'Жылдағы жөндеулер',
    'critical': 'критикалық',
    'requireAttention': 'Назар аудару қажет',
    'totalDiagnostics': 'Барлық диагностикалар',
    'completedThisYear': 'Осы жылы орындалды',
    'noData': 'Деректер жоқ',
    'clickToShowOnMap': 'Картада көрсету үшін басыңыз',
    'clickToFilter': 'Бұл әдістің объектілерін картада көрсету үшін басыңыз',
    'clickToResetFilter': 'Сүзгіні қалпына келтіру үшін басыңыз',
    'clickToShowRiskLevel': 'Бұл тәуекел деңгейінің объектілерін картада көрсету үшін басыңыз',
    
    // Критичность
    'normal': 'Қалыпты',
    'medium': 'Орташа тәуекел',
    'high': 'Жоғары тәуекел',
    
    // Объекты
    'object': 'Объект',
    'type': 'Түрі',
    'status': 'Күйі',
    'coordinates': 'Координаттар',
    'critical': 'КРИТИКАЛЫҚ',
    'normalStatus': 'ҚАЛЫПТЫ',
    
    // Языки
    'language': 'Тіл',
    'russian': 'Русский',
    'kazakh': 'Қазақша',
    'english': 'English',
    
    // Тема
    'theme': 'Тақырып',
    'light': 'Жарық',
    'dark': 'Қараңғы',
    
    // Sidebar
    'newImport': 'Жаңа импорт',
    'monitoringSystem': 'Мониторинг жүйесі',
  },
  en: {
    // General
    'loading': 'Loading...',
    'error': 'Error',
    'close': 'Close',
    'save': 'Save',
    'cancel': 'Cancel',
    
    // Navigation
    'dashboard': 'Dashboard',
    'import': 'New Import',
    'reports': 'Reports',
    'settings': 'Settings',
    
    // Dashboard
    'topRisks': 'Top-5 Risks',
    'methodsDistribution': 'Distribution by Methods',
    'criticalityDistribution': 'Distribution by Criticality',
    'defectsTimeline': 'Defects Timeline',
    'activeDefects': 'Active Defects',
    'highRisk': 'High Risk',
    'examinations': 'Examinations',
    'repairsThisYear': 'Repairs This Year',
    'critical': 'critical',
    'requireAttention': 'Require Attention',
    'totalDiagnostics': 'Total Diagnostics',
    'completedThisYear': 'Completed This Year',
    'noData': 'No Data',
    'clickToShowOnMap': 'Click to show on map',
    'clickToFilter': 'Click to show objects of this method on map',
    'clickToResetFilter': 'Click to reset filter',
    'clickToShowRiskLevel': 'Click to show objects of this risk level on map',
    
    // Criticality
    'normal': 'Normal',
    'medium': 'Medium Risk',
    'high': 'High Risk',
    
    // Objects
    'object': 'Object',
    'type': 'Type',
    'status': 'Status',
    'coordinates': 'Coordinates',
    'critical': 'CRITICAL',
    'normalStatus': 'NORMAL',
    
    // Languages
    'language': 'Language',
    'russian': 'Русский',
    'kazakh': 'Қазақша',
    'english': 'English',
    
    // Theme
    'theme': 'Theme',
    'light': 'Light',
    'dark': 'Dark',
  },
}

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<Language>('ru')
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    const savedLanguage = localStorage.getItem('language') as Language | null
    if (savedLanguage && ['ru', 'kz', 'en'].includes(savedLanguage)) {
      setLanguageState(savedLanguage)
    } else {
      // Определяем язык браузера
      const browserLang = navigator.language.toLowerCase()
      if (browserLang.startsWith('kk') || browserLang.startsWith('kz')) {
        setLanguageState('kz')
      } else if (browserLang.startsWith('en')) {
        setLanguageState('en')
      } else {
        setLanguageState('ru')
      }
    }
  }, [])

  useEffect(() => {
    if (mounted) {
      localStorage.setItem('language', language)
    }
  }, [language, mounted])

  const setLanguage = (lang: Language) => {
    setLanguageState(lang)
  }

  const t = (key: string): string => {
    return translations[language]?.[key] || key
  }

  // Всегда возвращаем провайдер, даже если еще не смонтирован
  // Это предотвращает ошибки при использовании хука до инициализации
  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  )
}

export function useLanguage() {
  const context = useContext(LanguageContext)
  if (context === undefined) {
    throw new Error('useLanguage must be used within a LanguageProvider')
  }
  return context
}

