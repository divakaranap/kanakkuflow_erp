import React, { useState, useEffect } from 'react'
import {
  Users,
  Truck,
  Package,
  Layers,
  Box,
  Tags,
  Calculator,
  Search,
  Info,
  CheckCircle2,
  AlertCircle,
  Loader2,
} from 'lucide-react'
import { masterService } from '../../services/masterService'
import { formatINR } from '../../lib/utils'
import type {
  Customer,
  Supplier,
  Product,
  RawMaterial,
  PackagingItem,
  PriceList,
  EffectivePrice,
} from '../../types/masters'

export function MasterDataOverview() {
  const [activeTab, setActiveTab] = useState<'customers' | 'suppliers' | 'products' | 'raw_materials' | 'packaging' | 'price_lists' | 'converter'>('customers')

  // Data states
  const [customers, setCustomers] = useState<Customer[]>([])
  const [suppliers, setSuppliers] = useState<Supplier[]>([])
  const [products, setProducts] = useState<Product[]>([])
  const [rawMaterials, setRawMaterials] = useState<RawMaterial[]>([])
  const [packaging, setPackaging] = useState<PackagingItem[]>([])
  const [priceLists, setPriceLists] = useState<PriceList[]>([])
  const [loading, setLoading] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')

  // Search & filter
  const [searchTerm, setSearchTerm] = useState('')

  // Effective price test states
  const [selectedCustId, setSelectedCustId] = useState('')
  const [selectedProdId, setSelectedProdId] = useState('')
  const [effectivePriceResult, setEffectivePriceResult] = useState<EffectivePrice | null>(null)

  // Unit converter states
  const [convQty, setConvQty] = useState('2000')
  const [convFrom, setConvFrom] = useState('g')
  const [convTo, setConvTo] = useState('kg')
  const [convCtnSize, setConvCtnSize] = useState('20')
  const [convResult, setConvResult] = useState<string | null>(null)
  const [convError, setConvError] = useState('')

  const loadAllData = async () => {
    setLoading(true)
    setErrorMsg('')
    try {
      const [c, s, p, rm, pkg, pl] = await Promise.all([
        masterService.getCustomers(),
        masterService.getSuppliers(),
        masterService.getProducts(),
        masterService.getRawMaterials(),
        masterService.getPackaging(),
        masterService.getPriceLists(),
      ])
      setCustomers(c)
      setSuppliers(s)
      setProducts(p)
      setRawMaterials(rm)
      setPackaging(pkg)
      setPriceLists(pl)
      if (c.length > 0) setSelectedCustId(c[0].id)
      if (p.length > 0) setSelectedProdId(p[0].id)
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to load master records. Ensure backend is running.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadAllData()
  }, [])

  const handleResolvePrice = async () => {
    if (!selectedCustId || !selectedProdId) return
    try {
      const res = await masterService.getEffectivePrice(selectedCustId, selectedProdId)
      setEffectivePriceResult(res)
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Error resolving effective price')
    }
  }

  const handleConvertUnits = async (e: React.FormEvent) => {
    e.preventDefault()
    setConvError('')
    setConvResult(null)
    try {
      const res = await masterService.convertUnit({
        quantity: convQty,
        from_unit: convFrom,
        to_unit: convTo,
        packets_per_carton: convFrom === 'carton' || convTo === 'carton' || convFrom === 'packet' || convTo === 'packet'
          ? parseInt(convCtnSize)
          : undefined,
      })
      setConvResult(res.converted_quantity)
    } catch (err: any) {
      setConvError(err.response?.data?.detail || 'Conversion failed')
    }
  }

  return (
    <div className="space-y-6">
      {/* Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <div className="bg-white p-4 rounded-xl border border-[#E2E8F0] shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-[#64748B]">
            <span className="text-xs font-semibold uppercase tracking-wider">Customers</span>
            <Users className="h-4 w-4 text-blue-600" />
          </div>
          <div className="text-2xl font-bold text-[#172033] mt-2">
            {loading ? <Loader2 className="h-5 w-5 animate-spin text-slate-400" /> : customers.length}
          </div>
          <div className="text-[11px] text-[#64748B] mt-1">Retailers &amp; Distributors</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-[#E2E8F0] shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-[#64748B]">
            <span className="text-xs font-semibold uppercase tracking-wider">Suppliers</span>
            <Truck className="h-4 w-4 text-emerald-600" />
          </div>
          <div className="text-2xl font-bold text-[#172033] mt-2">
            {loading ? <Loader2 className="h-5 w-5 animate-spin text-slate-400" /> : suppliers.length}
          </div>
          <div className="text-[11px] text-[#64748B] mt-1">Flour, Oil, Spices, Pkg</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-[#E2E8F0] shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-[#64748B]">
            <span className="text-xs font-semibold uppercase tracking-wider">Products</span>
            <Package className="h-4 w-4 text-purple-600" />
          </div>
          <div className="text-2xl font-bold text-[#172033] mt-2">
            {loading ? <Loader2 className="h-5 w-5 animate-spin text-slate-400" /> : products.length}
          </div>
          <div className="text-[11px] text-[#64748B] mt-1">Murukku &amp; Snacks</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-[#E2E8F0] shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-[#64748B]">
            <span className="text-xs font-semibold uppercase tracking-wider">Raw Materials</span>
            <Layers className="h-4 w-4 text-amber-600" />
          </div>
          <div className="text-2xl font-bold text-[#172033] mt-2">
            {loading ? <Loader2 className="h-5 w-5 animate-spin text-slate-400" /> : rawMaterials.length}
          </div>
          <div className="text-[11px] text-[#64748B] mt-1">Kg / Litre Master Items</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-[#E2E8F0] shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-[#64748B]">
            <span className="text-xs font-semibold uppercase tracking-wider">Packaging</span>
            <Box className="h-4 w-4 text-cyan-600" />
          </div>
          <div className="text-2xl font-bold text-[#172033] mt-2">
            {loading ? <Loader2 className="h-5 w-5 animate-spin text-slate-400" /> : packaging.length}
          </div>
          <div className="text-[11px] text-[#64748B] mt-1">Pouches &amp; Cartons</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-[#E2E8F0] shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-[#64748B]">
            <span className="text-xs font-semibold uppercase tracking-wider">Price Lists</span>
            <Tags className="h-4 w-4 text-rose-600" />
          </div>
          <div className="text-2xl font-bold text-[#172033] mt-2">
            {loading ? <Loader2 className="h-5 w-5 animate-spin text-slate-400" /> : priceLists.length}
          </div>
          <div className="text-[11px] text-[#64748B] mt-1">Tiered MRP &amp; Wholesale</div>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm overflow-hidden">
        <div className="flex items-center border-b border-[#E2E8F0] px-4 overflow-x-auto space-x-1">
          <button
            onClick={() => setActiveTab('customers')}
            className={`py-3.5 px-4 text-xs font-semibold border-b-2 transition flex items-center space-x-2 ${
              activeTab === 'customers'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-[#64748B] hover:text-[#172033]'
            }`}
          >
            <Users className="h-4 w-4" />
            <span>Customers ({customers.length})</span>
          </button>

          <button
            onClick={() => setActiveTab('suppliers')}
            className={`py-3.5 px-4 text-xs font-semibold border-b-2 transition flex items-center space-x-2 ${
              activeTab === 'suppliers'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-[#64748B] hover:text-[#172033]'
            }`}
          >
            <Truck className="h-4 w-4" />
            <span>Suppliers ({suppliers.length})</span>
          </button>

          <button
            onClick={() => setActiveTab('products')}
            className={`py-3.5 px-4 text-xs font-semibold border-b-2 transition flex items-center space-x-2 ${
              activeTab === 'products'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-[#64748B] hover:text-[#172033]'
            }`}
          >
            <Package className="h-4 w-4" />
            <span>Products ({products.length})</span>
          </button>

          <button
            onClick={() => setActiveTab('raw_materials')}
            className={`py-3.5 px-4 text-xs font-semibold border-b-2 transition flex items-center space-x-2 ${
              activeTab === 'raw_materials'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-[#64748B] hover:text-[#172033]'
            }`}
          >
            <Layers className="h-4 w-4" />
            <span>Raw Materials ({rawMaterials.length})</span>
          </button>

          <button
            onClick={() => setActiveTab('packaging')}
            className={`py-3.5 px-4 text-xs font-semibold border-b-2 transition flex items-center space-x-2 ${
              activeTab === 'packaging'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-[#64748B] hover:text-[#172033]'
            }`}
          >
            <Box className="h-4 w-4" />
            <span>Packaging ({packaging.length})</span>
          </button>

          <button
            onClick={() => setActiveTab('price_lists')}
            className={`py-3.5 px-4 text-xs font-semibold border-b-2 transition flex items-center space-x-2 ${
              activeTab === 'price_lists'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-[#64748B] hover:text-[#172033]'
            }`}
          >
            <Tags className="h-4 w-4" />
            <span>Price Lists ({priceLists.length})</span>
          </button>

          <button
            onClick={() => setActiveTab('converter')}
            className={`py-3.5 px-4 text-xs font-semibold border-b-2 transition flex items-center space-x-2 ${
              activeTab === 'converter'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-[#64748B] hover:text-[#172033]'
            }`}
          >
            <Calculator className="h-4 w-4" />
            <span>Unit Conversion Engine</span>
          </button>
        </div>

        {/* Tab Content Panes */}
        <div className="p-6">
          {errorMsg && (
            <div className="mb-4 p-3 bg-red-50 text-red-700 text-xs rounded-lg border border-red-200 flex items-center space-x-2">
              <AlertCircle className="h-4 w-4 flex-shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* TAB 1: CUSTOMERS */}
          {activeTab === 'customers' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-base font-bold text-[#172033]">Registered Customers</h3>
                  <p className="text-xs text-[#64748B]">B2B Retailers and Wholesalers with GST and State territory mapping</p>
                </div>
                <div className="relative">
                  <Search className="h-4 w-4 absolute left-3 top-2.5 text-slate-400" />
                  <input
                    type="text"
                    placeholder="Search name, code, GSTIN..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-9 pr-4 py-1.5 text-xs border border-[#E2E8F0] rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="overflow-x-auto border border-[#E2E8F0] rounded-lg">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 text-[#64748B] border-b border-[#E2E8F0]">
                    <tr>
                      <th className="py-2.5 px-3 font-semibold">Code</th>
                      <th className="py-2.5 px-3 font-semibold">Customer Name</th>
                      <th className="py-2.5 px-3 font-semibold">Type</th>
                      <th className="py-2.5 px-3 font-semibold">State</th>
                      <th className="py-2.5 px-3 font-semibold">GSTIN</th>
                      <th className="py-2.5 px-3 font-semibold">Phone</th>
                      <th className="py-2.5 px-3 font-semibold">Credit Limit</th>
                      <th className="py-2.5 px-3 font-semibold">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#E2E8F0]">
                    {customers
                      .filter((c) =>
                        !searchTerm ||
                        c.customer_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                        c.customer_code.toLowerCase().includes(searchTerm.toLowerCase()) ||
                        c.gstin.toLowerCase().includes(searchTerm.toLowerCase())
                      )
                      .map((c) => (
                        <tr key={c.id} className="hover:bg-slate-50/50">
                          <td className="py-3 px-3 font-mono font-semibold text-blue-600">{c.customer_code}</td>
                          <td className="py-3 px-3 font-semibold text-[#172033]">{c.customer_name}</td>
                          <td className="py-3 px-3">
                            <span
                              className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                                c.customer_type === 'RETAILER'
                                  ? 'bg-blue-50 text-blue-700 border-blue-200'
                                  : 'bg-emerald-50 text-emerald-700 border-emerald-200'
                              }`}
                            >
                              {c.customer_type}
                            </span>
                          </td>
                          <td className="py-3 px-3">
                            <span className="font-medium text-[#172033]">{c.state}</span>
                            <span className="text-[10px] text-slate-400 ml-1">({c.state_code})</span>
                          </td>
                          <td className="py-3 px-3 font-mono text-slate-600">{c.gstin}</td>
                          <td className="py-3 px-3 text-slate-600">{c.phone}</td>
                          <td className="py-3 px-3 font-semibold text-[#172033]">{formatINR(c.credit_limit_paise)}</td>
                          <td className="py-3 px-3">
                            <span className="inline-flex items-center text-emerald-600 font-semibold text-[11px]">
                              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 mr-1.5"></span> Active
                            </span>
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 2: SUPPLIERS */}
          {activeTab === 'suppliers' && (
            <div className="space-y-4">
              <div>
                <h3 className="text-base font-bold text-[#172033]">Approved Suppliers</h3>
                <p className="text-xs text-[#64748B]">Procurement partners for Flour, Cooking Oil, Spices, and Packaging</p>
              </div>

              <div className="overflow-x-auto border border-[#E2E8F0] rounded-lg">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 text-[#64748B] border-b border-[#E2E8F0]">
                    <tr>
                      <th className="py-2.5 px-3 font-semibold">Code</th>
                      <th className="py-2.5 px-3 font-semibold">Supplier Name</th>
                      <th className="py-2.5 px-3 font-semibold">Contact Person</th>
                      <th className="py-2.5 px-3 font-semibold">Location</th>
                      <th className="py-2.5 px-3 font-semibold">GSTIN</th>
                      <th className="py-2.5 px-3 font-semibold">Payment Terms</th>
                      <th className="py-2.5 px-3 font-semibold">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#E2E8F0]">
                    {suppliers.map((s) => (
                      <tr key={s.id} className="hover:bg-slate-50/50">
                        <td className="py-3 px-3 font-mono font-semibold text-emerald-600">{s.supplier_code}</td>
                        <td className="py-3 px-3 font-semibold text-[#172033]">{s.supplier_name}</td>
                        <td className="py-3 px-3 text-slate-600">{s.contact_person || '—'}</td>
                        <td className="py-3 px-3 text-slate-600">{s.city}, {s.state}</td>
                        <td className="py-3 px-3 font-mono text-slate-600">{s.gstin}</td>
                        <td className="py-3 px-3 font-medium text-slate-700">{s.payment_terms || 'Net 30'}</td>
                        <td className="py-3 px-3">
                          <span className="inline-flex items-center text-emerald-600 font-semibold text-[11px]">
                            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 mr-1.5"></span> Active
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 3: PRODUCTS */}
          {activeTab === 'products' && (
            <div className="space-y-4">
              <div>
                <h3 className="text-base font-bold text-[#172033]">Finished Goods Catalog</h3>
                <p className="text-xs text-[#64748B]">Products with benchmark pricing, HSN codes, and carton packing ratios</p>
              </div>

              <div className="overflow-x-auto border border-[#E2E8F0] rounded-lg">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 text-[#64748B] border-b border-[#E2E8F0]">
                    <tr>
                      <th className="py-2.5 px-3 font-semibold">SKU</th>
                      <th className="py-2.5 px-3 font-semibold">Product Name</th>
                      <th className="py-2.5 px-3 font-semibold">Category</th>
                      <th className="py-2.5 px-3 font-semibold">Pack Size</th>
                      <th className="py-2.5 px-3 font-semibold">HSN Code</th>
                      <th className="py-2.5 px-3 font-semibold">GST Rate</th>
                      <th className="py-2.5 px-3 font-semibold">MRP Selling Price</th>
                      <th className="py-2.5 px-3 font-semibold">Carton Packing</th>
                      <th className="py-2.5 px-3 font-semibold">Reorder Level</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#E2E8F0]">
                    {products.map((p) => (
                      <tr key={p.id} className="hover:bg-slate-50/50">
                        <td className="py-3 px-3 font-mono font-bold text-purple-600">{p.sku}</td>
                        <td className="py-3 px-3 font-semibold text-[#172033]">{p.product_name}</td>
                        <td className="py-3 px-3 text-slate-600">{p.category}</td>
                        <td className="py-3 px-3 font-medium text-[#172033]">{p.pack_size} {p.pack_size_unit}</td>
                        <td className="py-3 px-3 font-mono text-slate-500">{p.hsn_code}</td>
                        <td className="py-3 px-3 font-medium text-emerald-700">
                          {(Number(p.gst_rate) * 100).toFixed(0)}%
                        </td>
                        <td className="py-3 px-3 font-bold text-[#172033]">
                          {formatINR(p.selling_price_paise)}
                        </td>
                        <td className="py-3 px-3 font-medium text-blue-600">
                          {p.packets_per_carton} pkts / carton
                        </td>
                        <td className="py-3 px-3 text-slate-600">{p.reorder_level} {p.base_unit}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 4: RAW MATERIALS */}
          {activeTab === 'raw_materials' && (
            <div className="space-y-4">
              <div className="p-4 bg-amber-50 rounded-xl border border-amber-200 flex items-start space-x-3">
                <Info className="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" />
                <div className="text-xs text-amber-900 space-y-1">
                  <p className="font-semibold">Ledger Stock Rule (Phase 2 Master Data)</p>
                  <p className="text-amber-800 leading-relaxed">
                    Per system specification section 4.3, stock balances are never stored as manually editable numbers in master records.
                    Real stock quantities will be strictly ledger-aggregated from <code>stock_movements</code> when Phase 3 inventory is initiated.
                  </p>
                </div>
              </div>

              <div className="overflow-x-auto border border-[#E2E8F0] rounded-lg">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 text-[#64748B] border-b border-[#E2E8F0]">
                    <tr>
                      <th className="py-2.5 px-3 font-semibold">Material Code</th>
                      <th className="py-2.5 px-3 font-semibold">Material Name</th>
                      <th className="py-2.5 px-3 font-semibold">Category</th>
                      <th className="py-2.5 px-3 font-semibold">Base Unit</th>
                      <th className="py-2.5 px-3 font-semibold">Reorder Threshold</th>
                      <th className="py-2.5 px-3 font-semibold">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#E2E8F0]">
                    {rawMaterials.map((rm) => (
                      <tr key={rm.id} className="hover:bg-slate-50/50">
                        <td className="py-3 px-3 font-mono font-bold text-amber-700">{rm.material_code}</td>
                        <td className="py-3 px-3 font-semibold text-[#172033]">{rm.material_name}</td>
                        <td className="py-3 px-3 text-slate-600">{rm.category}</td>
                        <td className="py-3 px-3 font-mono font-semibold text-blue-700">{rm.base_unit}</td>
                        <td className="py-3 px-3 text-slate-600">{rm.reorder_level} {rm.base_unit}</td>
                        <td className="py-3 px-3">
                          <span className="inline-flex items-center text-emerald-600 font-semibold text-[11px]">
                            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 mr-1.5"></span> Active
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 5: PACKAGING */}
          {activeTab === 'packaging' && (
            <div className="space-y-4">
              <div>
                <h3 className="text-base font-bold text-[#172033]">Packaging Materials</h3>
                <p className="text-xs text-[#64748B]">Pouches and outer corrugated cartons tracked in exact units</p>
              </div>

              <div className="overflow-x-auto border border-[#E2E8F0] rounded-lg">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 text-[#64748B] border-b border-[#E2E8F0]">
                    <tr>
                      <th className="py-2.5 px-3 font-semibold">Item Code</th>
                      <th className="py-2.5 px-3 font-semibold">Packaging Name</th>
                      <th className="py-2.5 px-3 font-semibold">Category</th>
                      <th className="py-2.5 px-3 font-semibold">Base Unit</th>
                      <th className="py-2.5 px-3 font-semibold">Reorder Threshold</th>
                      <th className="py-2.5 px-3 font-semibold">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#E2E8F0]">
                    {packaging.map((pkg) => (
                      <tr key={pkg.id} className="hover:bg-slate-50/50">
                        <td className="py-3 px-3 font-mono font-bold text-cyan-700">{pkg.packaging_code}</td>
                        <td className="py-3 px-3 font-semibold text-[#172033]">{pkg.packaging_name}</td>
                        <td className="py-3 px-3 text-slate-600">{pkg.category}</td>
                        <td className="py-3 px-3 font-mono font-semibold text-blue-700">{pkg.base_unit}</td>
                        <td className="py-3 px-3 text-slate-600">{pkg.reorder_level} {pkg.base_unit}</td>
                        <td className="py-3 px-3">
                          <span className="inline-flex items-center text-emerald-600 font-semibold text-[11px]">
                            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 mr-1.5"></span> Active
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 6: PRICE LISTS & EFFECTIVE PRICING */}
          {activeTab === 'price_lists' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-base font-bold text-[#172033]">Active Price Lists &amp; Effective Pricing Resolver</h3>
                <p className="text-xs text-[#64748B]">Multi-tier customer pricing engine with automatic fallback resolution</p>
              </div>

              {/* Price Lists Table */}
              <div className="overflow-x-auto border border-[#E2E8F0] rounded-lg">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 text-[#64748B] border-b border-[#E2E8F0]">
                    <tr>
                      <th className="py-2.5 px-3 font-semibold">Price List Name</th>
                      <th className="py-2.5 px-3 font-semibold">Customer Scope</th>
                      <th className="py-2.5 px-3 font-semibold">Description</th>
                      <th className="py-2.5 px-3 font-semibold">Configured Products &amp; Rates</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#E2E8F0]">
                    {priceLists.map((pl) => (
                      <tr key={pl.id} className="hover:bg-slate-50/50">
                        <td className="py-3 px-3 font-bold text-[#172033]">{pl.name}</td>
                        <td className="py-3 px-3">
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-700 border border-slate-200">
                            {pl.customer_type}
                          </span>
                        </td>
                        <td className="py-3 px-3 text-slate-600">{pl.description || '—'}</td>
                        <td className="py-3 px-3">
                          <div className="space-y-1">
                            {pl.items.map((it) => (
                              <div key={it.id} className="flex items-center space-x-2 text-xs">
                                <span className="font-semibold text-purple-700">{it.product_sku || 'MUR-200'}:</span>
                                <span className="font-bold text-emerald-700">{formatINR(it.selling_price_paise)}</span>
                              </div>
                            ))}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Live Effective Price Resolver Box */}
              <div className="p-5 bg-slate-50 rounded-xl border border-[#E2E8F0] space-y-4">
                <div className="flex items-center space-x-2">
                  <Tags className="h-4 w-4 text-blue-600" />
                  <h4 className="text-sm font-bold text-[#172033]">Live Effective Price Resolver (Salesman &amp; Order Engine)</h4>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-[#172033] mb-1">Select Customer</label>
                    <select
                      value={selectedCustId}
                      onChange={(e) => setSelectedCustId(e.target.value)}
                      className="w-full px-3 py-2 text-xs border border-[#E2E8F0] rounded-lg bg-white"
                    >
                      {customers.map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.customer_name} ({c.customer_type})
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-[#172033] mb-1">Select Product</label>
                    <select
                      value={selectedProdId}
                      onChange={(e) => setSelectedProdId(e.target.value)}
                      className="w-full px-3 py-2 text-xs border border-[#E2E8F0] rounded-lg bg-white"
                    >
                      {products.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.sku} - {p.product_name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="flex items-end">
                    <button
                      onClick={handleResolvePrice}
                      className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs rounded-lg transition"
                    >
                      Resolve Effective Rate
                    </button>
                  </div>
                </div>

                {effectivePriceResult && (
                  <div className="p-4 bg-emerald-50 rounded-lg border border-emerald-200 flex items-center justify-between">
                    <div>
                      <div className="text-xs font-medium text-emerald-800">
                        Resolved for {effectivePriceResult.sku} ({effectivePriceResult.product_name})
                      </div>
                      <div className="text-[11px] text-emerald-700 mt-0.5">
                        Source Hierarchy: <span className="font-semibold">{effectivePriceResult.source}</span>
                        {effectivePriceResult.price_list_name && ` (${effectivePriceResult.price_list_name})`}
                      </div>
                    </div>
                    <div className="text-xl font-bold text-emerald-800">
                      {formatINR(effectivePriceResult.selling_price_paise)}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 7: UNIT CONVERTER ENGINE */}
          {activeTab === 'converter' && (
            <div className="max-w-2xl mx-auto space-y-6">
              <div className="text-center space-y-1">
                <h3 className="text-lg font-bold text-[#172033]">High-Precision Unit Conversion Engine</h3>
                <p className="text-xs text-[#64748B]">Zero-drift Decimal arithmetic supporting Weight, Volume, Pouches, and Cartons</p>
              </div>

              <form onSubmit={handleConvertUnits} className="bg-slate-50 p-6 rounded-2xl border border-[#E2E8F0] space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-[#172033] mb-1">Input Quantity</label>
                    <input
                      type="text"
                      value={convQty}
                      onChange={(e) => setConvQty(e.target.value)}
                      className="w-full px-3 py-2 text-sm border border-[#E2E8F0] rounded-lg bg-white"
                      placeholder="e.g. 2000"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-[#172033] mb-1">From Unit</label>
                    <select
                      value={convFrom}
                      onChange={(e) => setConvFrom(e.target.value)}
                      className="w-full px-3 py-2 text-sm border border-[#E2E8F0] rounded-lg bg-white"
                    >
                      <option value="g">Grams (g)</option>
                      <option value="kg">Kilograms (kg)</option>
                      <option value="ml">Millilitres (ml)</option>
                      <option value="litre">Litres (L)</option>
                      <option value="packet">Packets (pkt)</option>
                      <option value="carton">Cartons (ctn)</option>
                      <option value="piece">Pieces (pc)</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-[#172033] mb-1">To Unit</label>
                    <select
                      value={convTo}
                      onChange={(e) => setConvTo(e.target.value)}
                      className="w-full px-3 py-2 text-sm border border-[#E2E8F0] rounded-lg bg-white"
                    >
                      <option value="kg">Kilograms (kg)</option>
                      <option value="g">Grams (g)</option>
                      <option value="litre">Litres (L)</option>
                      <option value="ml">Millilitres (ml)</option>
                      <option value="carton">Cartons (ctn)</option>
                      <option value="packet">Packets (pkt)</option>
                      <option value="piece">Pieces (pc)</option>
                    </select>
                  </div>

                  {(convFrom === 'carton' || convTo === 'carton' || convFrom === 'packet' || convTo === 'packet') && (
                    <div>
                      <label className="block text-xs font-semibold text-[#172033] mb-1">Packets per Carton</label>
                      <input
                        type="number"
                        value={convCtnSize}
                        onChange={(e) => setConvCtnSize(e.target.value)}
                        className="w-full px-3 py-2 text-sm border border-[#E2E8F0] rounded-lg bg-white"
                        placeholder="20"
                      />
                    </div>
                  )}
                </div>

                <button
                  type="submit"
                  className="w-full py-2.5 px-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm rounded-lg transition shadow-md shadow-blue-500/20"
                >
                  Convert Quantity
                </button>
              </form>

              {convError && (
                <div className="p-3 bg-red-50 text-red-700 text-xs rounded-lg border border-red-200 flex items-center space-x-2">
                  <AlertCircle className="h-4 w-4 flex-shrink-0" />
                  <span>{convError}</span>
                </div>
              )}

              {convResult !== null && (
                <div className="p-5 bg-white rounded-xl border border-blue-200 shadow-sm text-center space-y-1">
                  <div className="text-xs font-semibold text-[#64748B]">Conversion Result</div>
                  <div className="text-2xl font-extrabold text-blue-600">
                    {convQty} {convFrom} = {convResult} {convTo}
                  </div>
                  <div className="text-[11px] text-emerald-600 flex items-center justify-center font-medium">
                    <CheckCircle2 className="h-3.5 w-3.5 mr-1" />
                    Exact Decimal Representation Validated
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
