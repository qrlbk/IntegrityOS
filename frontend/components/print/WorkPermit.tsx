'use client'

import { useEffect, useState } from 'react'
import { PipelineObject, Diagnostic, WorkPermit as WorkPermitType, createWorkPermitForObject } from '@/lib/api'

interface WorkPermitProps {
  object: PipelineObject
  diagnostics?: Diagnostic[]
  workPermit?: WorkPermitType | null  // Если передан готовый наряд-допуск
}

export default function WorkPermit({ object, diagnostics, workPermit: initialWorkPermit }: WorkPermitProps) {
  const [workPermit, setWorkPermit] = useState<WorkPermitType | null>(initialWorkPermit || null)
  const [creatingPermit, setCreatingPermit] = useState(false)

  useEffect(() => {
    // Автоматически создаем наряд-допуск, если он не передан
    const createPermitIfNeeded = async () => {
      if (!workPermit && !creatingPermit && object?.id) {
        setCreatingPermit(true)
        try {
          console.log('Создание наряда-допуска для объекта:', object.id)
          const permit = await createWorkPermitForObject(object.id)
          console.log('Наряд-допуск создан:', permit)
          setWorkPermit(permit)
        } catch (error) {
          console.error('Ошибка создания наряда-допуска:', error)
          // Показываем ошибку пользователю
          if (error instanceof Error) {
            console.error('Детали ошибки:', error.message)
          }
        } finally {
          setCreatingPermit(false)
        }
      }
    }

    createPermitIfNeeded()
  }, [object?.id, workPermit, creatingPermit])

  useEffect(() => {
    // Автоматическая печать при загрузке
    if (workPermit) {
      const timer = setTimeout(() => {
        window.print()
      }, 500)
      return () => clearTimeout(timer)
    }
  }, [workPermit])

  const currentDate = new Date().toLocaleDateString('ru-RU', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })

  const latestDiagnostic = diagnostics && diagnostics.length > 0 ? diagnostics[0] : null

  // Функция для перевода статуса на русский
  const getStatusText = (status: string) => {
    switch (status) {
      case 'issued':
        return 'ВЫДАН'
      case 'active':
        return 'АКТИВЕН'
      case 'closed':
        return 'ЗАКРЫТ'
      case 'cancelled':
        return 'ОТМЕНЕН'
      default:
        return status.toUpperCase()
    }
  }

  return (
    <div className="print-document p-8 max-w-4xl mx-auto bg-white text-black">
      {/* Шапка документа */}
      <div className="text-center mb-8 border-b-2 border-black pb-4">
        <h1 className="text-2xl font-bold mb-2">НАРЯД-ДОПУСК</h1>
        <p className="text-sm">на выполнение работ по диагностике трубопроводной инфраструктуры</p>
        {workPermit && (
          <div className="mt-4 space-y-2">
            <div className="flex justify-between items-center">
              <div className="text-left">
                <p className="font-semibold text-lg">
                  № <span className="font-mono font-bold">{workPermit.permit_number}</span>
                </p>
                <p className="text-sm mt-1">
                  ID: <span className="font-mono">{workPermit.permit_id}</span> | Статус: <span className="font-semibold">{getStatusText(workPermit.status)}</span>
                </p>
              </div>
              <div className="text-right">
                {workPermit.issued_date && (
                  <p className="text-sm">
                    Дата выдачи: <span className="font-semibold">
                      {new Date(workPermit.issued_date).toLocaleDateString('ru-RU', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric'
                      })}
                    </span>
                  </p>
                )}
                {workPermit.issued_by && (
                  <p className="text-sm mt-1">Выдал: <span className="font-semibold">{workPermit.issued_by}</span></p>
                )}
              </div>
            </div>
          </div>
        )}
        {creatingPermit && (
          <div className="mt-4 text-sm text-gray-600">
            Создание наряда-допуска...
          </div>
        )}
        {!workPermit && !creatingPermit && (
          <div className="mt-4 text-sm text-red-600">
            ⚠ Наряд-допуск не найден. Создается...
          </div>
        )}
      </div>

      {/* Информация об объекте */}
      <div className="mb-6">
        <h2 className="text-xl font-bold mb-4">1. Информация об объекте</h2>
        <table className="w-full border-collapse border border-gray-800 mb-4">
          <tbody>
            {workPermit && (
              <>
                <tr>
                  <td className="border border-gray-800 p-2 font-semibold bg-gray-100 w-1/3">
                    ID наряда-допуска:
                  </td>
                  <td className="border border-gray-800 p-2 font-mono font-bold">{workPermit.permit_id}</td>
                </tr>
                <tr>
                  <td className="border border-gray-800 p-2 font-semibold bg-gray-100 w-1/3">
                    Номер наряда-допуска:
                  </td>
                  <td className="border border-gray-800 p-2 font-mono font-bold">{workPermit.permit_number}</td>
                </tr>
                {workPermit.issued_by && (
                  <tr>
                    <td className="border border-gray-800 p-2 font-semibold bg-gray-100 w-1/3">
                      Выдал наряд-допуск:
                    </td>
                    <td className="border border-gray-800 p-2">{workPermit.issued_by}</td>
                  </tr>
                )}
                {workPermit.issued_date && (
                  <tr>
                    <td className="border border-gray-800 p-2 font-semibold bg-gray-100 w-1/3">
                      Дата выдачи:
                    </td>
                    <td className="border border-gray-800 p-2">
                      {new Date(workPermit.issued_date).toLocaleDateString('ru-RU', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric'
                      })}
                    </td>
                  </tr>
                )}
              </>
            )}
            <tr>
              <td className="border border-gray-800 p-2 font-semibold bg-gray-100 w-1/3">
                ID объекта:
              </td>
              <td className="border border-gray-800 p-2 font-mono font-bold">{object.id}</td>
            </tr>
            <tr>
              <td className="border border-gray-800 p-2 font-semibold bg-gray-100 w-1/3">
                Наименование объекта:
              </td>
              <td className="border border-gray-800 p-2">{object.name}</td>
            </tr>
            <tr>
              <td className="border border-gray-800 p-2 font-semibold bg-gray-100">
                Тип объекта:
              </td>
              <td className="border border-gray-800 p-2">{object.type}</td>
            </tr>
            <tr>
              <td className="border border-gray-800 p-2 font-semibold bg-gray-100">
                Трасса:
              </td>
              <td className="border border-gray-800 p-2">{object.pipeline_id || 'Не указано'}</td>
            </tr>
            <tr>
              <td className="border border-gray-800 p-2 font-semibold bg-gray-100">
                Координаты:
              </td>
              <td className="border border-gray-800 p-2">
                {object.lat && object.lon
                  ? `Широта: ${object.lat.toFixed(6)}, Долгота: ${object.lon.toFixed(6)}`
                  : 'Не указано'}
              </td>
            </tr>
            <tr>
              <td className="border border-gray-800 p-2 font-semibold bg-gray-100">
                Статус:
              </td>
              <td className="border border-gray-800 p-2">
                <span
                  className={`font-bold ${
                    object.status === 'Critical' ? 'text-red-600' : 'text-green-600'
                  }`}
                >
                  {object.status === 'Critical' ? 'КРИТИЧЕСКИЙ' : 'НОРМАЛЬНЫЙ'}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* История диагностики */}
      {diagnostics && diagnostics.length > 0 && (
        <div className="mb-6">
          <h2 className="text-xl font-bold mb-4">2. История диагностики</h2>
          <table className="w-full border-collapse border border-gray-800 mb-4">
            <thead>
              <tr className="bg-gray-200">
                <th className="border border-gray-800 p-2 text-left">ID</th>
                <th className="border border-gray-800 p-2 text-left">Дата</th>
                <th className="border border-gray-800 p-2 text-left">Метод</th>
                <th className="border border-gray-800 p-2 text-left">Результат</th>
                <th className="border border-gray-800 p-2 text-left">Описание</th>
              </tr>
            </thead>
            <tbody>
              {diagnostics.slice(0, 5).map((diag) => (
                <tr key={diag.diag_id}>
                  <td className="border border-gray-800 p-2 font-mono font-semibold">{diag.diag_id}</td>
                  <td className="border border-gray-800 p-2">
                    {new Date(diag.date).toLocaleDateString('ru-RU')}
                  </td>
                  <td className="border border-gray-800 p-2">{diag.method}</td>
                  <td className="border border-gray-800 p-2">
                    {diag.defect_found ? (
                      <span className="text-red-600 font-semibold">Дефект обнаружен</span>
                    ) : (
                      <span className="text-green-600">Норма</span>
                    )}
                  </td>
                  <td className="border border-gray-800 p-2 text-sm">
                    {diag.defect_description || '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Последняя диагностика */}
      {latestDiagnostic && (
        <div className="mb-6">
          <h2 className="text-xl font-bold mb-4">3. Последняя диагностика</h2>
          <div className="border border-gray-800 p-4">
            <p className="mb-2">
              <strong>ID диагностики:</strong>{' '}
              <span className="font-mono font-bold">{latestDiagnostic.diag_id}</span>
            </p>
            <p className="mb-2">
              <strong>Дата:</strong>{' '}
              {new Date(latestDiagnostic.date).toLocaleDateString('ru-RU')}
            </p>
            <p className="mb-2">
              <strong>Метод контроля:</strong> {latestDiagnostic.method}
            </p>
            <p className="mb-2">
              <strong>Результат:</strong>{' '}
              {latestDiagnostic.defect_found ? (
                <span className="text-red-600 font-semibold">Дефект обнаружен</span>
              ) : (
                <span className="text-green-600">Дефектов не обнаружено</span>
              )}
            </p>
            {latestDiagnostic.defect_description && (
              <p className="mb-2">
                <strong>Описание дефекта:</strong> {latestDiagnostic.defect_description}
              </p>
            )}
            {latestDiagnostic.ml_label && (
              <p>
                <strong>ML-оценка критичности:</strong>{' '}
                <span className="font-semibold uppercase">{latestDiagnostic.ml_label}</span>
              </p>
            )}
          </div>
        </div>
      )}

      {/* Подписи */}
      <div className="mt-12">
        <div className="flex justify-between mb-8">
          <div className="w-1/2">
            <p className="mb-2 border-t-2 border-black pt-2">Выдал наряд-допуск:</p>
            {workPermit?.issued_by ? (
              <>
                <p className="text-sm mt-2 font-semibold">{workPermit.issued_by}</p>
                <p className="text-sm text-gray-600 mt-6">Подпись: _________________</p>
              </>
            ) : (
              <p className="text-sm text-gray-600 mt-2">(не указано)</p>
            )}
          </div>
          <div className="w-1/2 ml-4">
            <p className="mb-2 border-t-2 border-black pt-2">Принял наряд-допуск:</p>
            {workPermit?.closed_by ? (
              <>
                <p className="text-sm mt-2 font-semibold">{workPermit.closed_by}</p>
                <p className="text-sm text-gray-600 mt-6">Подпись: _________________</p>
              </>
            ) : (
              <p className="text-sm text-gray-600 mt-2">Подпись: _________________</p>
            )}
          </div>
        </div>
        <div className="text-sm text-gray-600 space-y-1">
          {workPermit?.issued_date && (
            <p>
              <strong>Дата выдачи:</strong>{' '}
              {new Date(workPermit.issued_date).toLocaleDateString('ru-RU', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
              })}
            </p>
          )}
          {workPermit?.closed_date && (
            <p>
              <strong>Дата закрытия:</strong>{' '}
              {new Date(workPermit.closed_date).toLocaleDateString('ru-RU', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
              })}
            </p>
          )}
          {!workPermit?.issued_date && (
            <p className="text-right">Дата выдачи: {currentDate}</p>
          )}
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
