import React, { useState, useEffect } from 'react'
import {
  Scale,
  Plus,
  RefreshCw,
  CheckCircle2,
  XCircle,
  Eye,
  BookOpen,
  Calendar,
  ShieldCheck,
  Check,
} from 'lucide-react'
import { accountingService } from '../../services/accountingService'
import type {
  Account,
  JournalEntry,
  TrialBalanceResponse,
  GeneralLedgerResponse,
  AuditLog,
} from '../../types/accounting'

export function AccountingOverview() {
  const [activeTab, setActiveTab] = useState<'trial-balance' | 'ledger' | 'journals' | 'new-journal' | 'accounts' | 'audit'>('trial-balance')
  const [loading, setLoading] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')
  const [successMsg, setSuccessMsg] = useState('')

  // Data
  const [accounts, setAccounts] = useState<Account[]>([])
  const [trialBalance, setTrialBalance] = useState<TrialBalanceResponse | null>(null)
  const [journalEntries, setJournalEntries] = useState<JournalEntry[]>([])
  const [selectedAccountId, setSelectedAccountId] = useState('')
  const [generalLedger, setGeneralLedger] = useState<GeneralLedgerResponse | null>(null)
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([])

  // Modal / Detail state
  const [selectedJournal, setSelectedJournal] = useState<JournalEntry | null>(null)

  // Guided Manual Journal Form State
  const [journalDate, setJournalDate] = useState(new Date().toISOString().split('T')[0])
  const [journalNarration, setJournalNarration] = useState('Opening equity infusion or adjustment')
  const [journalLines, setJournalLines] = useState<
    { account_id: string; debit_rs: string; credit_rs: string; line_narration: string }[]
  >([
    { account_id: '', debit_rs: '500000', credit_rs: '0', line_narration: 'Debit entry' },
    { account_id: '', debit_rs: '0', credit_rs: '500000', line_narration: 'Credit entry' },
  ])

  useEffect(() => {
    loadBaseData()
  }, [])

  useEffect(() => {
    if (selectedAccountId) {
      loadAccountLedger(selectedAccountId)
    }
  }, [selectedAccountId])

  const loadBaseData = async () => {
    setLoading(true)
    setErrorMsg('')
    try {
      const [acctList, tb, journals, logs] = await Promise.all([
        accountingService.getAccounts(),
        accountingService.getTrialBalance(),
        accountingService.getJournalEntries(),
        accountingService.getAuditLogs(),
      ])
      setAccounts(acctList)
      setTrialBalance(tb)
      setJournalEntries(journals)
      setAuditLogs(logs)

      if (acctList.length > 0 && !selectedAccountId) {
        setSelectedAccountId(acctList[0].id)
      }
      if (acctList.length >= 2 && !journalLines[0].account_id) {
        // Pre-select bank and equity for the form demo
        const bank = acctList.find((a) => a.code === '1020') || acctList[0]
        const capital = acctList.find((a) => a.code === '3010') || acctList[1]
        setJournalLines([
          { account_id: bank.id, debit_rs: '500000', credit_rs: '0', line_narration: 'Capital deposit in bank' },
          { account_id: capital.id, debit_rs: '0', credit_rs: '500000', line_narration: 'Promoter equity capital' },
        ])
      }
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to load accounting data')
    } finally {
      setLoading(false)
    }
  }

  const loadAccountLedger = async (acctId: string) => {
    setLoading(true)
    try {
      const gl = await accountingService.getGeneralLedger(acctId)
      setGeneralLedger(gl)
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to load general ledger')
    } finally {
      setLoading(false)
    }
  }

  const handleAddJournalLine = () => {
    setJournalLines([
      ...journalLines,
      { account_id: accounts[0]?.id || '', debit_rs: '0', credit_rs: '0', line_narration: '' },
    ])
  }

  const handleRemoveJournalLine = (idx: number) => {
    if (journalLines.length <= 2) return
    setJournalLines(journalLines.filter((_, i) => i !== idx))
  }

  const handleCreateJournal = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrorMsg('')
    setSuccessMsg('')

    const totalDeb = journalLines.reduce((s, l) => s + (parseFloat(l.debit_rs) || 0), 0)
    const totalCred = journalLines.reduce((s, l) => s + (parseFloat(l.credit_rs) || 0), 0)

    if (Math.abs(totalDeb - totalCred) > 0.001) {
      setErrorMsg(
        `Double-entry invariant violated: Total Debits (₹${totalDeb.toFixed(2)}) != Total Credits (₹${totalCred.toFixed(2)})`
      )
      return
    }

    if (totalDeb <= 0) {
      setErrorMsg('Journal amount must be greater than zero')
      return
    }

    setLoading(true)
    try {
      const payload = {
        entry_date: journalDate,
        source_module: 'MANUAL',
        narration: journalNarration,
        lines: journalLines.map((l) => ({
          account_id: l.account_id,
          debit_paise: Math.round((parseFloat(l.debit_rs) || 0) * 100),
          credit_paise: Math.round((parseFloat(l.credit_rs) || 0) * 100),
          line_narration: l.line_narration,
        })),
      }
      const newJv = await accountingService.createJournalEntry(payload)
      setSuccessMsg(`Journal Voucher ${newJv.entry_number} posted successfully!`)
      await loadBaseData()
      if (selectedAccountId) await loadAccountLedger(selectedAccountId)
      setActiveTab('journals')
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to create journal voucher')
    } finally {
      setLoading(false)
    }
  }

  const totalFormDebit = journalLines.reduce((s, l) => s + (parseFloat(l.debit_rs) || 0), 0)
  const totalFormCredit = journalLines.reduce((s, l) => s + (parseFloat(l.credit_rs) || 0), 0)
  const isFormBalanced = Math.abs(totalFormDebit - totalFormCredit) < 0.001 && totalFormDebit > 0

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-white p-6 rounded-2xl border border-[#EAE8F1] shadow-card flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center space-x-3">
            <span className="p-2.5 bg-[#F2EEFF] text-[#7655E8] rounded-xl shadow-xs">
              <Scale className="h-5 w-5" />
            </span>
            <h2 className="text-xl sm:text-2xl font-extrabold text-[#17152B] tracking-tight">General Ledger &amp; Financial Audit</h2>
          </div>
          <p className="text-xs text-[#77758A] mt-1">
            Double-entry balanced accounting engine, Trial Balance invariance (Debit = Credit), General Ledger &amp; Auditor Trail.
          </p>
        </div>

        <div className="flex items-center space-x-2.5">
          <button
            onClick={() => {
              loadBaseData()
              if (selectedAccountId) loadAccountLedger(selectedAccountId)
            }}
            disabled={loading}
            className="px-3.5 py-2 text-xs font-bold text-[#17152B] hover:text-[#7655E8] border border-[#EAE8F1] rounded-xl bg-[#F8F7FC] flex items-center space-x-1.5 hover:bg-white transition shadow-xs"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin text-[#7655E8]' : ''}`} />
            <span>Refresh</span>
          </button>
          <button
            onClick={() => setActiveTab('new-journal')}
            className="px-4 py-2 text-xs font-bold text-white bg-gradient-to-r from-[#7655E8] to-[#9675F5] hover:opacity-95 rounded-xl flex items-center space-x-1.5 transition shadow-md shadow-[#7655E8]/20"
          >
            <Plus className="h-4 w-4" />
            <span>Post Journal Voucher</span>
          </button>
        </div>
      </div>

      {/* Notifications */}
      {errorMsg && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-2xl flex items-center justify-between text-xs text-red-700">
          <div className="flex items-center space-x-2">
            <XCircle className="h-4 w-4 flex-shrink-0" />
            <span>{errorMsg}</span>
          </div>
          <button onClick={() => setErrorMsg('')} className="text-red-500 hover:text-red-700 font-bold">
            &times;
          </button>
        </div>
      )}
      {successMsg && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl flex items-center justify-between text-xs text-emerald-700">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="h-4 w-4 flex-shrink-0" />
            <span>{successMsg}</span>
          </div>
          <button onClick={() => setSuccessMsg('')} className="text-emerald-500 hover:text-emerald-700 font-bold">
            &times;
          </button>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="bg-[#F8F7FC] p-1.5 rounded-2xl border border-[#EAE8F1] flex items-center space-x-1 overflow-x-auto shadow-xs">
        <button
          onClick={() => setActiveTab('trial-balance')}
          className={`py-2 px-4 rounded-xl text-xs font-bold transition whitespace-nowrap ${
            activeTab === 'trial-balance'
              ? 'bg-white text-[#7655E8] shadow-sm'
              : 'text-[#77758A] hover:text-[#17152B] hover:bg-white/50'
          }`}
        >
          Trial Balance
        </button>
        <button
          onClick={() => setActiveTab('ledger')}
          className={`py-2 px-4 rounded-xl text-xs font-bold transition whitespace-nowrap ${
            activeTab === 'ledger'
              ? 'bg-white text-[#7655E8] shadow-sm'
              : 'text-[#77758A] hover:text-[#17152B] hover:bg-white/50'
          }`}
        >
          General Ledger
        </button>
        <button
          onClick={() => setActiveTab('journals')}
          className={`py-2 px-4 rounded-xl text-xs font-bold transition whitespace-nowrap ${
            activeTab === 'journals'
              ? 'bg-white text-[#7655E8] shadow-sm'
              : 'text-[#77758A] hover:text-[#17152B] hover:bg-white/50'
          }`}
        >
          Journal Vouchers ({journalEntries.length})
        </button>
        <button
          onClick={() => setActiveTab('new-journal')}
          className={`py-2 px-4 rounded-xl text-xs font-bold transition whitespace-nowrap ${
            activeTab === 'new-journal'
              ? 'bg-white text-[#7655E8] shadow-sm'
              : 'text-[#77758A] hover:text-[#17152B] hover:bg-white/50'
          }`}
        >
          Post Journal
        </button>
        <button
          onClick={() => setActiveTab('accounts')}
          className={`py-2 px-4 rounded-xl text-xs font-bold transition whitespace-nowrap ${
            activeTab === 'accounts'
              ? 'bg-white text-[#7655E8] shadow-sm'
              : 'text-[#77758A] hover:text-[#17152B] hover:bg-white/50'
          }`}
        >
          Chart of Accounts ({accounts.length})
        </button>
        <button
          onClick={() => setActiveTab('audit')}
          className={`py-2 px-4 rounded-xl text-xs font-bold transition whitespace-nowrap ${
            activeTab === 'audit'
              ? 'bg-white text-[#7655E8] shadow-sm'
              : 'text-[#77758A] hover:text-[#17152B] hover:bg-white/50'
          }`}
        >
          Audit Trail ({auditLogs.length})
        </button>
      </div>

      {/* TAB 1: TRIAL BALANCE */}
      {activeTab === 'trial-balance' && trialBalance && (
        <div className="space-y-6">
          {/* Status Indicator Card */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
              <div>
                <span className="text-[11px] font-semibold text-slate-500 uppercase">Trial Balance State</span>
                <div className="mt-1 flex items-center space-x-1.5">
                  {trialBalance.is_balanced ? (
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
                      <CheckCircle2 className="h-3.5 w-3.5 mr-1" />
                      Strictly Balanced
                    </span>
                  ) : (
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold bg-red-100 text-red-800 border border-red-200">
                      <XCircle className="h-3.5 w-3.5 mr-1" />
                      Difference: ₹{(trialBalance.difference_paise / 100).toFixed(2)}
                    </span>
                  )}
                </div>
              </div>
            </div>

            <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-sm">
              <span className="text-[11px] font-semibold text-slate-500 uppercase">Total Net Debits</span>
              <p className="text-base font-extrabold text-blue-600 mt-1 font-mono">
                ₹{(trialBalance.grand_total_debit_paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </p>
            </div>

            <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-sm">
              <span className="text-[11px] font-semibold text-slate-500 uppercase">Total Net Credits</span>
              <p className="text-base font-extrabold text-emerald-600 mt-1 font-mono">
                ₹{(trialBalance.grand_total_credit_paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </p>
            </div>

            <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-sm">
              <span className="text-[11px] font-semibold text-slate-500 uppercase">As of Date</span>
              <p className="text-sm font-bold text-slate-800 mt-1 flex items-center">
                <Calendar className="h-4 w-4 mr-1 text-slate-400" />
                {trialBalance.as_of_date}
              </p>
            </div>
          </div>

          {/* Accounts Schedule */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="p-4 border-b border-slate-200 bg-slate-50/50 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-slate-800">Chart of Accounts - Trial Balance Extract</h3>
                <p className="text-xs text-slate-500">Every double-entry transaction aggregated to net debit/credit.</p>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-100 text-slate-700 font-semibold border-b border-slate-200">
                  <tr>
                    <th className="py-2.5 px-4">Code</th>
                    <th className="py-2.5 px-4">Account Name</th>
                    <th className="py-2.5 px-4">Category</th>
                    <th className="py-2.5 px-4 text-right">Gross Debit (₹)</th>
                    <th className="py-2.5 px-4 text-right">Gross Credit (₹)</th>
                    <th className="py-2.5 px-4 text-right">Net Debit (₹)</th>
                    <th className="py-2.5 px-4 text-right">Net Credit (₹)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 font-mono">
                  {trialBalance.accounts.map((row) => (
                    <tr
                      key={row.account_id}
                      onClick={() => {
                        setSelectedAccountId(row.account_id)
                        setActiveTab('ledger')
                      }}
                      className="hover:bg-slate-50 transition font-sans cursor-pointer"
                    >
                      <td className="py-2.5 px-4 font-mono font-bold text-indigo-600">{row.account_code}</td>
                      <td className="py-2.5 px-4 font-medium text-slate-900">{row.account_name}</td>
                      <td className="py-2.5 px-4">
                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-700">
                          {row.category}
                        </span>
                      </td>
                      <td className="py-2.5 px-4 text-right font-mono text-slate-500">
                        {row.total_debit_paise > 0
                          ? `₹${(row.total_debit_paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`
                          : '-'}
                      </td>
                      <td className="py-2.5 px-4 text-right font-mono text-slate-500">
                        {row.total_credit_paise > 0
                          ? `₹${(row.total_credit_paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`
                          : '-'}
                      </td>
                      <td className="py-2.5 px-4 text-right font-mono font-bold text-blue-700">
                        {row.net_debit_paise > 0
                          ? `₹${(row.net_debit_paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`
                          : '-'}
                      </td>
                      <td className="py-2.5 px-4 text-right font-mono font-bold text-emerald-700">
                        {row.net_credit_paise > 0
                          ? `₹${(row.net_credit_paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`
                          : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot className="bg-slate-100 border-t-2 border-slate-300 font-mono font-bold text-xs">
                  <tr>
                    <td colSpan={5} className="py-3 px-4 font-sans uppercase text-right text-slate-700">
                      Grand Totals:
                    </td>
                    <td className="py-3 px-4 text-right text-blue-800">
                      ₹{(trialBalance.grand_total_debit_paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="py-3 px-4 text-right text-emerald-800">
                      ₹{(trialBalance.grand_total_credit_paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: GENERAL LEDGER */}
      {activeTab === 'ledger' && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
              <div>
                <h3 className="text-base font-bold text-slate-900">General Ledger Statement</h3>
                <p className="text-xs text-slate-500">
                  Select an account to view its chronological journal entries and running balance.
                </p>
              </div>

              <div className="flex items-center space-x-2">
                <label className="text-xs font-semibold text-slate-600">Account:</label>
                <select
                  value={selectedAccountId}
                  onChange={(e) => setSelectedAccountId(e.target.value)}
                  className="text-xs p-2 rounded-lg border border-slate-300 bg-white font-medium"
                >
                  {accounts.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.code} - {a.name} ({a.category})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {generalLedger && (
              <>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 pt-2">
                  <div className="p-4 bg-slate-50 rounded-lg border border-slate-200">
                    <span className="text-[11px] font-semibold text-slate-500 uppercase">Account Code &amp; Name</span>
                    <p className="text-sm font-bold text-slate-900 mt-1">
                      {generalLedger.account_code} - {generalLedger.account_name}
                    </p>
                  </div>
                  <div className="p-4 bg-slate-50 rounded-lg border border-slate-200">
                    <span className="text-[11px] font-semibold text-slate-500 uppercase">Total Debits</span>
                    <p className="text-sm font-bold text-blue-600 mt-1 font-mono">
                      ₹{(generalLedger.total_debit_paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </p>
                  </div>
                  <div className="p-4 bg-slate-50 rounded-lg border border-slate-200">
                    <span className="text-[11px] font-semibold text-slate-500 uppercase">Total Credits</span>
                    <p className="text-sm font-bold text-emerald-600 mt-1 font-mono">
                      ₹{(generalLedger.total_credit_paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </p>
                  </div>
                  <div className="p-4 bg-slate-50 rounded-lg border border-slate-200">
                    <span className="text-[11px] font-semibold text-slate-500 uppercase">Closing Balance</span>
                    <p className="text-sm font-bold text-slate-900 mt-1 font-mono">
                      ₹{(generalLedger.closing_balance_paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </p>
                  </div>
                </div>

                <div className="overflow-x-auto border border-slate-200 rounded-lg">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-100 text-slate-700 font-semibold border-b border-slate-200">
                      <tr>
                        <th className="py-2.5 px-3">Date</th>
                        <th className="py-2.5 px-3">Voucher #</th>
                        <th className="py-2.5 px-3">Module</th>
                        <th className="py-2.5 px-3">Narration</th>
                        <th className="py-2.5 px-3 text-right">Debit (₹)</th>
                        <th className="py-2.5 px-3 text-right">Credit (₹)</th>
                        <th className="py-2.5 px-3 text-right">Running Balance (₹)</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200 font-mono">
                      {generalLedger.rows.length === 0 ? (
                        <tr>
                          <td colSpan={7} className="py-6 text-center text-slate-500 font-sans">
                            No journal transactions posted to this account yet.
                          </td>
                        </tr>
                      ) : (
                        generalLedger.rows.map((row) => (
                          <tr key={row.id} className="hover:bg-slate-50 transition font-sans">
                            <td className="py-2.5 px-3 text-slate-600 font-mono">{row.entry_date}</td>
                            <td className="py-2.5 px-3 font-mono font-bold text-indigo-600">{row.entry_number}</td>
                            <td className="py-2.5 px-3">
                              <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-700">
                                {row.source_module}
                              </span>
                            </td>
                            <td className="py-2.5 px-3 text-slate-700">{row.narration}</td>
                            <td className="py-2.5 px-3 text-right font-mono text-blue-600">
                              {row.debit_paise > 0
                                ? `₹${(row.debit_paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`
                                : '-'}
                            </td>
                            <td className="py-2.5 px-3 text-right font-mono text-emerald-600">
                              {row.credit_paise > 0
                                ? `₹${(row.credit_paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`
                                : '-'}
                            </td>
                            <td className="py-2.5 px-3 text-right font-mono font-bold text-slate-900">
                              ₹{(row.running_balance_paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* TAB 3: JOURNAL ENTRIES LIST */}
      {activeTab === 'journals' && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-slate-50/50">
            <div>
              <h3 className="text-sm font-bold text-slate-800">All Journal Vouchers</h3>
              <p className="text-xs text-slate-500">Immutable double-entry vouchers across all ERP events.</p>
            </div>
            <span className="text-xs font-semibold px-2.5 py-1 bg-white border border-slate-200 rounded-lg text-slate-700">
              Total Vouchers: {journalEntries.length}
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-100 text-slate-700 font-semibold border-b border-slate-200">
                <tr>
                  <th className="py-3 px-4">Voucher Number</th>
                  <th className="py-3 px-4">Date</th>
                  <th className="py-3 px-4">Module</th>
                  <th className="py-3 px-4">Narration</th>
                  <th className="py-3 px-4 text-right">Debit (₹)</th>
                  <th className="py-3 px-4 text-right">Credit (₹)</th>
                  <th className="py-3 px-4 text-center">Status</th>
                  <th className="py-3 px-4 text-center">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {journalEntries.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="py-8 text-center text-slate-500">
                      No journal vouchers posted yet.
                    </td>
                  </tr>
                ) : (
                  journalEntries.map((jv) => (
                    <tr key={jv.id} className="hover:bg-slate-50 transition">
                      <td className="py-3 px-4 font-mono font-bold text-indigo-600">{jv.entry_number}</td>
                      <td className="py-3 px-4 text-slate-600">{jv.entry_date}</td>
                      <td className="py-3 px-4">
                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-700">
                          {jv.source_module}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-800 max-w-xs truncate">{jv.narration}</td>
                      <td className="py-3 px-4 text-right font-mono font-bold text-blue-600">
                        ₹{(jv.total_debit_paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </td>
                      <td className="py-3 px-4 text-right font-mono font-bold text-emerald-600">
                        ₹{(jv.total_credit_paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
                          POSTED
                        </span>
                      </td>
                      <td className="py-3 px-4 text-center">
                        <button
                          onClick={() => setSelectedJournal(jv)}
                          className="p-1.5 rounded bg-slate-100 text-slate-700 hover:bg-slate-200 transition"
                          title="View Double Entry Lines"
                        >
                          <Eye className="h-3.5 w-3.5" />
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 4: POST MANUAL JOURNAL */}
      {activeTab === 'new-journal' && (
        <form onSubmit={handleCreateJournal} className="space-y-6">
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-6">
            <div className="border-b border-slate-200 pb-4">
              <h3 className="text-base font-bold text-slate-900">Post Manual Double-Entry Journal Voucher</h3>
              <p className="text-xs text-slate-500 mt-1">
                Enforces strict accounting invariance: Total Debits must exactly equal Total Credits.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Voucher Date</label>
                <input
                  type="date"
                  value={journalDate}
                  onChange={(e) => setJournalDate(e.target.value)}
                  className="w-full text-xs p-2.5 rounded-lg border border-slate-300 bg-white"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Narration / Purpose</label>
                <input
                  type="text"
                  value={journalNarration}
                  onChange={(e) => setJournalNarration(e.target.value)}
                  placeholder="e.g. Infusion of promoter equity capital into bank"
                  className="w-full text-xs p-2.5 rounded-lg border border-slate-300 bg-white"
                  required
                />
              </div>
            </div>

            {/* Dynamic Lines Table */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-800 uppercase tracking-wider block">
                  Journal Lines (Minimum 2 Lines)
                </span>
                <button
                  type="button"
                  onClick={handleAddJournalLine}
                  className="px-2.5 py-1 text-xs bg-indigo-50 text-indigo-700 rounded border border-indigo-200 font-semibold hover:bg-indigo-100 transition flex items-center space-x-1"
                >
                  <Plus className="h-3 w-3" />
                  <span>Add Line</span>
                </button>
              </div>

              <div className="border border-slate-200 rounded-lg overflow-hidden">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-100 text-slate-700 font-semibold border-b border-slate-200">
                    <tr>
                      <th className="py-2.5 px-3">Account</th>
                      <th className="py-2.5 px-3">Line Description</th>
                      <th className="py-2.5 px-3 text-right">Debit (₹)</th>
                      <th className="py-2.5 px-3 text-right">Credit (₹)</th>
                      <th className="py-2.5 px-3 text-center">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 font-mono">
                    {journalLines.map((line, idx) => (
                      <tr key={idx} className="hover:bg-slate-50 transition font-sans">
                        <td className="py-2 px-3">
                          <select
                            value={line.account_id}
                            onChange={(e) => {
                              const newLines = [...journalLines]
                              newLines[idx].account_id = e.target.value
                              setJournalLines(newLines)
                            }}
                            className="w-full text-xs p-1.5 rounded border border-slate-300 bg-white"
                            required
                          >
                            <option value="">-- Select Account --</option>
                            {accounts.map((a) => (
                              <option key={a.id} value={a.id}>
                                {a.code} - {a.name} ({a.category})
                              </option>
                            ))}
                          </select>
                        </td>
                        <td className="py-2 px-3">
                          <input
                            type="text"
                            value={line.line_narration}
                            onChange={(e) => {
                              const newLines = [...journalLines]
                              newLines[idx].line_narration = e.target.value
                              setJournalLines(newLines)
                            }}
                            placeholder="Line narration"
                            className="w-full text-xs p-1.5 rounded border border-slate-300 bg-white"
                          />
                        </td>
                        <td className="py-2 px-3 text-right">
                          <input
                            type="number"
                            step="0.01"
                            min="0"
                            value={line.debit_rs}
                            onChange={(e) => {
                              const newLines = [...journalLines]
                              newLines[idx].debit_rs = e.target.value
                              if (parseFloat(e.target.value) > 0) newLines[idx].credit_rs = '0'
                              setJournalLines(newLines)
                            }}
                            className="w-28 text-right text-xs p-1.5 rounded border border-slate-300 bg-white font-mono font-bold text-blue-700"
                          />
                        </td>
                        <td className="py-2 px-3 text-right">
                          <input
                            type="number"
                            step="0.01"
                            min="0"
                            value={line.credit_rs}
                            onChange={(e) => {
                              const newLines = [...journalLines]
                              newLines[idx].credit_rs = e.target.value
                              if (parseFloat(e.target.value) > 0) newLines[idx].debit_rs = '0'
                              setJournalLines(newLines)
                            }}
                            className="w-28 text-right text-xs p-1.5 rounded border border-slate-300 bg-white font-mono font-bold text-emerald-700"
                          />
                        </td>
                        <td className="py-2 px-3 text-center">
                          {journalLines.length > 2 && (
                            <button
                              type="button"
                              onClick={() => handleRemoveJournalLine(idx)}
                              className="text-red-500 hover:text-red-700 font-bold"
                            >
                              &times;
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot className="bg-slate-100 border-t border-slate-300 font-mono font-bold text-xs">
                    <tr>
                      <td colSpan={2} className="py-2 px-3 text-right font-sans uppercase">
                        Voucher Balance:
                      </td>
                      <td className="py-2 px-3 text-right text-blue-700 font-mono">₹{totalFormDebit.toFixed(2)}</td>
                      <td className="py-2 px-3 text-right text-emerald-700 font-mono">₹{totalFormCredit.toFixed(2)}</td>
                      <td className="py-2 px-3 text-center">
                        {isFormBalanced ? (
                          <span className="text-[10px] text-emerald-700 font-bold">BALANCED</span>
                        ) : (
                          <span className="text-[10px] text-red-600 font-bold">
                            DIFF: ₹{Math.abs(totalFormDebit - totalFormCredit).toFixed(2)}
                          </span>
                        )}
                      </td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </div>

            <div className="flex items-center justify-end space-x-3 pt-4 border-t border-slate-200">
              <button
                type="button"
                onClick={() => setActiveTab('journals')}
                className="px-4 py-2 border border-slate-300 text-slate-700 text-xs font-semibold rounded-lg hover:bg-slate-50 transition"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading || !isFormBalanced}
                className="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-lg shadow-sm transition disabled:opacity-50 flex items-center space-x-1.5"
              >
                <Check className="h-4 w-4" />
                <span>{loading ? 'Posting...' : 'Post Journal Voucher'}</span>
              </button>
            </div>
          </div>
        </form>
      )}

      {/* TAB 5: CHART OF ACCOUNTS */}
      {activeTab === 'accounts' && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-4 border-b border-slate-200 bg-slate-50/50 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-800">Chart of Accounts (COA)</h3>
              <p className="text-xs text-slate-500">Master ledger taxonomy for financial control.</p>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-100 text-slate-700 font-semibold border-b border-slate-200">
                <tr>
                  <th className="py-2.5 px-4">Account Code</th>
                  <th className="py-2.5 px-4">Account Name</th>
                  <th className="py-2.5 px-4">Category</th>
                  <th className="py-2.5 px-4">Type</th>
                  <th className="py-2.5 px-4">Description</th>
                  <th className="py-2.5 px-4 text-center">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {accounts.map((a) => (
                  <tr key={a.id} className="hover:bg-slate-50 transition">
                    <td className="py-2.5 px-4 font-mono font-bold text-indigo-600">{a.code}</td>
                    <td className="py-2.5 px-4 font-medium text-slate-900">{a.name}</td>
                    <td className="py-2.5 px-4">
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-700">
                        {a.category}
                      </span>
                    </td>
                    <td className="py-2.5 px-4 font-mono text-slate-500 text-[11px]">{a.account_type}</td>
                    <td className="py-2.5 px-4 text-slate-500 max-w-xs truncate">{a.description || '-'}</td>
                    <td className="py-2.5 px-4 text-center">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-100 text-emerald-800">
                        Active
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 6: AUDIT TRAIL */}
      {activeTab === 'audit' && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-4 border-b border-slate-200 bg-slate-50/50 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-800 flex items-center space-x-2">
                <ShieldCheck className="h-4 w-4 text-indigo-600" />
                <span>Statutory &amp; System Audit Trail</span>
              </h3>
              <p className="text-xs text-slate-500">Immutable chronological record of business and security events.</p>
            </div>
            <span className="text-xs font-semibold px-2.5 py-1 bg-white border border-slate-200 rounded-lg text-slate-700">
              Audit Logs: {auditLogs.length}
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-100 text-slate-700 font-semibold border-b border-slate-200">
                <tr>
                  <th className="py-2.5 px-4">Timestamp</th>
                  <th className="py-2.5 px-4">User</th>
                  <th className="py-2.5 px-4">Role</th>
                  <th className="py-2.5 px-4">Action</th>
                  <th className="py-2.5 px-4">Entity Type</th>
                  <th className="py-2.5 px-4">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 font-mono">
                {auditLogs.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-slate-500 font-sans">
                      No audit events recorded yet.
                    </td>
                  </tr>
                ) : (
                  auditLogs.map((log) => (
                    <tr key={log.id} className="hover:bg-slate-50 transition font-sans">
                      <td className="py-2.5 px-4 font-mono text-slate-600 text-[11px]">{log.created_at}</td>
                      <td className="py-2.5 px-4 font-bold text-slate-900">{log.username}</td>
                      <td className="py-2.5 px-4">
                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200">
                          {log.role}
                        </span>
                      </td>
                      <td className="py-2.5 px-4">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-800">
                          {log.action}
                        </span>
                      </td>
                      <td className="py-2.5 px-4 font-mono text-slate-600">{log.entity_type}</td>
                      <td className="py-2.5 px-4 text-slate-800 max-w-sm truncate">{log.details || '-'}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Journal Voucher Breakdown Modal */}
      {selectedJournal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-xl w-full border border-slate-200 shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-200 pb-3">
              <div>
                <h3 className="text-base font-bold text-slate-900 flex items-center space-x-2">
                  <BookOpen className="h-4 w-4 text-indigo-600" />
                  <span>Journal Voucher #{selectedJournal.entry_number}</span>
                </h3>
                <span className="text-xs text-slate-500">
                  {selectedJournal.entry_date} &bull; Module: {selectedJournal.source_module}
                </span>
              </div>
              <button
                onClick={() => setSelectedJournal(null)}
                className="text-slate-400 hover:text-slate-600 text-lg font-bold"
              >
                &times;
              </button>
            </div>

            <p className="text-xs text-slate-700 bg-slate-50 p-2.5 rounded-lg border border-slate-200">
              <span className="font-semibold">Narration:</span> {selectedJournal.narration}
            </p>

            <div className="border border-slate-200 rounded-lg overflow-hidden">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-100 text-slate-700 font-semibold border-b border-slate-200">
                  <tr>
                    <th className="py-2 px-3">Account Code &amp; Name</th>
                    <th className="py-2 px-3 text-right">Debit (₹)</th>
                    <th className="py-2 px-3 text-right">Credit (₹)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 font-mono">
                  {selectedJournal.lines.map((line) => (
                    <tr key={line.id} className="hover:bg-slate-50">
                      <td className="py-2 px-3 font-sans">
                        <span className="font-mono font-bold text-indigo-600 mr-2">{line.account_code}</span>
                        <span>{line.account_name}</span>
                        {line.line_narration && (
                          <span className="block text-[10px] text-slate-500 italic">{line.line_narration}</span>
                        )}
                      </td>
                      <td className="py-2 px-3 text-right text-blue-600 font-bold">
                        {line.debit_paise > 0 ? `₹${(line.debit_paise / 100).toFixed(2)}` : '-'}
                      </td>
                      <td className="py-2 px-3 text-right text-emerald-600 font-bold">
                        {line.credit_paise > 0 ? `₹${(line.credit_paise / 100).toFixed(2)}` : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot className="bg-slate-100 border-t border-slate-300 font-mono font-bold text-xs">
                  <tr>
                    <td className="py-2 px-3 text-right font-sans uppercase">Total:</td>
                    <td className="py-2 px-3 text-right text-blue-700 font-bold">
                      ₹{(selectedJournal.total_debit_paise / 100).toFixed(2)}
                    </td>
                    <td className="py-2 px-3 text-right text-emerald-700 font-bold">
                      ₹{(selectedJournal.total_credit_paise / 100).toFixed(2)}
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>

            <div className="flex justify-end pt-3 border-t border-slate-200">
              <button
                onClick={() => setSelectedJournal(null)}
                className="px-4 py-1.5 border border-slate-300 text-slate-700 rounded text-xs font-semibold hover:bg-slate-50 transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
