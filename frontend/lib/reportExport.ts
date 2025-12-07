/**
 * Утилиты для экспорта отчета в различные форматы
 */

import jsPDF from 'jspdf'
import html2canvas from 'html2canvas'
import * as XLSX from 'xlsx'
import { PipelineObject, Diagnostic, StatsSummary, TopRisk } from './api'

interface ReportData {
  objects: PipelineObject[]
  stats: StatsSummary | null
  topRisks: TopRisk[]
  defects: Array<{ object: PipelineObject; diagnostic: Diagnostic }>
  currentDate: string
}

/**
 * Создает HTML-представление карты с координатами объектов
 */
function createMapTableHTML(topRisks: TopRisk[], objects: PipelineObject[]): string {
  const criticalObjects = objects.filter(o => o.status === 'Critical' && o.lat && o.lon)
  
  let tableHTML = `
    <div class="mb-8">
      <h2 style="font-size: 20px; font-weight: bold; margin-top: 20px; margin-bottom: 10px;">4. Карта участка</h2>
      <p style="margin-bottom: 15px; font-size: 14px; color: #666;">
        Координаты объектов с дефектами. Красные маркеры - объекты с критическими дефектами, зеленые - нормальные.
      </p>
      <table style="width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 12px;">
        <thead>
          <tr style="background-color: #f0f0f0;">
            <th style="border: 1px solid #000; padding: 8px; text-align: left;">№</th>
            <th style="border: 1px solid #000; padding: 8px; text-align: left;">Объект</th>
            <th style="border: 1px solid #000; padding: 8px; text-align: left;">Тип</th>
            <th style="border: 1px solid #000; padding: 8px; text-align: left;">Широта</th>
            <th style="border: 1px solid #000; padding: 8px; text-align: left;">Долгота</th>
            <th style="border: 1px solid #000; padding: 8px; text-align: left;">Статус</th>
          </tr>
        </thead>
        <tbody>
  `
  
  // Добавляем критичные объекты
  criticalObjects.slice(0, 50).forEach((obj, index) => {
    tableHTML += `
      <tr style="background-color: ${index % 2 === 0 ? '#fff' : '#f9f9f9'};">
        <td style="border: 1px solid #000; padding: 8px;">${index + 1}</td>
        <td style="border: 1px solid #000; padding: 8px;">${obj.name}</td>
        <td style="border: 1px solid #000; padding: 8px;">${obj.type}</td>
        <td style="border: 1px solid #000; padding: 8px;">${obj.lat?.toFixed(6) || '-'}</td>
        <td style="border: 1px solid #000; padding: 8px;">${obj.lon?.toFixed(6) || '-'}</td>
        <td style="border: 1px solid #000; padding: 8px; color: #dc2626; font-weight: bold;">КРИТИЧЕСКИЙ</td>
      </tr>
    `
  })
  
  tableHTML += `
        </tbody>
      </table>
    </div>
  `
  
  return tableHTML
}

/**
 * Экспорт отчета в HTML формат
 */
export async function exportToHTML(
  reportElement: HTMLElement, 
  filename: string = 'report.html',
  topRisks: TopRisk[] = [],
  objects: PipelineObject[] = []
) {
  // Клонируем элемент, чтобы не изменять оригинал
  const clonedElement = reportElement.cloneNode(true) as HTMLElement
  
  // Удаляем кнопки экспорта
  const noPrintElements = clonedElement.querySelectorAll('.no-print')
  noPrintElements.forEach(el => el.remove())
  
  // Заменяем карту на таблицу координат
  // Ищем секцию с картой по заголовку "4. Карта участка"
  const allSections = clonedElement.querySelectorAll('h2')
  let mapSection: HTMLElement | null = null
  
  allSections.forEach(h2 => {
    if (h2.textContent?.includes('Карта участка') && h2.parentElement) {
      mapSection = h2.parentElement as HTMLElement
    }
  })
  
  if (mapSection) {
    mapSection.outerHTML = createMapTableHTML(topRisks, objects)
  }
  
  // Получаем HTML содержимое элемента
  const htmlContent = `
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Отчет о техническом состоянии</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Times New Roman', serif;
            line-height: 1.6;
            color: #000;
            background: #fff;
            padding: 20px;
        }
        .print-document {
            max-width: 210mm;
            margin: 0 auto;
            padding: 20mm;
        }
        h1 {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
            text-align: center;
        }
        h2 {
            font-size: 20px;
            font-weight: bold;
            margin-top: 20px;
            margin-bottom: 10px;
        }
        h3 {
            font-size: 18px;
            font-weight: bold;
            margin-top: 15px;
            margin-bottom: 8px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            font-size: 12px;
        }
        th, td {
            border: 1px solid #000;
            padding: 8px;
            text-align: left;
        }
        th {
            background-color: #f0f0f0;
            font-weight: bold;
        }
        tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        .text-center {
            text-align: center;
        }
        .text-right {
            text-align: right;
        }
        .border-b-2 {
            border-bottom: 2px solid #000;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        .grid {
            display: grid;
            gap: 10px;
            margin: 15px 0;
        }
        .grid-cols-2 {
            grid-template-columns: repeat(2, 1fr);
        }
        .grid-cols-3 {
            grid-template-columns: repeat(3, 1fr);
        }
        .grid-cols-4 {
            grid-template-columns: repeat(4, 1fr);
        }
        .border {
            border: 1px solid #000;
            padding: 10px;
        }
        .mb-4 {
            margin-bottom: 15px;
        }
        .mb-8 {
            margin-bottom: 30px;
        }
        .mt-12 {
            margin-top: 50px;
        }
        @media print {
            body {
                padding: 0;
            }
            .no-print {
                display: none !important;
            }
            @page {
                size: A4;
                margin: 2cm;
            }
        }
    </style>
</head>
<body>
    ${clonedElement.innerHTML}
</body>
</html>
  `

  // Создаем blob и скачиваем
  const blob = new Blob([htmlContent], { type: 'text/html;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

/**
 * Экспорт отчета в PDF формат
 */
export async function exportToPDF(
  reportElement: HTMLElement,
  filename: string = 'report.pdf',
  includeMap: boolean = false
) {
  // Сохраняем оригинальные стили и содержимое для восстановления
  const originalStyles: Map<HTMLElement, string> = new Map()
  const elementsToRestore: HTMLElement[] = []
  let mapSection: HTMLElement | null = null
  let mapOriginalHTML: string = ''
  
  try {
    // Скрываем элементы, которые не должны быть в PDF
    const noPrintElements = reportElement.querySelectorAll('.no-print')
    noPrintElements.forEach((el) => {
      const htmlEl = el as HTMLElement
      originalStyles.set(htmlEl, htmlEl.style.display)
      htmlEl.style.display = 'none'
      elementsToRestore.push(htmlEl)
    })

    // Находим и заменяем карту на текстовое описание
    const allSections = reportElement.querySelectorAll('h2')
    
    allSections.forEach(h2 => {
      if (h2.textContent?.includes('Карта участка') && h2.parentElement) {
        mapSection = h2.parentElement as HTMLElement
      }
    })
    
    if (mapSection) {
      // Сохраняем оригинальное содержимое
      mapOriginalHTML = mapSection.innerHTML
      
      // Заменяем содержимое секции на текстовое описание (убираем карту)
      mapSection.innerHTML = `
        <h2 class="text-2xl font-bold mb-4">4. Карта участка</h2>
        <div class="border border-gray-800 p-4">
          <p class="text-gray-600">
            Карта участка доступна в онлайн-версии отчета. Координаты объектов с дефектами представлены в разделе "Рекомендуемые раскопки".
          </p>
        </div>
      `
      
      // Ждем немного для применения изменений
      await new Promise(resolve => setTimeout(resolve, 200))
    }

    // Конвертируем HTML в canvas, работая с оригинальным элементом
    // Используем простые настройки без клонирования iframe
    const canvas = await html2canvas(reportElement, {
      scale: 1.5,
      useCORS: true,
      allowTaint: false,
      logging: false,
      backgroundColor: '#ffffff',
      ignoreElements: (element) => {
        // Игнорируем все iframe и Leaflet элементы
        if (element.tagName === 'IFRAME') return true
        if (element.classList.contains('leaflet-container')) return true
        if (element.classList.contains('leaflet-pane')) return true
        if (element.classList.contains('leaflet-map-pane')) return true
        if (element.querySelector('iframe')) return true
        return false
      },
      onclone: (clonedDoc) => {
        try {
          // Удаляем все iframe из клона
          const iframes = clonedDoc.querySelectorAll('iframe')
          iframes.forEach(iframe => {
            try {
              iframe.remove()
            } catch (e) {
              // Игнорируем ошибки удаления
            }
          })
          
          // Удаляем все Leaflet контейнеры
          const leafletSelectors = [
            '.leaflet-container',
            '.leaflet-pane',
            '.leaflet-map-pane',
            '.leaflet-control-container',
            '[class*="leaflet"]'
          ]
          
          leafletSelectors.forEach(selector => {
            try {
              const elements = clonedDoc.querySelectorAll(selector)
              elements.forEach(el => el.remove())
            } catch (e) {
              // Игнорируем ошибки
            }
          })
          
          // Удаляем скрипты
          const scripts = clonedDoc.querySelectorAll('script')
          scripts.forEach(script => script.remove())
        } catch (e) {
          // Игнорируем ошибки в onclone
          console.warn('Ошибка в onclone:', e)
        }
      },
      imageTimeout: 15000,
    })

    if (!canvas || canvas.width === 0 || canvas.height === 0) {
      throw new Error('Не удалось создать изображение для PDF')
    }

    const imgData = canvas.toDataURL('image/jpeg', 0.85)
    const pdf = new jsPDF('p', 'mm', 'a4')
    
    const pdfWidth = pdf.internal.pageSize.getWidth()
    const pdfHeight = pdf.internal.pageSize.getHeight()
    const imgWidth = canvas.width
    const imgHeight = canvas.height
    
    // Рассчитываем размеры для вставки на страницу
    const margin = 10 // отступы в мм
    const availableWidth = pdfWidth - (2 * margin)
    const availableHeight = pdfHeight - (2 * margin)
    
    // Конвертируем размеры canvas в мм (примерно 3.78 пикселей на мм при 96dpi)
    const pixelsPerMm = 3.78
    const imgWidthMm = imgWidth / pixelsPerMm
    const imgHeightMm = imgHeight / pixelsPerMm
    
    // Вычисляем масштаб
    const widthRatio = availableWidth / imgWidthMm
    const heightRatio = availableHeight / imgHeightMm
    const ratio = Math.min(widthRatio, heightRatio, 1)
    
    const finalWidth = imgWidthMm * ratio
    const finalHeight = imgHeightMm * ratio

    // Если изображение помещается на одной странице
    if (finalHeight <= availableHeight) {
      pdf.addImage(imgData, 'JPEG', margin, margin, finalWidth, finalHeight)
    } else {
      // Разбиваем на несколько страниц
      const pageHeight = availableHeight
      let yOffset = 0
      let sourceY = 0
      
      while (yOffset < finalHeight) {
        if (yOffset > 0) {
          pdf.addPage()
        }
        
        const remainingHeight = finalHeight - yOffset
        const heightToDraw = Math.min(remainingHeight, pageHeight)
        
        // Вычисляем, какую часть исходного изображения нужно взять
        const sourceHeight = (heightToDraw / ratio) * pixelsPerMm
        
        // Создаем временный canvas для этой части
        const tempCanvas = document.createElement('canvas')
        tempCanvas.width = imgWidth
        tempCanvas.height = Math.ceil(sourceHeight)
        const tempCtx = tempCanvas.getContext('2d')
        
        if (tempCtx) {
          tempCtx.drawImage(
            canvas,
            0, sourceY,
            imgWidth, sourceHeight,
            0, 0,
            imgWidth, sourceHeight
          )
          
          const pageImgData = tempCanvas.toDataURL('image/jpeg', 0.85)
          pdf.addImage(pageImgData, 'JPEG', margin, margin, finalWidth, heightToDraw)
        }
        
        yOffset += pageHeight
        sourceY += sourceHeight
      }
    }

    pdf.save(filename)
  } catch (error) {
    console.error('Ошибка при экспорте в PDF:', error)
    const errorMessage = error instanceof Error ? error.message : 'Неизвестная ошибка'
    alert(`Ошибка при создании PDF: ${errorMessage}. Попробуйте использовать другой формат.`)
    throw error
  } finally {
    // Восстанавливаем оригинальные стили и содержимое
    elementsToRestore.forEach((el) => {
      const originalDisplay = originalStyles.get(el)
      if (originalDisplay !== undefined) {
        el.style.display = originalDisplay
      }
    })
    
    // Восстанавливаем содержимое карты, если было изменено
    if (mapSection && mapOriginalHTML) {
      mapSection.innerHTML = mapOriginalHTML
    }
  }
}

/**
 * Экспорт отчета в Excel формат
 */
export function exportToExcel(data: ReportData, filename: string = 'report.xlsx') {
  const workbook = XLSX.utils.book_new()

  // 1. Лист "Общая статистика"
  const statsData = [
    ['ОТЧЕТ О ТЕХНИЧЕСКОМ СОСТОЯНИИ МАГИСТРАЛЬНЫХ ТРУБОПРОВОДОВ'],
    ['Дата формирования:', data.currentDate],
    [''],
    ['ОБЩАЯ СТАТИСТИКА'],
    ['Всего объектов', data.stats?.total_objects || data.objects.length],
    ['Диагностик', data.stats?.total_diagnostics || 0],
    ['Дефектов', data.stats?.total_defects || 0],
    ['% дефектов', data.stats ? `${data.stats.defects_percentage.toFixed(1)}%` : '0%'],
    [''],
    ['РАСПРЕДЕЛЕНИЕ ПО КРИТИЧНОСТИ'],
    ['Высокий риск', data.stats?.criticality.high || 0],
    ['Средний риск', data.stats?.criticality.medium || 0],
    ['Норма', data.stats?.criticality.normal || 0],
  ]
  
  const statsSheet = XLSX.utils.aoa_to_sheet(statsData)
  XLSX.utils.book_append_sheet(workbook, statsSheet, 'Общая статистика')

  // 2. Лист "Таблица дефектов"
  const defectsHeaders = [
    '№',
    'Критичность',
    'Объект',
    'Тип объекта',
    'Метод диагностики',
    'Дата',
    'Параметр 1',
    'Параметр 2',
    'Параметр 3',
    'Описание дефекта',
  ]

  const defectsRows = data.defects.map((item, index) => {
    const getCriticalityText = (label?: string | null) => {
      if (label === 'high') return 'ВЫСОКИЙ'
      if (label === 'medium') return 'СРЕДНИЙ'
      return 'НОРМА'
    }

    return [
      index + 1,
      getCriticalityText(item.diagnostic.ml_label),
      item.object.name,
      item.object.type,
      item.diagnostic.method,
      new Date(item.diagnostic.date).toLocaleDateString('ru-RU'),
      item.diagnostic.param1 !== null && item.diagnostic.param1 !== undefined
        ? item.diagnostic.param1.toFixed(2)
        : '-',
      item.diagnostic.param2 !== null && item.diagnostic.param2 !== undefined
        ? item.diagnostic.param2.toFixed(2)
        : '-',
      item.diagnostic.param3 !== null && item.diagnostic.param3 !== undefined
        ? item.diagnostic.param3.toFixed(2)
        : '-',
      item.diagnostic.defect_description || '-',
    ]
  })

  const defectsData = [defectsHeaders, ...defectsRows]
  const defectsSheet = XLSX.utils.aoa_to_sheet(defectsData)
  
  // Автоматическая ширина колонок
  defectsSheet['!cols'] = [
    { wch: 5 },  // №
    { wch: 12 }, // Критичность
    { wch: 25 }, // Объект
    { wch: 15 }, // Тип объекта
    { wch: 20 }, // Метод диагностики
    { wch: 12 }, // Дата
    { wch: 12 }, // Параметр 1
    { wch: 12 }, // Параметр 2
    { wch: 12 }, // Параметр 3
    { wch: 50 }, // Описание дефекта
  ]
  
  XLSX.utils.book_append_sheet(workbook, defectsSheet, 'Таблица дефектов')

  // 3. Лист "Рекомендуемые раскопки"
  const excavationsHeaders = [
    '№',
    'Объект',
    'Тип',
    'Широта',
    'Долгота',
    'Критических дефектов',
    'Приоритет',
  ]

  const recommendedExcavations = data.topRisks.filter((risk) => risk.high_defects_count > 0)
  const excavationsRows = recommendedExcavations.map((risk, index) => [
    index + 1,
    risk.object_name,
    risk.object_type,
    risk.lat.toFixed(6),
    risk.lon.toFixed(6),
    risk.high_defects_count,
    'ВЫСОКИЙ',
  ])

  const excavationsData = [excavationsHeaders, ...excavationsRows]
  const excavationsSheet = XLSX.utils.aoa_to_sheet(excavationsData)
  
  // Автоматическая ширина колонок
  excavationsSheet['!cols'] = [
    { wch: 5 },  // №
    { wch: 25 }, // Объект
    { wch: 15 }, // Тип
    { wch: 12 }, // Широта
    { wch: 12 }, // Долгота
    { wch: 20 }, // Критических дефектов
    { wch: 12 }, // Приоритет
  ]
  
  XLSX.utils.book_append_sheet(workbook, excavationsSheet, 'Рекомендуемые раскопки')

  // 4. Лист "Заключение"
  const conclusionData = [
    ['ЗАКЛЮЧЕНИЕ'],
    [''],
    ['На основании проведенного анализа технического состояния магистральных трубопроводов выявлено:'],
    [''],
    ['Всего объектов:', data.stats?.total_objects || data.objects.length],
    ['Объектов с дефектами:', data.objects.filter((o) => o.status === 'Critical').length],
    ['Критических объектов:', data.stats?.criticality.high || 0],
    ['Рекомендуется раскопка:', recommendedExcavations.length, 'объектов'],
    [''],
    ['РЕКОМЕНДАЦИИ:'],
    ['Необходимо провести немедленное обследование объектов из раздела "Рекомендуемые раскопки"'],
    ['для предотвращения аварийных ситуаций.'],
    [''],
    ['Дата формирования:', data.currentDate],
  ]
  
  const conclusionSheet = XLSX.utils.aoa_to_sheet(conclusionData)
  XLSX.utils.book_append_sheet(workbook, conclusionSheet, 'Заключение')

  // Сохраняем файл
  XLSX.writeFile(workbook, filename)
}

