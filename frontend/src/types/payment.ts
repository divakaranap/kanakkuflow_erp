export type PaymentMode = 'CASH' | 'CHEQUE' | 'NEFT' | 'RTGS' | 'UPI'
export type PaymentStatus = 'RECORDED' | 'CLEARED' | 'BOUNCED'

export interface PaymentAllocation {
  id: string
  payment_id: string
  invoice_id: string
  invoice_number?: string
  allocated_amount_paise: number
  created_at: string
}

export interface CustomerPayment {
  id: string
  payment_number: string
  customer_id: string
  customer_name?: string
  payment_date: string
  amount_paise: number
  payment_mode: PaymentMode
  reference_number?: string
  bank_name?: string
  status: PaymentStatus
  notes?: string
  created_by: number
  created_at: string
  allocations: PaymentAllocation[]
}

export interface AllocationCreate {
  invoice_id: string
  allocated_amount_paise: number
}

export interface CustomerPaymentCreate {
  customer_id: string
  payment_date?: string
  amount_paise: number
  payment_mode: PaymentMode
  reference_number?: string
  bank_name?: string
  notes?: string
  allocations: AllocationCreate[]
}

export interface CustomerLedgerEntry {
  id: string
  customer_id: string
  entry_date: string
  entry_type: string
  reference_document_id?: string
  reference_number: string
  debit_paise: number
  credit_paise: number
  running_balance_paise: number
  description?: string
  created_at: string
}

export interface CustomerLedgerStatement {
  customer_id: string
  customer_name: string
  customer_code?: string
  phone?: string
  gstin?: string
  opening_balance_paise: number
  total_debit_paise: number
  total_credit_paise: number
  closing_balance_paise: number
  entries: CustomerLedgerEntry[]
}

export interface ReceivablesAgeingCustomer {
  customer_id: string
  customer_name: string
  customer_code?: string
  total_outstanding_paise: number
  not_due_paise: number
  days_0_to_30_paise: number
  days_31_to_60_paise: number
  days_61_to_90_paise: number
  days_over_90_paise: number
}

export interface ReceivablesAgeingSummary {
  as_of_date: string
  total_receivables_paise: number
  total_not_due_paise: number
  total_0_to_30_paise: number
  total_31_to_60_paise: number
  total_61_to_90_paise: number
  total_over_90_paise: number
  customers: ReceivablesAgeingCustomer[]
}

export interface UnpaidInvoiceSummary {
  id: string
  invoice_number: string
  invoice_date: string
  grand_total_paise: number
  amount_paid_paise: number
  remaining_unpaid_paise: number
}
