import React from 'react'
import {
  Settings,
  Building,
  ShieldCheck,
  Coins,
  CheckCircle2,
  Server,
  User,
} from 'lucide-react'
import { authService } from '../../services/authService'

export const SettingsOverview: React.FC = () => {
  const currentUser = authService.getStoredUser()

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Header */}
      <div className="bg-white rounded-2xl border border-[#EAE8F1] p-6 shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#7655E8] to-[#9675F5] flex items-center justify-center text-white shadow-md shadow-[#7655E8]/20">
              <Settings className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-xl sm:text-2xl font-extrabold text-[#17152B]">
                System Settings &amp; Configuration
              </h1>
              <p className="text-xs text-[#77758A]">
                Company master parameters, statutory fiscal year, and ledger audit parameters
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-[#F2EEFF] text-[#7655E8] border border-[#EAE8F1] text-xs font-semibold">
          <ShieldCheck className="w-4 h-4 text-[#7655E8]" />
          <span>System Healthy &bull; Double-Entry Enforced</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Company Master Card */}
        <div className="bg-white rounded-2xl border border-[#EAE8F1] p-6 shadow-xs">
          <div className="flex items-center gap-2.5 pb-4 border-b border-[#F0EFF6]">
            <Building className="w-5 h-5 text-[#7655E8]" />
            <h3 className="text-sm font-bold text-[#17152B]">Company Entity Profile</h3>
          </div>
          <div className="mt-4 space-y-3.5 text-xs">
            <div>
              <span className="text-[#77758A] block">Legal Entity Name</span>
              <span className="font-bold text-[#17152B] text-sm">KANAKKUFLOW FOOD PRODUCTS</span>
            </div>
            <div>
              <span className="text-[#77758A] block">GSTIN Registration</span>
              <span className="font-mono font-semibold text-[#17152B]">33AABCF1234F1Z5</span>
            </div>
            <div>
              <span className="text-[#77758A] block">State Code &amp; Jurisdiction</span>
              <span className="font-semibold text-[#17152B]">33 - Tamil Nadu (Tiruchirappalli)</span>
            </div>
            <div>
              <span className="text-[#77758A] block">Statutory Fiscal Year</span>
              <span className="font-semibold text-[#7655E8]">2026 – 2027 (Active)</span>
            </div>
          </div>
        </div>

        {/* Currency & Financial Precision */}
        <div className="bg-white rounded-2xl border border-[#EAE8F1] p-6 shadow-xs">
          <div className="flex items-center gap-2.5 pb-4 border-b border-[#F0EFF6]">
            <Coins className="w-5 h-5 text-[#16A36A]" />
            <h3 className="text-sm font-bold text-[#17152B]">Financial Precision &amp; Math</h3>
          </div>
          <div className="mt-4 space-y-3.5 text-xs">
            <div>
              <span className="text-[#77758A] block">Ledger Math Engine</span>
              <span className="font-semibold text-[#17152B]">Strict Integer Arithmetic (Paise)</span>
            </div>
            <div>
              <span className="text-[#77758A] block">Rounding Drift Prevention</span>
              <span className="inline-flex items-center gap-1 font-semibold text-[#16A36A]">
                <CheckCircle2 className="w-3.5 h-3.5" />
                Zero Float Accumulation (₹ 0.00 discrepancy)
              </span>
            </div>
            <div>
              <span className="text-[#77758A] block">Unit Conversion Engine</span>
              <span className="font-semibold text-[#17152B]">High-precision Decimal (grams &bull; pkts &bull; kg)</span>
            </div>
            <div>
              <span className="text-[#77758A] block">GST Tax Calculation</span>
              <span className="font-semibold text-[#17152B]">Intra-State (CGST 2.5% + SGST 2.5%) / IGST 5%</span>
            </div>
          </div>
        </div>

        {/* Current User & Role Profile */}
        <div className="bg-white rounded-2xl border border-[#EAE8F1] p-6 shadow-xs">
          <div className="flex items-center gap-2.5 pb-4 border-b border-[#F0EFF6]">
            <User className="w-5 h-5 text-[#9675F5]" />
            <h3 className="text-sm font-bold text-[#17152B]">Active Session &amp; Credentials</h3>
          </div>
          <div className="mt-4 space-y-3.5 text-xs">
            <div>
              <span className="text-[#77758A] block">Full Name</span>
              <span className="font-bold text-[#17152B] text-sm">{currentUser?.full_name || 'System User'}</span>
            </div>
            <div>
              <span className="text-[#77758A] block">User Handle / Login</span>
              <span className="font-mono text-[#7655E8]">@{currentUser?.username || 'user'}</span>
            </div>
            <div>
              <span className="text-[#77758A] block">Role Permissions</span>
              <span className="inline-block mt-0.5 px-2.5 py-0.5 rounded-full text-xs font-bold bg-[#F2EEFF] text-[#7655E8]">
                {currentUser?.role || 'ADMIN'}
              </span>
            </div>
            <div>
              <span className="text-[#77758A] block">Authentication Token</span>
              <span className="font-semibold text-[#16A36A]">JWT Bearer (Valid &bull; 60m expiry)</span>
            </div>
          </div>
        </div>
      </div>

      {/* Audit System Information */}
      <div className="bg-white rounded-2xl border border-[#EAE8F1] p-6 shadow-xs">
        <div className="flex items-center justify-between pb-4 border-b border-[#F0EFF6]">
          <div className="flex items-center gap-2.5">
            <Server className="w-5 h-5 text-[#7655E8]" />
            <div>
              <h3 className="text-sm font-bold text-[#17152B]">Audit Engine &amp; Immutable Log</h3>
              <p className="text-xs text-[#77758A]">Tamper-evident verification across all business documents</p>
            </div>
          </div>
          <span className="text-xs font-semibold px-2.5 py-1 rounded-lg bg-[#EBF9F1] text-[#16A36A]">
            Active
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-4 text-xs">
          <div className="p-4 rounded-xl bg-[#F8F7FC] border border-[#EAE8F1]">
            <span className="text-[#77758A] block">Transaction Traceability</span>
            <span className="font-bold text-[#17152B] text-base mt-1 block">100% End-to-End</span>
            <span className="text-[#77758A] text-[11px] mt-0.5 block">Order &rarr; Run &rarr; Invoice &rarr; Journal</span>
          </div>

          <div className="p-4 rounded-xl bg-[#F8F7FC] border border-[#EAE8F1]">
            <span className="text-[#77758A] block">Database Backend</span>
            <span className="font-bold text-[#17152B] text-base mt-1 block">PostgreSQL 16</span>
            <span className="text-[#77758A] text-[11px] mt-0.5 block">ACID-compliant transactions</span>
          </div>

          <div className="p-4 rounded-xl bg-[#F8F7FC] border border-[#EAE8F1]">
            <span className="text-[#77758A] block">Report Generation</span>
            <span className="font-bold text-[#17152B] text-base mt-1 block">Audit Center Ready</span>
            <span className="text-[#77758A] text-[11px] mt-0.5 block">CSV &bull; OpenPyXL &bull; ReportLab PDF</span>
          </div>
        </div>
      </div>
    </div>
  )
}
