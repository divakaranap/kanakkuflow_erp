import { api } from './api'
import type {
  Account,
  JournalEntry,
  JournalEntryCreate,
  TrialBalanceResponse,
  GeneralLedgerResponse,
  AuditLog,
} from '../types/accounting'

export const accountingService = {
  async getAccounts(): Promise<Account[]> {
    const response = await api.get<Account[]>('/accounting/accounts')
    return response.data
  },

  async createAccount(data: Partial<Account>): Promise<Account> {
    const response = await api.post<Account>('/accounting/accounts', data)
    return response.data
  },

  async getJournalEntries(
    sourceModule?: string,
    fromDate?: string,
    toDate?: string
  ): Promise<JournalEntry[]> {
    const params: Record<string, string> = {}
    if (sourceModule) params.source_module = sourceModule
    if (fromDate) params.from_date = fromDate
    if (toDate) params.to_date = toDate
    const response = await api.get<JournalEntry[]>('/accounting/journals', { params })
    return response.data
  },

  async createJournalEntry(data: JournalEntryCreate): Promise<JournalEntry> {
    const response = await api.post<JournalEntry>('/accounting/journals', data)
    return response.data
  },

  async getTrialBalance(asOf?: string): Promise<TrialBalanceResponse> {
    const params = asOf ? { as_of: asOf } : {}
    const response = await api.get<TrialBalanceResponse>('/accounting/trial-balance', { params })
    return response.data
  },

  async getGeneralLedger(accountId: string): Promise<GeneralLedgerResponse> {
    const response = await api.get<GeneralLedgerResponse>(`/accounting/general-ledger/${accountId}`)
    return response.data
  },

  async getAuditLogs(
    action?: string,
    entityType?: string,
    limit: number = 100
  ): Promise<AuditLog[]> {
    const params: Record<string, any> = { limit }
    if (action) params.action = action
    if (entityType) params.entity_type = entityType
    const response = await api.get<AuditLog[]>('/accounting/audit-logs', { params })
    return response.data
  },
}
