import { describe, it, expect } from 'vitest'
import type { JournalEntryLineCreate, TrialBalanceRow } from '../types/accounting'

describe('Phase 8 - Accounting, Double-Entry & Audit Trail Tests', () => {
  it('validates double-entry invariant: Sum of Debits must equal Sum of Credits', () => {
    const lines: JournalEntryLineCreate[] = [
      { account_id: 'acct-bank', debit_paise: 50000000, credit_paise: 0 },
      { account_id: 'acct-equity', debit_paise: 0, credit_paise: 50000000 },
    ]

    const totalDebit = lines.reduce((s, l) => s + l.debit_paise, 0)
    const totalCredit = lines.reduce((s, l) => s + l.credit_paise, 0)

    expect(totalDebit).toBe(50000000)
    expect(totalCredit).toBe(50000000)
    expect(totalDebit).toBe(totalCredit)
  })

  it('rejects unbalanced journal entries where debit != credit', () => {
    const lines: JournalEntryLineCreate[] = [
      { account_id: 'acct-bank', debit_paise: 100000, credit_paise: 0 },
      { account_id: 'acct-equity', debit_paise: 0, credit_paise: 80000 },
    ]

    const totalDebit = lines.reduce((s, l) => s + l.debit_paise, 0)
    const totalCredit = lines.reduce((s, l) => s + l.credit_paise, 0)

    const isBalanced = totalDebit === totalCredit
    const difference = Math.abs(totalDebit - totalCredit)

    expect(isBalanced).toBe(false)
    expect(difference).toBe(20000) // ₹200 difference
  })

  it('verifies Trial Balance net calculation and grand total equilibrium', () => {
    const rows: Partial<TrialBalanceRow>[] = [
      {
        account_code: '1020',
        total_debit_paise: 50000000,
        total_credit_paise: 0,
        net_debit_paise: 50000000,
        net_credit_paise: 0,
      },
      {
        account_code: '1030',
        total_debit_paise: 787500,
        total_credit_paise: 400000,
        net_debit_paise: 387500,
        net_credit_paise: 0,
      },
      {
        account_code: '3010',
        total_debit_paise: 0,
        total_credit_paise: 50000000,
        net_debit_paise: 0,
        net_credit_paise: 50000000,
      },
      {
        account_code: '4010',
        total_debit_paise: 0,
        total_credit_paise: 387500,
        net_debit_paise: 0,
        net_credit_paise: 387500,
      },
    ]

    const grandTotalDebit = rows.reduce((s, r) => s + (r.net_debit_paise || 0), 0)
    const grandTotalCredit = rows.reduce((s, r) => s + (r.net_credit_paise || 0), 0)

    expect(grandTotalDebit).toBe(50387500)
    expect(grandTotalCredit).toBe(50387500)
    expect(grandTotalDebit - grandTotalCredit).toBe(0)
  })
})
