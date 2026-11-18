export type AccountCategory = 'ASSET' | 'LIABILITY' | 'EQUITY' | 'REVENUE' | 'EXPENSE'

export type AccountType =
  | 'CASH_BANK'
  | 'ACCOUNTS_RECEIVABLE'
  | 'RAW_MATERIAL_INVENTORY'
  | 'PACKAGING_INVENTORY'
  | 'FINISHED_GOODS_INVENTORY'
  | 'INPUT_CGST'
  | 'INPUT_SGST'
  | 'INPUT_IGST'
  | 'ACCOUNTS_PAYABLE'
  | 'OUTPUT_CGST'
  | 'OUTPUT_SGST'
  | 'OUTPUT_IGST'
  | 'OWNERS_CAPITAL'
  | 'RETAINED_EARNINGS'
  | 'SALES_REVENUE'
  | 'DISCOUNT_ALLOWED'
  | 'COGS'
  | 'DIRECT_LABOUR'
  | 'FACTORY_OVERHEAD'
  | 'YIELD_VARIANCE_EXPENSE'

export interface Account {
  id: string
  code: string
  name: string
  category: AccountCategory
  account_type: AccountType
  is_active: boolean
  description?: string
  created_at: string
  updated_at: string
}

export interface JournalEntryLine {
  id: string
  entry_id: string
  account_id: string
  account_code?: string
  account_name?: string
  debit_paise: number
  credit_paise: number
  line_narration?: string
}

export interface JournalEntry {
  id: string
  entry_number: string
  entry_date: string
  source_module: string
  source_document_id?: string
  source_reference?: string
  narration: string
  total_debit_paise: number
  total_credit_paise: number
  is_posted: boolean
  created_by: number
  created_at: string
  lines: JournalEntryLine[]
}

export interface JournalEntryLineCreate {
  account_id: string
  debit_paise: number
  credit_paise: number
  line_narration?: string
}

export interface JournalEntryCreate {
  entry_date?: string
  source_module?: string
  source_document_id?: string
  source_reference?: string
  narration: string
  lines: JournalEntryLineCreate[]
}

export interface TrialBalanceRow {
  account_id: string
  account_code: string
  account_name: string
  category: AccountCategory
  account_type: AccountType
  total_debit_paise: number
  total_credit_paise: number
  net_debit_paise: number
  net_credit_paise: number
}

export interface TrialBalanceResponse {
  as_of_date: string
  is_balanced: boolean
  grand_total_debit_paise: number
  grand_total_credit_paise: number
  difference_paise: number
  accounts: TrialBalanceRow[]
}

export interface GeneralLedgerRow {
  id: string
  entry_id: string
  entry_number: string
  entry_date: string
  source_module: string
  source_reference?: string
  narration: string
  line_narration?: string
  debit_paise: number
  credit_paise: number
  running_balance_paise: number
}

export interface GeneralLedgerResponse {
  account_id: string
  account_code: string
  account_name: string
  category: AccountCategory
  total_debit_paise: number
  total_credit_paise: number
  closing_balance_paise: number
  rows: GeneralLedgerRow[]
}

export interface AuditLog {
  id: string
  user_id?: number
  username: string
  role: string
  action: string
  entity_type: string
  entity_id: string
  details?: string
  ip_address?: string
  created_at: string
}
