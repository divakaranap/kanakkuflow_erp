import { api } from './api'
import type { DashboardSummary, ReportPreviewData } from '../types/reports'

export const reportService = {
  async getDashboardSummary(): Promise<DashboardSummary> {
    const response = await api.get<DashboardSummary>('/analytics/dashboard-summary')
    return response.data
  },

  async getReportPreview(
    reportPath: string,
    params?: Record<string, string>
  ): Promise<ReportPreviewData> {
    const response = await api.get<ReportPreviewData>(reportPath, {
      params: { ...params, format: 'json' },
    })
    return response.data
  },

  async downloadReport(
    reportPath: string,
    format: 'csv' | 'xlsx' | 'pdf',
    filenamePrefix: string,
    params?: Record<string, string>
  ): Promise<string> {
    const response = await api.get(reportPath, {
      params: { ...params, format },
      responseType: 'blob',
    })

    // Check if error response arrived as JSON blob
    if (response.data?.type === 'application/json') {
      const text = await (response.data as Blob).text()
      try {
        const json = JSON.parse(text)
        throw new Error(json.detail || 'Report generation failed')
      } catch (err) {
        if (err instanceof Error && err.message !== 'Report generation failed') throw err
        throw new Error(text || 'Report generation failed')
      }
    }

    const contentDisposition = response.headers['content-disposition'] as string | undefined
    let filename = `${filenamePrefix}_${new Date().toISOString().slice(0, 10)}.${format}`
    if (contentDisposition) {
      const match = contentDisposition.match(/filename=["']?([^"';]+)["']?/)
      if (match && match[1]) {
        filename = match[1].trim()
      }
    }

    const mimeTypes: Record<string, string> = {
      csv: 'text/csv;charset=utf-8',
      xlsx: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      pdf: 'application/pdf',
    }

    const blob = new Blob([response.data], { type: mimeTypes[format] || 'application/octet-stream' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)

    return filename
  },
}
