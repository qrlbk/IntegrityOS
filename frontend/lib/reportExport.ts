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
 * Экспорт отчета в HTML формат
 */
export async function exportToHTML(reportElement: HTMLElement, filename: string = 'report.html') {
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
    ${reportElement.innerHTML}
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
  try {
    // Скрываем элементы, которые не должны быть в PDF (кнопки, карта если нужно)
    const noPrintElements = reportElement.querySelectorAll('.no-print')
    const originalDisplay: (string | null)[] = []
    
    noPrintElements.forEach((el) => {
      const htmlEl = el as HTMLElement
      originalDisplay.push(htmlEl.style.display)
      htmlEl.style.display = 'none'
    })

    // Если карта не нужна, скрываем её
    if (!includeMap) {
      const mapElement = reportElement.querySelector('[style*="height"]')
      if (mapElement) {
        const htmlEl = mapElement as HTMLElement
        originalDisplay.push(htmlEl.style.display)
        htmlEl.style.display = 'none'
      }
    }

    // Конвертируем HTML в canvas
    const canvas = await html2canvas(reportElement, {
      scale: 2,
      useCORS: true,
      logging: false,
      backgroundColor: '#ffffff',
    })

    // Восстанавливаем скрытые элементы
    noPrintElements.forEach((el, index) => {
      const htmlEl = el as HTMLElement
      if (originalDisplay[index] !== undefined) {
        htmlEl.style.display = originalDisplay[index] || ''
      }
    })

    const imgData = canvas.toDataURL('image/png')
    const pdf = new jsPDF('p', 'mm', 'a4')
    
    const pdfWidth = pdf.internal.pageSize.getWidth()
    const pdfHeight = pdf.internal.pageSize.getHeight()
    const imgWidth = canvas.width
    const imgHeight = canvas.height
    const ratio = Math.min(pdfWidth / imgWidth, pdfHeight / imgHeight)
    const imgScaledWidth = imgWidth * ratio
    const imgScaledHeight = imgHeight * ratio

    // Если изображение больше одной страницы, разбиваем на несколько страниц
    const pageHeight = pdfHeight
    let heightLeft = imgScaledHeight
    let position = 0

    pdf.addImage(imgData, 'PNG', 0, position, imgScaledWidth, imgScaledHeight)
    heightLeft -= pageHeight

    while (heightLeft > 0) {
      position = heightLeft - imgScaledHeight
      pdf.addPage()
      pdf.addImage(imgData, 'PNG', 0, position, imgScaledWidth, imgScaledHeight)
      heightLeft -= pageHeight
    }

    pdf.save(filename)
  } catch (error) {
    console.error('Ошибка при экспорте в PDF:', error)
    alert('Ошибка при создании PDF. Попробуйте использовать другой формат.')
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

