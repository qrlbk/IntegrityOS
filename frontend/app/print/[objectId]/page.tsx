'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import { fetchObjects, fetchDiagnostics, fetchWorkPermitsForObject, PipelineObject, Diagnostic, WorkPermit as WorkPermitType } from '@/lib/api'
import WorkPermit from '@/components/print/WorkPermit'

export default function PrintPage() {
  const params = useParams()
  const objectId = params?.objectId ? parseInt(params.objectId as string) : null
  const [object, setObject] = useState<PipelineObject | null>(null)
  const [diagnostics, setDiagnostics] = useState<Diagnostic[]>([])
  const [workPermit, setWorkPermit] = useState<WorkPermitType | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadData = async () => {
      if (!objectId) {
        setLoading(false)
        return
      }

      try {
        // Загружаем все объекты и находим нужный
        const objects = await fetchObjects()
        const foundObject = objects.find((obj) => obj.id === objectId)
        
        if (foundObject) {
          setObject(foundObject)
          // Загружаем диагностику
          const diagData = await fetchDiagnostics(objectId)
          setDiagnostics(diagData)
          
          // Загружаем последний активный наряд-допуск или создаем новый
          try {
            const permits = await fetchWorkPermitsForObject(objectId)
            if (permits.length > 0) {
              // Берем последний активный или выданный наряд-допуск
              const activePermit = permits.find(p => p.status === 'active' || p.status === 'issued') || permits[0]
              setWorkPermit(activePermit)
            }
          } catch (error) {
            console.error('Ошибка загрузки нарядов-допусков:', error)
          }
        }
      } catch (error) {
        console.error('Ошибка загрузки данных:', error)
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [objectId])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Загрузка данных для печати...</div>
      </div>
    )
  }

  if (!object) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg text-red-600">Объект не найден</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-white">
      <WorkPermit object={object} diagnostics={diagnostics} workPermit={workPermit} />
    </div>
  )
}

