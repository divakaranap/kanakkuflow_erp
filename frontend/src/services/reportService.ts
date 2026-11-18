import { api } from './api'
import type { DashboardSummary } from '../types/reports'

export const reportService = {
  async getDashboardSummary(): Promise<DashboardSummary> {
    const response = await api.get<DashboardSummary>('/analytics/dashboard-summary')
    return response.data
  },

  async downloadReport(
    reportPath: string,
    format: 'csv' | 'xlsx' | 'pdf',
    filenamePrefix: string,
    params?: Record<string, string>
  ): Promise<void> {
    const response = await api.get(reportPath, {
      params: { ...params, format },
      responseType: 'blob',
    })

    const mimeTypes: Record<string, string> = {
      csv: 'text/csv',
      xlsx: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      pdf: 'application/pdf',
    }

    const blob = new Blob([response.data], { type: mimeTypes[format] || 'application/octet-stream' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `${filenamePrefix}_${new Date().toISOString().slice(0, 10)}.${format}`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  },
}
