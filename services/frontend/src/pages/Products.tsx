import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { Package, Layers, Store, Search, AlertTriangle, ChevronLeft, ChevronRight, X, ExternalLink } from 'lucide-react'
import { api } from '../api/client'

function formatMoney(val: number) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(val)
}

type Tab = 'catalog' | 'batches' | 'vendors' | 'by-vendor' | 'expiring'

function ProductDetailModal({ product, onClose }: { product: any; onClose: () => void }) {
  const navigate = useNavigate()
  const { data: batchData, isLoading: batchLoading } = useQuery({
    queryKey: ['product-detail-batches', product.sku],
    queryFn: async () => {
      const { data } = await api.get('/products/batches', { params: { search: product.sku, limit: 50 } })
      return data
    },
    enabled: !!product.sku,
  })

  useEffect(() => {
    const h = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', h)
    return () => window.removeEventListener('keydown', h)
  }, [onClose])

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center gap-4 min-w-0">
            <div className="w-12 h-12 bg-emerald-100 rounded-full flex items-center justify-center flex-shrink-0">
              <Package className="w-6 h-6 text-emerald-600" />
            </div>
            <div className="min-w-0">
              <h2 className="text-xl font-bold text-gray-900 truncate">{product.item}</h2>
              <p className="text-sm text-gray-500">SKU: {product.sku}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-lg flex-shrink-0"><X className="w-5 h-5" /></button>
        </div>
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Product Info Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-xs text-gray-500 mb-1">Category</p>
              <p className="font-medium text-gray-900">{product.category || '-'}</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-xs text-gray-500 mb-1">Brand</p>
              <p className="font-medium text-gray-900">{product.brand || '-'}</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-xs text-gray-500 mb-1">Vendor</p>
              <p className="font-medium text-emerald-600">{product.vendor || '-'}</p>
            </div>
            <div className="bg-blue-50 rounded-lg p-3">
              <p className="text-xs text-blue-600 mb-1">Unit Price</p>
              <p className="text-xl font-bold text-blue-900">{product.unit_price ? formatMoney(product.unit_price) : '-'}</p>
            </div>
            <div className="bg-green-50 rounded-lg p-3">
              <p className="text-xs text-green-600 mb-1">In Stock</p>
              <p className="text-xl font-bold text-green-900">{product.inventory_available ?? '-'}</p>
            </div>
            <div className={`${product.active ? 'bg-green-50' : 'bg-red-50'} rounded-lg p-3`}>
              <p className={`text-xs ${product.active ? 'text-green-600' : 'text-red-600'} mb-1`}>Status</p>
              <p className={`text-xl font-bold ${product.active ? 'text-green-900' : 'text-red-900'}`}>{product.active ? 'Active' : 'Inactive'}</p>
            </div>
          </div>

          {/* Pricing Tiers */}
          {(product.tier_1_price || product.tier_2_price) && (
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-2">Pricing Tiers</h3>
              <div className="grid grid-cols-3 gap-2 text-sm">
                {product.tier_1_price != null && <div className="bg-gray-50 rounded p-2"><span className="text-gray-500">Tier 1:</span> <span className="font-medium">{formatMoney(product.tier_1_price)}</span></div>}
                {product.tier_2_price != null && <div className="bg-gray-50 rounded p-2"><span className="text-gray-500">Tier 2:</span> <span className="font-medium">{formatMoney(product.tier_2_price)}</span></div>}
                {product.tier_3_price != null && <div className="bg-gray-50 rounded p-2"><span className="text-gray-500">Tier 3:</span> <span className="font-medium">{formatMoney(product.tier_3_price)}</span></div>}
              </div>
            </div>
          )}

          {/* Cannabinoid Info */}
          {(product.thc_pct || product.cbd_pct) && (
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-2">Cannabinoid Content</h3>
              <div className="flex gap-3">
                {product.thc_pct != null && <div className="bg-purple-50 rounded-lg px-4 py-2"><span className="text-xs text-purple-600">THC</span><div className="text-lg font-bold text-purple-900">{product.thc_pct}%</div></div>}
                {product.cbd_pct != null && <div className="bg-blue-50 rounded-lg px-4 py-2"><span className="text-xs text-blue-600">CBD</span><div className="text-lg font-bold text-blue-900">{product.cbd_pct}%</div></div>}
              </div>
            </div>
          )}

          {/* Batches */}
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Batches ({batchData?.total || 0})</h3>
            {batchLoading ? (
              <div className="text-center py-4 text-gray-500 text-sm">Loading batches...</div>
            ) : batchData?.items?.length === 0 ? (
              <div className="text-center py-4 text-gray-500 text-sm">No batches found for this product</div>
            ) : (
              <div className="border rounded-lg overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-3 py-2 text-left text-xs font-semibold text-gray-600">Batch ID</th>
                      <th className="px-3 py-2 text-left text-xs font-semibold text-gray-600">Status</th>
                      <th className="px-3 py-2 text-right text-xs font-semibold text-gray-600">Qty</th>
                      <th className="px-3 py-2 text-right text-xs font-semibold text-gray-600">THC %</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {batchData?.items?.slice(0, 10).map((b: any) => (
                      <tr key={b.id} className="hover:bg-gray-50">
                        <td className="px-3 py-2 font-mono text-gray-600">{b.batch_id || '-'}</td>
                        <td className="px-3 py-2">
                          <span className={`px-2 py-0.5 rounded-full text-xs ${b.status === 'Active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>{b.status || '-'}</span>
                        </td>
                        <td className="px-3 py-2 text-right">{b.current_qty ?? '-'}</td>
                        <td className="px-3 py-2 text-right">{b.total_thc_pct ? `${b.total_thc_pct}%` : '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-2">
            <button
              onClick={() => navigate(`/transactions?search=${encodeURIComponent(product.item)}`)}
              className="flex-1 btn btn-primary flex items-center justify-center gap-2"
            >
              <ExternalLink className="w-4 h-4" />
              View Transactions
            </button>
            <button
              onClick={() => navigate(`/reports?tab=byproduct&search=${encodeURIComponent(product.item)}`)}
              className="flex-1 btn btn-secondary flex items-center justify-center gap-2"
            >
              <ExternalLink className="w-4 h-4" />
              Sales Report
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function Products() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [activeTab, setActiveTab] = useState<Tab>('catalog')
  const [searchInput, setSearchInput] = useState('')
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(0)
  const [selectedProduct, setSelectedProduct] = useState<any>(null)
  const limit = 25

  // Read URL params on mount
  useEffect(() => {
    const urlSearch = searchParams.get('search')
    const urlTab = searchParams.get('tab') as Tab | null
    if (urlTab && ['catalog', 'batches', 'vendors', 'by-vendor', 'expiring'].includes(urlTab)) {
      setActiveTab(urlTab)
    }
    if (urlSearch) {
      setSearchInput(urlSearch)
      setSearch(urlSearch)
    }
    if (urlSearch || urlTab) setSearchParams({})
  }, [])

  useEffect(() => {
    const timer = setTimeout(() => {
      setSearch(searchInput)
      setPage(0)
    }, 300)
    return () => clearTimeout(timer)
  }, [searchInput])

  const handleTabChange = (tab: Tab) => {
    setActiveTab(tab)
    setPage(0)
  }

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['product-stats'],
    queryFn: async () => {
      const { data } = await api.get('/products/stats')
      return data
    },
  })

  const { data: catalog, isLoading: catalogLoading } = useQuery({
    queryKey: ['product-catalog', search, page],
    queryFn: async () => {
      const { data } = await api.get('/products', { params: { skip: page * limit, limit, search: search || undefined } })
      return data
    },
    enabled: activeTab === 'catalog',
  })

  const { data: batches, isLoading: batchesLoading } = useQuery({
    queryKey: ['product-batches', search, page],
    queryFn: async () => {
      const { data } = await api.get('/products/batches', { params: { skip: page * limit, limit, search: search || undefined } })
      return data
    },
    enabled: activeTab === 'batches',
  })

  const { data: vendors, isLoading: vendorsLoading } = useQuery({
    queryKey: ['vendors', search, page],
    queryFn: async () => {
      const { data } = await api.get('/products/vendors', { params: { skip: page * limit, limit, search: search || undefined } })
      return data
    },
    enabled: activeTab === 'vendors',
  })

  const { data: byVendor, isLoading: byVendorLoading } = useQuery({
    queryKey: ['products-by-vendor', search, page],
    queryFn: async () => {
      const { data } = await api.get('/products/by-vendor', { params: { skip: page * limit, limit } })
      return data
    },
    enabled: activeTab === 'by-vendor',
  })

  const { data: expiring, isLoading: expiringLoading } = useQuery({
    queryKey: ['products-expiring', page],
    queryFn: async () => {
      const { data } = await api.get('/products/sell-by-expire', { params: { skip: page * limit, limit } })
      return data
    },
    enabled: activeTab === 'expiring',
  })

  const tabs: { key: Tab; label: string }[] = [
    { key: 'catalog', label: 'Catalog' },
    { key: 'batches', label: 'Batches' },
    { key: 'vendors', label: 'Vendors' },
    { key: 'by-vendor', label: 'By Vendor' },
    { key: 'expiring', label: 'Expiring' },
  ]

  const getCurrentData = () => {
    switch (activeTab) {
      case 'catalog': return { data: catalog, loading: catalogLoading }
      case 'batches': return { data: batches, loading: batchesLoading }
      case 'vendors': return { data: vendors, loading: vendorsLoading }
      case 'by-vendor': return { data: byVendor, loading: byVendorLoading }
      case 'expiring': return { data: expiring, loading: expiringLoading }
    }
  }

  const { data: currentData, loading } = getCurrentData()
  const totalPages = Math.ceil((currentData?.total || 0) / limit)

  const renderPagination = () => (
    <div className="px-4 py-3 border-t border-gray-200 bg-gray-50 flex flex-col sm:flex-row items-center justify-between gap-2">
      <div className="text-sm text-gray-500">
        {(currentData?.total || 0) > 0
          ? `Showing ${page * limit + 1} - ${Math.min((page + 1) * limit, currentData?.total || 0)} of ${(currentData?.total || 0).toLocaleString()}`
          : 'No records'}
      </div>
      <div className="flex gap-2">
        <button onClick={() => setPage(Math.max(0, page - 1))} disabled={page === 0} className="p-2 rounded hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"><ChevronLeft className="w-5 h-5" /></button>
        <span className="px-4 py-2 text-sm">Page {page + 1} of {totalPages || 1}</span>
        <button onClick={() => setPage(page + 1)} disabled={page >= totalPages - 1} className="p-2 rounded hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"><ChevronRight className="w-5 h-5" /></button>
      </div>
    </div>
  )

  const renderEmpty = (msg: string) => (
    <tr><td colSpan={20} className="px-4 py-8 text-center text-gray-500">{msg}</td></tr>
  )

  return (
    <div className="space-y-6">
      {/* Product Detail Modal */}
      {selectedProduct && <ProductDetailModal product={selectedProduct} onClose={() => setSelectedProduct(null)} />}

      <div>
        <h1 className="text-2xl font-bold text-gray-900">Products</h1>
        <p className="text-gray-500">Product catalog, batches, and vendor directory</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card p-5">
          <div className="p-2 bg-blue-100 rounded-lg w-fit"><Package className="w-5 h-5 text-blue-600" /></div>
          <div className="mt-3">
            <div className="text-2xl font-bold text-gray-900">{statsLoading ? '...' : (stats?.total_products || 0).toLocaleString()}</div>
            <div className="text-sm text-gray-500">Total Products</div>
          </div>
        </div>
        <div className="card p-5">
          <div className="p-2 bg-green-100 rounded-lg w-fit"><Package className="w-5 h-5 text-green-600" /></div>
          <div className="mt-3">
            <div className="text-2xl font-bold text-gray-900">{statsLoading ? '...' : (stats?.active_products || 0).toLocaleString()}</div>
            <div className="text-sm text-gray-500">Active</div>
          </div>
        </div>
        <div className="card p-5">
          <div className="p-2 bg-purple-100 rounded-lg w-fit"><Layers className="w-5 h-5 text-purple-600" /></div>
          <div className="mt-3">
            <div className="text-2xl font-bold text-gray-900">{statsLoading ? '...' : (stats?.categories || 0)}</div>
            <div className="text-sm text-gray-500">Categories</div>
          </div>
        </div>
        <div className="card p-5">
          <div className="p-2 bg-orange-100 rounded-lg w-fit"><Store className="w-5 h-5 text-orange-600" /></div>
          <div className="mt-3">
            <div className="text-2xl font-bold text-gray-900">{statsLoading ? '...' : (stats?.vendors || 0)}</div>
            <div className="text-sm text-gray-500">Vendors</div>
          </div>
        </div>
      </div>

      {/* Tabs + Search */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="overflow-x-auto w-full sm:w-auto scrollbar-hide -mx-4 px-4 sm:mx-0 sm:px-0">
          <div className="flex space-x-1 bg-gray-100 rounded-lg p-1 w-max sm:w-auto">
            {tabs.map((tab) => (
              <button key={tab.key} onClick={() => handleTabChange(tab.key)}
                className={`px-3 sm:px-4 py-2 text-sm font-medium rounded-md transition-colors whitespace-nowrap ${activeTab === tab.key ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600 hover:text-gray-900'}`}>
                {tab.label}
              </button>
            ))}
          </div>
        </div>
        <div className="relative w-full sm:w-64">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input type="text" placeholder="Search products..." value={searchInput} onChange={(e) => setSearchInput(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500" />
        </div>
      </div>

      {/* Content */}
      <div className="card overflow-hidden">
        {loading ? (
          <div className="p-8 text-center">
            <div className="animate-spin w-8 h-8 border-4 border-emerald-500 border-t-transparent rounded-full mx-auto" />
            <p className="mt-4 text-gray-500">Loading...</p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              {activeTab === 'catalog' && (
                <table className="w-full">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Product</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">SKU</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Category</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden md:table-cell">Brand</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Price</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Stock</th>
                      <th className="px-4 py-3 text-center text-xs font-semibold text-gray-600 uppercase hidden md:table-cell">Active</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {catalog?.items?.length === 0 && renderEmpty('No products found')}
                    {catalog?.items?.map((p: any) => (
                      <tr key={p.id} onClick={() => setSelectedProduct(p)} className="hover:bg-blue-50 cursor-pointer transition-colors">
                        <td className="px-4 py-3 font-medium text-emerald-600 max-w-[200px] truncate">{p.item}</td>
                        <td className="px-4 py-3 text-gray-600 text-sm hidden sm:table-cell">{p.sku}</td>
                        <td className="px-4 py-3 text-gray-600 hidden sm:table-cell">{p.category || '-'}</td>
                        <td className="px-4 py-3 text-gray-600 hidden md:table-cell">{p.brand || '-'}</td>
                        <td className="px-4 py-3 text-right text-gray-900">{p.unit_price ? formatMoney(p.unit_price) : '-'}</td>
                        <td className="px-4 py-3 text-right text-gray-900 hidden sm:table-cell">{p.inventory_available ?? '-'}</td>
                        <td className="px-4 py-3 text-center hidden md:table-cell">
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${p.active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>{p.active ? 'Yes' : 'No'}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}

              {activeTab === 'batches' && (
                <table className="w-full">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Product</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Batch ID</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden md:table-cell">Vendor</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Status</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Qty</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">THC %</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden md:table-cell">Received</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {batches?.items?.length === 0 && renderEmpty('No batches found')}
                    {batches?.items?.map((b: any) => (
                      <tr key={b.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3">
                          <button onClick={() => { setActiveTab('catalog'); setSearchInput(b.product_name); }} className="font-medium text-emerald-600 hover:text-emerald-700 hover:underline text-left truncate max-w-[200px] block">{b.product_name}</button>
                        </td>
                        <td className="px-4 py-3 text-gray-600 text-sm hidden sm:table-cell">{b.batch_id || '-'}</td>
                        <td className="px-4 py-3 text-gray-600 hidden md:table-cell">{b.vendor_name || '-'}</td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${b.status === 'Active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>{b.status || '-'}</span>
                        </td>
                        <td className="px-4 py-3 text-right text-gray-900">{b.current_qty ?? '-'}</td>
                        <td className="px-4 py-3 text-right text-gray-600 hidden sm:table-cell">{b.total_thc_pct ? `${b.total_thc_pct}%` : '-'}</td>
                        <td className="px-4 py-3 text-gray-600 hidden md:table-cell">{b.received_date || '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}

              {activeTab === 'vendors' && (
                <table className="w-full">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Vendor</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Contact</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden md:table-cell">Phone</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden md:table-cell">Email</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Type</th>
                      <th className="px-4 py-3 text-center text-xs font-semibold text-gray-600 uppercase">Active</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {vendors?.items?.length === 0 && renderEmpty('No vendors found')}
                    {vendors?.items?.map((v: any) => (
                      <tr key={v.id} className="hover:bg-gray-50 cursor-pointer" onClick={() => { setActiveTab('by-vendor'); setSearchInput(v.vendor_name); }}>
                        <td className="px-4 py-3 font-medium text-emerald-600 hover:text-emerald-700">{v.vendor_name}</td>
                        <td className="px-4 py-3 text-gray-600 hidden sm:table-cell">{[v.contact_first_name, v.contact_last_name].filter(Boolean).join(' ') || '-'}</td>
                        <td className="px-4 py-3 text-gray-600 hidden md:table-cell">{v.phone || '-'}</td>
                        <td className="px-4 py-3 text-gray-600 hidden md:table-cell">{v.email || '-'}</td>
                        <td className="px-4 py-3 text-gray-600 hidden sm:table-cell">{v.vendor_type || '-'}</td>
                        <td className="px-4 py-3 text-center">
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${v.active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>{v.active ? 'Yes' : 'No'}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}

              {activeTab === 'by-vendor' && (
                <table className="w-full">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Vendor</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Product</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Category</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Qty Sold</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden md:table-cell">In Stock</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Sales</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {byVendor?.items?.length === 0 && renderEmpty('No products found')}
                    {byVendor?.items?.map((p: any) => (
                      <tr key={p.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 font-medium text-gray-900">{p.vendor}</td>
                        <td className="px-4 py-3">
                          <button onClick={() => { setActiveTab('catalog'); setSearchInput(p.product); }} className="text-emerald-600 hover:text-emerald-700 hover:underline text-left truncate max-w-[200px] block">{p.product}</button>
                        </td>
                        <td className="px-4 py-3 text-gray-600 hidden sm:table-cell">{p.category || '-'}</td>
                        <td className="px-4 py-3 text-right text-gray-900 hidden sm:table-cell">{p.quantity_sold ?? 0}</td>
                        <td className="px-4 py-3 text-right text-gray-900 hidden md:table-cell">{p.quantity_in_stock ?? 0}</td>
                        <td className="px-4 py-3 text-right text-gray-900">{formatMoney(p.sales || 0)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}

              {activeTab === 'expiring' && (
                <table className="w-full">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Product</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Category</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden md:table-cell">Batch ID</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Sell By</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Qty</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {expiring?.items?.length === 0 && renderEmpty('No expiring products found')}
                    {expiring?.items?.map((p: any) => {
                      const isExpired = p.sell_by_date && new Date(p.sell_by_date) < new Date()
                      return (
                        <tr key={p.id} className={`hover:bg-gray-50 ${isExpired ? 'bg-red-50' : ''}`}>
                          <td className="px-4 py-3">
                            <button onClick={() => { setActiveTab('catalog'); setSearchInput(p.product_name); }} className="font-medium text-emerald-600 hover:text-emerald-700 hover:underline text-left truncate max-w-[200px] block">
                              {isExpired && <AlertTriangle className="w-4 h-4 text-red-500 inline mr-1" />}
                              {p.product_name}
                            </button>
                          </td>
                          <td className="px-4 py-3 text-gray-600 hidden sm:table-cell">{p.product_category || '-'}</td>
                          <td className="px-4 py-3 text-gray-600 text-sm hidden md:table-cell">{p.batch_id || '-'}</td>
                          <td className="px-4 py-3 text-gray-600">{p.sell_by_date || '-'}</td>
                          <td className="px-4 py-3 text-right text-gray-900">{p.qty_remaining ?? 0}</td>
                          <td className="px-4 py-3 text-gray-600 hidden sm:table-cell">{p.status || '-'}</td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              )}
            </div>
            {renderPagination()}
          </>
        )}
      </div>
    </div>
  )
}
