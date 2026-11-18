import { api } from './api'
import type { ERPView } from '../components/common/AppSidebar'

export interface SearchResultItem {
  id: string
  type: 'product' | 'customer' | 'order' | 'invoice' | 'production' | 'dispatch' | 'raw_material'
  title: string
  subtitle: string
  view: ERPView
  tab?: string
  badge: string
}

export interface SearchResponse {
  query: string
  total: number
  results: SearchResultItem[]
}

export const searchService = {
  search: async (query: string): Promise<SearchResponse> => {
    if (!query || !query.trim()) {
      return { query: '', total: 0, results: [] }
    }
    const response = await api.get<SearchResponse>(`/search?q=${encodeURIComponent(query.trim())}`)
    return response.data
  },
}
