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
  RefreshCw,
} from 'lucide-react'
import { masterService } from '../../services/masterService'
import { formatINR } from '../../lib/utils'
import { MetricCard } from '../../components/common/MetricCard'
import { StatusBadge } from '../../components/common/StatusBadge'
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
  const [activeTab, setActiveTab] = useState<
    'customers' | 'suppliers' | 'products' | 'raw_materials' | 'packaging' | 'price_lists' | 'converter'
  >('customers')

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
  const [customerTypeFilter, setCustomerTypeFilter] = useState<'ALL' | 'RETAILER' | 'DISTRIBUTOR'>('ALL')
  const [productCategoryFilter, setProductCategoryFilter] = useState<string>('ALL')

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
      if (c.length > 0 && !selectedCustId) setSelectedCustId(c[0].id)
      if (p.length > 0 && !selectedProdId) setSelectedProdId(p[0].id)
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
        packets_per_carton:
          convFrom === 'carton' || convTo === 'carton' || convFrom === 'packet' || convTo === 'packet'
            ? parseInt(convCtnSize)
            : undefined,
      })
      setConvResult(res.converted_quantity)
    } catch (err: any) {
      setConvError(err.response?.data?.detail || 'Conversion failed')
    }
  }

  // Filtered lists
  const filteredCustomers = customers.filter((c) => {
    const matchesSearch =
      !searchTerm ||
      c.customer_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.customer_code.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.gstin.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesType = customerTypeFilter === 'ALL' || c.customer_type === customerTypeFilter
    return matchesSearch && matchesType
  })

  const filteredProducts = products.filter((p) => {
    const matchesSearch =
      !searchTerm ||
      p.product_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.sku.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.hsn_code.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesCat = productCategoryFilter === 'ALL' || p.category === productCategoryFilter
    return matchesSearch && matchesCat
  })

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Page Heading & Header */}
      <div className="bg-white rounded-2xl border border-[#EAE8F1] p-6 shadow-card flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <div className="flex items-center space-x-3">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-[#17152B] tracking-tight">Master Data</h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[#F2EEFF] text-[#7655E8] border border-[#EAE8F1]">
              Core Entities
            </span>
          </div>
          <p className="text-sm text-[#77758A] mt-1">Manage your business entities and configurations.</p>
        </div>

        <div className="flex items-center space-x-2.5">
          <button
            onClick={loadAllData}
            disabled={loading}
            className="inline-flex items-center space-x-1.5 px-3.5 py-2 bg-[#F8F7FC] border border-[#EAE8F1] rounded-xl text-xs font-bold text-[#17152B] hover:bg-white hover:border-[#7655E8]/30 transition shadow-xs"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-[#7655E8] ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <MetricCard
          title="Customers"
          value={loading ? '—' : customers.length}
          icon={Users}
          badgeText="B2B"
          badgeVariant="purple"
          subtitle="Retail & Wholesale"
        />
        <MetricCard
          title="Suppliers"
          value={loading ? '—' : suppliers.length}
          icon={Truck}
          badgeText="Active"
          badgeVariant="info"
          subtitle="Ingredients & Pkg"
        />
        <MetricCard
          title="Products"
          value={loading ? '—' : products.length}
          icon={Package}
          badgeText="5 SKUs"
          badgeVariant="success"
          subtitle="Murukku & Sweets"
        />
        <MetricCard
          title="Raw Materials"
          value={loading ? '—' : rawMaterials.length}
          icon={Layers}
          badgeText="8 Items"
          badgeVariant="warning"
          subtitle="Flour, Oil, Spices"
        />
        <MetricCard
          title="Packaging"
          value={loading ? '—' : packaging.length}
          icon={Box}
          badgeText="6 Items"
          badgeVariant="purple"
          subtitle="Pouches & Cartons"
        />
        <MetricCard
          title="Price Lists"
          value={loading ? '—' : priceLists.length}
          icon={Tags}
          badgeText="Tiered"
          badgeVariant="success"
          subtitle="Multi-Tier MRP"
        />
      </div>

      {/* Main Tabs Navigation Container */}
      <div className="bg-white rounded-2xl border border-[#EAE8F1] shadow-card overflow-hidden">
        {/* Modern Lavender Tabs Switcher */}
        <div className="bg-[#F8F7FC] p-2 border-b border-[#EAE8F1] flex items-center space-x-1.5 overflow-x-auto">
          <button
            onClick={() => {
              setActiveTab('customers')
              setSearchTerm('')
            }}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center space-x-2 shrink-0 ${
              activeTab === 'customers'
                ? 'bg-white text-[#7655E8] shadow-sm'
                : 'text-[#77758A] hover:text-[#17152B] hover:bg-white/50'
            }`}
          >
            <Users className="h-3.5 w-3.5" />
            <span>Customers ({customers.length})</span>
          </button>

          <button
            onClick={() => {
              setActiveTab('suppliers')
              setSearchTerm('')
            }}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center space-x-2 shrink-0 ${
              activeTab === 'suppliers'
                ? 'bg-white text-[#7655E8] shadow-sm'
                : 'text-[#77758A] hover:text-[#17152B] hover:bg-white/50'
            }`}
          >
            <Truck className="h-3.5 w-3.5" />
            <span>Suppliers ({suppliers.length})</span>
          </button>

          <button
            onClick={() => {
              setActiveTab('products')
              setSearchTerm('')
            }}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center space-x-2 shrink-0 ${
              activeTab === 'products'
                ? 'bg-white text-[#7655E8] shadow-sm'
                : 'text-[#77758A] hover:text-[#17152B] hover:bg-white/50'
            }`}
          >
            <Package className="h-3.5 w-3.5" />
            <span>Products ({products.length})</span>
          </button>

          <button
            onClick={() => {
              setActiveTab('raw_materials')
              setSearchTerm('')
            }}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center space-x-2 shrink-0 ${
              activeTab === 'raw_materials'
                ? 'bg-white text-[#7655E8] shadow-sm'
                : 'text-[#77758A] hover:text-[#17152B] hover:bg-white/50'
            }`}
          >
            <Layers className="h-3.5 w-3.5" />
            <span>Raw Materials ({rawMaterials.length})</span>
          </button>

          <button
            onClick={() => {
              setActiveTab('packaging')
              setSearchTerm('')
            }}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center space-x-2 shrink-0 ${
              activeTab === 'packaging'
                ? 'bg-white text-[#7655E8] shadow-sm'
                : 'text-[#77758A] hover:text-[#17152B] hover:bg-white/50'
            }`}
          >
            <Box className="h-3.5 w-3.5" />
            <span>Packaging ({packaging.length})</span>
          </button>

          <button
            onClick={() => {
              setActiveTab('price_lists')
              setSearchTerm('')
            }}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center space-x-2 shrink-0 ${
              activeTab === 'price_lists'
                ? 'bg-white text-[#7655E8] shadow-sm'
                : 'text-[#77758A] hover:text-[#17152B] hover:bg-white/50'
            }`}
          >
            <Tags className="h-3.5 w-3.5" />
            <span>Price Lists ({priceLists.length})</span>
          </button>

          <button
            onClick={() => {
              setActiveTab('converter')
              setSearchTerm('')
            }}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center space-x-2 shrink-0 ${
              activeTab === 'converter'
                ? 'bg-white text-[#7655E8] shadow-sm'
                : 'text-[#77758A] hover:text-[#17152B] hover:bg-white/50'
            }`}
          >
            <Calculator className="h-3.5 w-3.5" />
            <span>Unit Conversion Engine</span>
          </button>
        </div>

        {/* Tab Content Panes */}
        <div className="p-6">
          {errorMsg && (
            <div className="mb-4 p-4 bg-red-50 text-red-700 text-xs rounded-xl border border-red-200 flex items-center space-x-2">
              <AlertCircle className="h-4 w-4 flex-shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* TAB 1: CUSTOMERS */}
          {activeTab === 'customers' && (
            <div className="space-y-4">
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
                <div>
                  <h3 className="text-base font-bold text-[#17152B]">Registered Customers</h3>
                  <p className="text-xs text-[#77758A]">B2B Retailers and Wholesalers with GST and State territory mapping</p>
                </div>
                <div className="flex items-center space-x-3 w-full sm:w-auto">
                  {/* Type Filter */}
                  <div className="bg-[#F8F7FC] p-1 rounded-xl border border-[#EAE8F1] flex items-center text-xs">
                    {(['ALL', 'RETAILER', 'DISTRIBUTOR'] as const).map((t) => (
                      <button
                        key={t}
                        onClick={() => setCustomerTypeFilter(t)}
                        className={`px-2.5 py-1 rounded-lg font-semibold transition ${
                          customerTypeFilter === t
                            ? 'bg-white text-[#7655E8] shadow-xs'
                            : 'text-[#77758A] hover:text-[#17152B]'
                        }`}
                      >
                        {t}
                      </button>
                    ))}
                  </div>

                  {/* Search */}
                  <div className="relative flex-1 sm:w-64">
                    <Search className="h-3.5 w-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-[#77758A]" />
                    <input
                      type="text"
                      placeholder="Search name, code, GSTIN..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="w-full pl-9 pr-3 py-1.5 text-xs bg-[#F8F7FC] border border-[#EAE8F1] rounded-xl text-[#17152B] focus:outline-none focus:ring-1 focus:ring-[#7655E8]"
                    />
                  </div>
                </div>
              </div>

              <div className="overflow-x-auto border border-[#EAE8F1] rounded-xl">
                <table className="w-full text-left text-xs">
                  <thead className="bg-[#F8F7FC] text-[#77758A] border-b border-[#EAE8F1]">
                    <tr>
                      <th className="py-3 px-4 font-bold">Code</th>
                      <th className="py-3 px-4 font-bold">Customer Name</th>
                      <th className="py-3 px-4 font-bold">Type</th>
                      <th className="py-3 px-4 font-bold">State</th>
                      <th className="py-3 px-4 font-bold">GSTIN</th>
                      <th className="py-3 px-4 font-bold">Phone</th>
                      <th className="py-3 px-4 font-bold text-right">Credit Limit</th>
                      <th className="py-3 px-4 font-bold text-center">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#EAE8F1]">
                    {filteredCustomers.length > 0 ? (
                      filteredCustomers.map((c) => (
                        <tr key={c.id} className="hover:bg-[#F8F7FC] transition-colors">
                          <td className="py-3 px-4 font-mono font-bold text-[#7655E8]">{c.customer_code}</td>
                          <td className="py-3 px-4 font-semibold text-[#17152B]">{c.customer_name}</td>
                          <td className="py-3 px-4">
                            <StatusBadge status={c.customer_type} dot={false} />
                          </td>
                          <td className="py-3 px-4">
                            <span className="font-medium text-[#17152B]">{c.state}</span>
                            <span className="text-[10px] text-[#77758A] ml-1 font-mono">({c.state_code})</span>
                          </td>
                          <td className="py-3 px-4 font-mono text-[#77758A]">{c.gstin}</td>
                          <td className="py-3 px-4 text-[#77758A]">{c.phone}</td>
                          <td className="py-3 px-4 font-bold text-[#17152B] text-right">{formatINR(c.credit_limit_paise)}</td>
                          <td className="py-3 px-4 text-center">
                            <StatusBadge status="ACTIVE" />
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={8} className="py-6 text-center text-[#77758A]">
                          No customers found matching filter.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 2: SUPPLIERS */}
          {activeTab === 'suppliers' && (
            <div className="space-y-4">
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
                <div>
                  <h3 className="text-base font-bold text-[#17152B]">Approved Suppliers</h3>
                  <p className="text-xs text-[#77758A]">Procurement partners for Flour, Cooking Oil, Spices, and Packaging</p>
                </div>
                <div className="relative w-full sm:w-64">
                  <Search className="h-3.5 w-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-[#77758A]" />
                  <input
                    type="text"
                    placeholder="Search supplier..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-9 pr-3 py-1.5 text-xs bg-[#F8F7FC] border border-[#EAE8F1] rounded-xl text-[#17152B] focus:outline-none focus:ring-1 focus:ring-[#7655E8]"
                  />
                </div>
              </div>

              <div className="overflow-x-auto border border-[#EAE8F1] rounded-xl">
                <table className="w-full text-left text-xs">
                  <thead className="bg-[#F8F7FC] text-[#77758A] border-b border-[#EAE8F1]">
                    <tr>
                      <th className="py-3 px-4 font-bold">Code</th>
                      <th className="py-3 px-4 font-bold">Supplier Name</th>
                      <th className="py-3 px-4 font-bold">Contact Person</th>
                      <th className="py-3 px-4 font-bold">Location</th>
                      <th className="py-3 px-4 font-bold">GSTIN</th>
                      <th className="py-3 px-4 font-bold">Payment Terms</th>
                      <th className="py-3 px-4 font-bold text-center">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#EAE8F1]">
                    {suppliers
                      .filter((s) => !searchTerm || s.supplier_name.toLowerCase().includes(searchTerm.toLowerCase()))
                      .map((s) => (
                        <tr key={s.id} className="hover:bg-[#F8F7FC] transition-colors">
                          <td className="py-3 px-4 font-mono font-bold text-[#16A36A]">{s.supplier_code}</td>
                          <td className="py-3 px-4 font-semibold text-[#17152B]">{s.supplier_name}</td>
                          <td className="py-3 px-4 text-[#77758A]">{s.contact_person || '—'}</td>
                          <td className="py-3 px-4 text-[#77758A]">
                            {s.city}, {s.state}
                          </td>
                          <td className="py-3 px-4 font-mono text-[#77758A]">{s.gstin}</td>
                          <td className="py-3 px-4 font-medium text-[#17152B]">{s.payment_terms || 'Net 30'}</td>
                          <td className="py-3 px-4 text-center">
                            <StatusBadge status="ACTIVE" />
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
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
                <div>
                  <h3 className="text-base font-bold text-[#17152B]">Finished Goods Catalog</h3>
                  <p className="text-xs text-[#77758A]">Products with benchmark pricing, HSN codes, and carton packing ratios</p>
                </div>
                <div className="flex items-center space-x-2 w-full sm:w-auto">
                  <select
                    value={productCategoryFilter}
                    onChange={(e) => setProductCategoryFilter(e.target.value)}
                    className="py-1.5 px-3 text-xs bg-[#F8F7FC] border border-[#EAE8F1] rounded-xl text-[#17152B] focus:outline-none focus:ring-1 focus:ring-[#7655E8]"
                  >
                    <option value="ALL">All Categories</option>
                    <option value="SNACKS">Snacks</option>
                    <option value="SWEETS">Sweets</option>
                  </select>
                  <div className="relative w-full sm:w-64">
                    <Search className="h-3.5 w-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-[#77758A]" />
                    <input
                      type="text"
                      placeholder="Search SKU or name..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="w-full pl-9 pr-3 py-1.5 text-xs bg-[#F8F7FC] border border-[#EAE8F1] rounded-xl text-[#17152B] focus:outline-none focus:ring-1 focus:ring-[#7655E8]"
                    />
                  </div>
                </div>
              </div>

              <div className="overflow-x-auto border border-[#EAE8F1] rounded-xl">
                <table className="w-full text-left text-xs">
                  <thead className="bg-[#F8F7FC] text-[#77758A] border-b border-[#EAE8F1]">
                    <tr>
                      <th className="py-3 px-4 font-bold">SKU</th>
                      <th className="py-3 px-4 font-bold">Product Name</th>
                      <th className="py-3 px-4 font-bold">Category</th>
                      <th className="py-3 px-4 font-bold">Pack Size</th>
                      <th className="py-3 px-4 font-bold">HSN Code</th>
                      <th className="py-3 px-4 font-bold">GST Rate</th>
                      <th className="py-3 px-4 font-bold text-right">Selling Price</th>
                      <th className="py-3 px-4 font-bold text-center">Carton Ratio</th>
                      <th className="py-3 px-4 font-bold text-right">Reorder Level</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#EAE8F1]">
                    {filteredProducts.map((p) => (
                      <tr key={p.id} className="hover:bg-[#F8F7FC] transition-colors">
                        <td className="py-3 px-4 font-mono font-bold text-[#7655E8]">{p.sku}</td>
                        <td className="py-3 px-4 font-semibold text-[#17152B]">{p.product_name}</td>
                        <td className="py-3 px-4 text-[#77758A]">{p.category}</td>
                        <td className="py-3 px-4 font-medium text-[#17152B]">
                          {p.pack_size} {p.pack_size_unit}
                        </td>
                        <td className="py-3 px-4 font-mono text-[#77758A]">{p.hsn_code}</td>
                        <td className="py-3 px-4 font-bold text-[#16A36A]">
                          {(Number(p.gst_rate) * 100).toFixed(0)}%
                        </td>
                        <td className="py-3 px-4 font-bold text-[#17152B] text-right">
                          {formatINR(p.selling_price_paise)}
                        </td>
                        <td className="py-3 px-4 font-semibold text-[#7655E8] text-center">
                          {p.packets_per_carton} pkts / ctn
                        </td>
                        <td className="py-3 px-4 text-[#77758A] text-right">
                          {p.reorder_level} {p.base_unit}
                        </td>
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
              <div className="p-4 bg-[#F2EEFF] rounded-2xl border border-[#EAE8F1] flex items-start space-x-3">
                <Info className="h-5 w-5 text-[#7655E8] flex-shrink-0 mt-0.5" />
                <div className="text-xs text-[#17152B] space-y-1">
                  <p className="font-bold">Ledger Stock Rule (Master Data &amp; Inventory Engine)</p>
                  <p className="text-[#77758A] leading-relaxed">
                    Stock balances are never stored as manually editable numbers in master records. Real stock quantities are
                    strictly aggregated from chronological movement journals in the Stock Movement Ledger.
                  </p>
                </div>
              </div>

              <div className="overflow-x-auto border border-[#EAE8F1] rounded-xl">
                <table className="w-full text-left text-xs">
                  <thead className="bg-[#F8F7FC] text-[#77758A] border-b border-[#EAE8F1]">
                    <tr>
                      <th className="py-3 px-4 font-bold">Material Code</th>
                      <th className="py-3 px-4 font-bold">Material Name</th>
                      <th className="py-3 px-4 font-bold">Category</th>
                      <th className="py-3 px-4 font-bold">Base Unit</th>
                      <th className="py-3 px-4 font-bold text-right">Reorder Threshold</th>
                      <th className="py-3 px-4 font-bold text-center">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#EAE8F1]">
                    {rawMaterials.map((rm) => (
                      <tr key={rm.id} className="hover:bg-[#F8F7FC] transition-colors">
                        <td className="py-3 px-4 font-mono font-bold text-[#E9A23B]">{rm.material_code}</td>
                        <td className="py-3 px-4 font-semibold text-[#17152B]">{rm.material_name}</td>
                        <td className="py-3 px-4 text-[#77758A]">{rm.category}</td>
                        <td className="py-3 px-4 font-mono font-bold text-[#7655E8]">{rm.base_unit}</td>
                        <td className="py-3 px-4 text-[#77758A] text-right">
                          {rm.reorder_level} {rm.base_unit}
                        </td>
                        <td className="py-3 px-4 text-center">
                          <StatusBadge status="ACTIVE" />
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
                <h3 className="text-base font-bold text-[#17152B]">Packaging Materials</h3>
                <p className="text-xs text-[#77758A]">Pouches and outer corrugated master cartons tracked in exact units</p>
              </div>

              <div className="overflow-x-auto border border-[#EAE8F1] rounded-xl">
                <table className="w-full text-left text-xs">
                  <thead className="bg-[#F8F7FC] text-[#77758A] border-b border-[#EAE8F1]">
                    <tr>
                      <th className="py-3 px-4 font-bold">Item Code</th>
                      <th className="py-3 px-4 font-bold">Packaging Name</th>
                      <th className="py-3 px-4 font-bold">Category</th>
                      <th className="py-3 px-4 font-bold">Base Unit</th>
                      <th className="py-3 px-4 font-bold text-right">Reorder Threshold</th>
                      <th className="py-3 px-4 font-bold text-center">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#EAE8F1]">
                    {packaging.map((pkg) => (
                      <tr key={pkg.id} className="hover:bg-[#F8F7FC] transition-colors">
                        <td className="py-3 px-4 font-mono font-bold text-[#4385E8]">{pkg.packaging_code}</td>
                        <td className="py-3 px-4 font-semibold text-[#17152B]">{pkg.packaging_name}</td>
                        <td className="py-3 px-4 text-[#77758A]">{pkg.category}</td>
                        <td className="py-3 px-4 font-mono font-bold text-[#7655E8]">{pkg.base_unit}</td>
                        <td className="py-3 px-4 text-[#77758A] text-right">
                          {pkg.reorder_level} {pkg.base_unit}
                        </td>
                        <td className="py-3 px-4 text-center">
                          <StatusBadge status="ACTIVE" />
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
                <h3 className="text-base font-bold text-[#17152B]">Active Price Lists &amp; Effective Pricing Resolver</h3>
                <p className="text-xs text-[#77758A]">Multi-tier customer pricing engine with automatic fallback resolution</p>
              </div>

              {/* Price Lists Table */}
              <div className="overflow-x-auto border border-[#EAE8F1] rounded-xl">
                <table className="w-full text-left text-xs">
                  <thead className="bg-[#F8F7FC] text-[#77758A] border-b border-[#EAE8F1]">
                    <tr>
                      <th className="py-3 px-4 font-bold">Price List Name</th>
                      <th className="py-3 px-4 font-bold">Customer Scope</th>
                      <th className="py-3 px-4 font-bold">Description</th>
                      <th className="py-3 px-4 font-bold">Configured Products &amp; Rates</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#EAE8F1]">
                    {priceLists.map((pl) => (
                      <tr key={pl.id} className="hover:bg-[#F8F7FC] transition-colors">
                        <td className="py-3 px-4 font-bold text-[#17152B]">{pl.name}</td>
                        <td className="py-3 px-4">
                          <StatusBadge status={pl.customer_type} dot={false} />
                        </td>
                        <td className="py-3 px-4 text-[#77758A]">{pl.description || '—'}</td>
                        <td className="py-3 px-4">
                          <div className="space-y-1">
                            {pl.items.map((it) => (
                              <div key={it.id} className="flex items-center space-x-2 text-xs">
                                <span className="font-semibold text-[#7655E8]">{it.product_sku || 'MUR-200'}:</span>
                                <span className="font-bold text-[#16A36A]">{formatINR(it.selling_price_paise)}</span>
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
              <div className="p-6 bg-[#FAFAFD] rounded-2xl border border-[#EAE8F1] space-y-4">
                <div className="flex items-center space-x-2">
                  <Tags className="h-4 w-4 text-[#7655E8]" />
                  <h4 className="text-sm font-bold text-[#17152B]">Live Effective Price Resolver (Sales Order Engine)</h4>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-xs font-bold text-[#17152B] mb-1">Select Customer</label>
                    <select
                      value={selectedCustId}
                      onChange={(e) => setSelectedCustId(e.target.value)}
                      className="w-full px-3 py-2 text-xs border border-[#EAE8F1] rounded-xl bg-white focus:outline-none focus:ring-1 focus:ring-[#7655E8]"
                    >
                      {customers.map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.customer_name} ({c.customer_type})
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-[#17152B] mb-1">Select Product</label>
                    <select
                      value={selectedProdId}
                      onChange={(e) => setSelectedProdId(e.target.value)}
                      className="w-full px-3 py-2 text-xs border border-[#EAE8F1] rounded-xl bg-white focus:outline-none focus:ring-1 focus:ring-[#7655E8]"
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
                      className="w-full py-2.5 px-4 bg-gradient-to-r from-[#7655E8] to-[#9675F5] hover:opacity-95 text-white font-bold text-xs rounded-xl transition shadow-md shadow-[#7655E8]/20"
                    >
                      Resolve Effective Rate
                    </button>
                  </div>
                </div>

                {effectivePriceResult && (
                  <div className="p-4 bg-white rounded-xl border border-emerald-200 shadow-sm flex items-center justify-between">
                    <div>
                      <div className="text-xs font-semibold text-[#16A36A]">
                        Resolved for {effectivePriceResult.sku} ({effectivePriceResult.product_name})
                      </div>
                      <div className="text-[11px] text-[#77758A] mt-0.5">
                        Hierarchy Source: <span className="font-bold text-[#17152B]">{effectivePriceResult.source}</span>
                        {effectivePriceResult.price_list_name && ` (${effectivePriceResult.price_list_name})`}
                      </div>
                    </div>
                    <div className="text-2xl font-extrabold text-[#16A36A]">
                      {formatINR(effectivePriceResult.selling_price_paise)}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 7: UNIT CONVERTER ENGINE */}
          {activeTab === 'converter' && (
            <div className="max-w-2xl mx-auto space-y-6 py-4">
              <div className="text-center space-y-1">
                <h3 className="text-xl font-extrabold text-[#17152B]">High-Precision Unit Conversion Engine</h3>
                <p className="text-xs text-[#77758A]">
                  Zero-drift Decimal arithmetic supporting Weight (g ↔ kg), Volume (ml ↔ L), Pouches, and Cartons
                </p>
              </div>

              <form
                onSubmit={handleConvertUnits}
                className="bg-[#FAFAFD] p-6 rounded-2xl border border-[#EAE8F1] space-y-4 shadow-sm"
              >
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold text-[#17152B] mb-1">Input Quantity</label>
                    <input
                      type="text"
                      value={convQty}
                      onChange={(e) => setConvQty(e.target.value)}
                      className="w-full px-3 py-2 text-sm border border-[#EAE8F1] rounded-xl bg-white focus:outline-none focus:ring-1 focus:ring-[#7655E8]"
                      placeholder="e.g. 2000"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-[#17152B] mb-1">From Unit</label>
                    <select
                      value={convFrom}
                      onChange={(e) => setConvFrom(e.target.value)}
                      className="w-full px-3 py-2 text-sm border border-[#EAE8F1] rounded-xl bg-white focus:outline-none focus:ring-1 focus:ring-[#7655E8]"
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
                    <label className="block text-xs font-bold text-[#17152B] mb-1">To Unit</label>
                    <select
                      value={convTo}
                      onChange={(e) => setConvTo(e.target.value)}
                      className="w-full px-3 py-2 text-sm border border-[#EAE8F1] rounded-xl bg-white focus:outline-none focus:ring-1 focus:ring-[#7655E8]"
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
                      <label className="block text-xs font-bold text-[#17152B] mb-1">Packets per Carton</label>
                      <input
                        type="number"
                        value={convCtnSize}
                        onChange={(e) => setConvCtnSize(e.target.value)}
                        className="w-full px-3 py-2 text-sm border border-[#EAE8F1] rounded-xl bg-white focus:outline-none focus:ring-1 focus:ring-[#7655E8]"
                        placeholder="20"
                      />
                    </div>
                  )}
                </div>

                <button
                  type="submit"
                  className="w-full py-2.5 px-4 bg-gradient-to-r from-[#7655E8] to-[#9675F5] hover:opacity-95 text-white font-bold text-sm rounded-xl transition shadow-md shadow-[#7655E8]/20"
                >
                  Convert Quantity
                </button>
              </form>

              {convError && (
                <div className="p-3 bg-red-50 text-red-700 text-xs rounded-xl border border-red-200 flex items-center space-x-2">
                  <AlertCircle className="h-4 w-4 flex-shrink-0" />
                  <span>{convError}</span>
                </div>
              )}

              {convResult !== null && (
                <div className="p-6 bg-white rounded-2xl border border-[#EAE8F1] shadow-card text-center space-y-1">
                  <div className="text-xs font-bold text-[#77758A] uppercase tracking-wider">Converted Value</div>
                  <div className="text-3xl font-extrabold text-[#7655E8]">
                    {convQty} {convFrom} = {convResult} {convTo}
                  </div>
                  <div className="text-xs text-[#16A36A] flex items-center justify-center font-bold pt-1">
                    <CheckCircle2 className="h-4 w-4 mr-1.5" />
                    Exact High-Precision Decimal Math Validated
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
