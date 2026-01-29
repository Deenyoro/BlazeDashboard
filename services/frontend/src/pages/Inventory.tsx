import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell,
} from 'recharts'
import {
  Package, AlertTriangle, Truck, RefreshCw, ChevronLeft, ChevronRight, DollarSign, Layers,
  Search, Clock, ArrowLeftRight, BarChart3, ShoppingCart,
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'

function formatMoney(val: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val)
}
function formatNumber(val: number) {
  return new Intl.NumberFormat('en-US').format(val)
}

const COLORS = ['#16a34a', '#2563eb', '#dc2626', '#f59e0b', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316']

type ActiveTab = 'overview' | 'snapshots' | 'actions' | 'reconciliation' | 'received' | 'aging' | 'distribution' | 'valuation' | 'transfers' | 'sellthrough' | 'current'

export default function Inventory() {
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<ActiveTab>('overview')
  const [page, setPage] = useState(0)
  const [searchInput, setSearchInput] = useState('')
  const [search, setSearch] = useState('')
  const limit = 25

  useEffect(() => {
    const timer = setTimeout(() => setSearch(searchInput), 300)
    return () => clearTimeout(timer)
  }, [searchInput])

  const handleTabChange = (tab: ActiveTab) => {
    setActiveTab(tab)
    setPage(0)
  }

  // Summary stats
  const { data: summaryData } = useQuery({
    queryKey: ['inventory-summary'],
    queryFn: async () => { const { data } = await api.get('/reports/inventory/snapshots', { params: { limit: 1 } }); return data },
  })

  // Category breakdown
  const { data: categoryData } = useQuery({
    queryKey: ['inventory-categories'],
    queryFn: async () => {
      const { data } = await api.get('/reports/inventory/snapshots', { params: { limit: 500 } })
      const byCategory: Record<string, { count: number; value: number; quantity: number }> = {}
      data.items?.forEach((item: any) => {
        const cat = item.category || 'Other'
        if (!byCategory[cat]) byCategory[cat] = { count: 0, value: 0, quantity: 0 }
        byCategory[cat].count++
        byCategory[cat].value += item.total_value || 0
        byCategory[cat].quantity += item.quantity_on_hand || 0
      })
      return Object.entries(byCategory).map(([name, data]) => ({ name, ...data })).sort((a, b) => b.value - a.value)
    },
  })

  const { data: actionSummary } = useQuery({
    queryKey: ['inventory-action-summary'],
    queryFn: async () => {
      const { data } = await api.get('/reports/inventory/actions', { params: { limit: 1000 } })
      const byAction: Record<string, { count: number; quantity: number }> = {}
      data.items?.forEach((item: any) => {
        const action = item.action || 'Other'
        if (!byAction[action]) byAction[action] = { count: 0, quantity: 0 }
        byAction[action].count++
        byAction[action].quantity += Math.abs(item.quantity || 0)
      })
      return Object.entries(byAction).map(([name, data]) => ({ name, ...data })).sort((a, b) => b.count - a.count)
    },
  })

  // All tab queries
  const { data: snapshotsData, isLoading: snapshotsLoading } = useQuery({
    queryKey: ['inventory-snapshots-table', page, search], queryFn: async () => { const { data } = await api.get('/reports/inventory/snapshots', { params: { skip: page * limit, limit, search: search || undefined } }); return data }, enabled: activeTab === 'snapshots',
  })
  const { data: actionsData, isLoading: actionsLoading } = useQuery({
    queryKey: ['inventory-actions', page, search], queryFn: async () => { const { data } = await api.get('/reports/inventory/actions', { params: { skip: page * limit, limit, search: search || undefined } }); return data }, enabled: activeTab === 'actions',
  })
  const { data: reconData, isLoading: reconLoading } = useQuery({
    queryKey: ['inventory-reconciliation', page, search], queryFn: async () => { const { data } = await api.get('/reports/inventory/reconciliation', { params: { skip: page * limit, limit, search: search || undefined } }); return data }, enabled: activeTab === 'reconciliation',
  })
  const { data: receivedData, isLoading: receivedLoading } = useQuery({
    queryKey: ['inventory-received', page, search], queryFn: async () => { const { data } = await api.get('/reports/inventory/received', { params: { skip: page * limit, limit, search: search || undefined } }); return data }, enabled: activeTab === 'received',
  })
  const { data: agingData, isLoading: agingLoading } = useQuery({
    queryKey: ['inventory-aging', page, search], queryFn: async () => { const { data } = await api.get('/reports/inventory/aging', { params: { skip: page * limit, limit, search: search || undefined } }); return data }, enabled: activeTab === 'aging',
  })
  const { data: distData, isLoading: distLoading } = useQuery({
    queryKey: ['inventory-distribution', page, search], queryFn: async () => { const { data } = await api.get('/reports/inventory/distribution', { params: { skip: page * limit, limit, search: search || undefined } }); return data }, enabled: activeTab === 'distribution',
  })
  const { data: valData, isLoading: valLoading } = useQuery({
    queryKey: ['inventory-valuation', page, search], queryFn: async () => { const { data } = await api.get('/reports/inventory/valuation', { params: { skip: page * limit, limit, search: search || undefined } }); return data }, enabled: activeTab === 'valuation',
  })
  const { data: transferData, isLoading: transferLoading } = useQuery({
    queryKey: ['inventory-transfers', page, search], queryFn: async () => { const { data } = await api.get('/reports/inventory/transfers', { params: { skip: page * limit, limit, search: search || undefined } }); return data }, enabled: activeTab === 'transfers',
  })
  const { data: sellData, isLoading: sellLoading } = useQuery({
    queryKey: ['inventory-sellthrough', page, search], queryFn: async () => { const { data } = await api.get('/reports/inventory/sell-through', { params: { skip: page * limit, limit, search: search || undefined } }); return data }, enabled: activeTab === 'sellthrough',
  })
  const { data: currentData, isLoading: currentLoading } = useQuery({
    queryKey: ['inventory-current', page, search], queryFn: async () => { const { data } = await api.get('/reports/inventory/current', { params: { skip: page * limit, limit, search: search || undefined } }); return data }, enabled: activeTab === 'current',
  })

  const getTabData = () => {
    switch (activeTab) {
      case 'snapshots': return { data: snapshotsData, loading: snapshotsLoading }
      case 'actions': return { data: actionsData, loading: actionsLoading }
      case 'reconciliation': return { data: reconData, loading: reconLoading }
      case 'received': return { data: receivedData, loading: receivedLoading }
      case 'aging': return { data: agingData, loading: agingLoading }
      case 'distribution': return { data: distData, loading: distLoading }
      case 'valuation': return { data: valData, loading: valLoading }
      case 'transfers': return { data: transferData, loading: transferLoading }
      case 'sellthrough': return { data: sellData, loading: sellLoading }
      case 'current': return { data: currentData, loading: currentLoading }
      default: return { data: null, loading: false }
    }
  }

  const tabData = getTabData()
  const totalPages = Math.ceil((tabData.data?.total || 0) / limit)
  const totalValue = categoryData?.reduce((sum: number, c: any) => sum + c.value, 0) || 0
  const totalProducts = categoryData?.reduce((sum: number, c: any) => sum + c.count, 0) || 0

  const tabs = [
    { id: 'overview' as ActiveTab, label: 'Overview', icon: Layers },
    { id: 'current' as ActiveTab, label: 'Current', icon: Package },
    { id: 'aging' as ActiveTab, label: 'Aging', icon: Clock },
    { id: 'valuation' as ActiveTab, label: 'Valuation', icon: DollarSign },
    { id: 'distribution' as ActiveTab, label: 'Distribution', icon: BarChart3 },
    { id: 'sellthrough' as ActiveTab, label: 'Sell-Through', icon: ShoppingCart },
    { id: 'transfers' as ActiveTab, label: 'Transfers', icon: ArrowLeftRight },
    { id: 'snapshots' as ActiveTab, label: 'Snapshots', icon: Package },
    { id: 'actions' as ActiveTab, label: 'Actions', icon: RefreshCw },
    { id: 'reconciliation' as ActiveTab, label: 'Recon', icon: AlertTriangle },
    { id: 'received' as ActiveTab, label: 'Received', icon: Truck },
  ]

  const renderPagination = () => {
    if (activeTab === 'overview') return null
    return (
      <div className="px-4 py-3 border-t bg-gray-50 flex flex-col sm:flex-row items-center justify-between gap-2">
        <div className="text-sm text-gray-500">
          {(tabData.data?.total || 0) > 0
            ? `Showing ${page * limit + 1} - ${Math.min((page + 1) * limit, tabData.data?.total || 0)} of ${(tabData.data?.total || 0).toLocaleString()}`
            : 'No records'}
        </div>
        <div className="flex gap-2">
          <button onClick={() => setPage(Math.max(0, page - 1))} disabled={page === 0} className="p-2 rounded hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"><ChevronLeft className="w-5 h-5" /></button>
          <span className="px-4 py-2 text-sm">Page {page + 1} of {totalPages || 1}</span>
          <button onClick={() => setPage(page + 1)} disabled={page >= totalPages - 1} className="p-2 rounded hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"><ChevronRight className="w-5 h-5" /></button>
        </div>
      </div>
    )
  }

  const renderLoading = () => (
    <div className="p-8 text-center"><div className="animate-spin w-8 h-8 border-4 border-emerald-500 border-t-transparent rounded-full mx-auto" /></div>
  )

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Inventory</h1>
        <p className="text-gray-500">{formatNumber(summaryData?.total || 0)} snapshot records across {categoryData?.length || 0} categories</p>
      </div>

      {/* Tabs + Search */}
      <div className="flex flex-col gap-4">
        <div className="border-b border-gray-200 -mx-4 sm:mx-0">
          <nav className="flex space-x-4 sm:space-x-6 overflow-x-auto px-4 sm:px-0 scrollbar-hide">
            {tabs.map((tab) => {
              const Icon = tab.icon
              return (
                <button key={tab.id} onClick={() => handleTabChange(tab.id)}
                  className={`flex items-center gap-1.5 py-3 sm:py-4 px-1 border-b-2 font-medium text-xs sm:text-sm transition-colors whitespace-nowrap flex-shrink-0 ${
                    activeTab === tab.id ? 'border-emerald-500 text-emerald-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
                  {tab.label}
                </button>
              )
            })}
          </nav>
        </div>
        {activeTab !== 'overview' && (
          <div className="relative w-full sm:w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input type="text" placeholder="Search inventory..." value={searchInput} onChange={(e) => setSearchInput(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500" />
          </div>
        )}
      </div>

      {/* Overview */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="card p-4 sm:p-5">
              <div className="p-2 bg-green-100 rounded-lg w-fit"><DollarSign className="w-5 h-5 text-green-600" /></div>
              <div className="mt-3"><div className="text-xl sm:text-2xl font-bold text-gray-900">{formatMoney(totalValue)}</div><div className="text-xs sm:text-sm text-gray-500">Total Value</div></div>
            </div>
            <div className="card p-4 sm:p-5">
              <div className="p-2 bg-blue-100 rounded-lg w-fit"><Package className="w-5 h-5 text-blue-600" /></div>
              <div className="mt-3"><div className="text-xl sm:text-2xl font-bold text-gray-900">{formatNumber(totalProducts)}</div><div className="text-xs sm:text-sm text-gray-500">Products</div></div>
            </div>
            <div className="card p-4 sm:p-5">
              <div className="p-2 bg-purple-100 rounded-lg w-fit"><Layers className="w-5 h-5 text-purple-600" /></div>
              <div className="mt-3"><div className="text-xl sm:text-2xl font-bold text-gray-900">{categoryData?.length || 0}</div><div className="text-xs sm:text-sm text-gray-500">Categories</div></div>
            </div>
            <div className="card p-4 sm:p-5">
              <div className="p-2 bg-orange-100 rounded-lg w-fit"><RefreshCw className="w-5 h-5 text-orange-600" /></div>
              <div className="mt-3"><div className="text-xl sm:text-2xl font-bold text-gray-900">{formatNumber(actionSummary?.reduce((s: number, a: any) => s + a.count, 0) || 0)}</div><div className="text-xs sm:text-sm text-gray-500">Actions</div></div>
            </div>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="card p-5">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Value by Category</h2>
              <div className="h-72 sm:h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart><Pie data={categoryData?.slice(0, 8)} cx="50%" cy="50%" innerRadius={50} outerRadius={90} paddingAngle={2} dataKey="value" label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                    {categoryData?.slice(0, 8).map((_: any, i: number) => (<Cell key={i} fill={COLORS[i % COLORS.length]} />))}
                  </Pie><Tooltip formatter={(val: number) => formatMoney(val)} /></PieChart>
                </ResponsiveContainer>
              </div>
            </div>
            <div className="card p-5">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Inventory Actions</h2>
              <div className="h-72 sm:h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={actionSummary} layout="vertical"><CartesianGrid strokeDasharray="3 3" /><XAxis type="number" tickFormatter={(val) => formatNumber(val)} /><YAxis type="category" dataKey="name" width={90} fontSize={11} /><Tooltip formatter={(val: number) => formatNumber(val)} /><Bar dataKey="count" fill="#2563eb" name="Count" /></BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
          <div className="card overflow-hidden">
            <div className="px-5 py-4 border-b border-gray-200"><h2 className="text-lg font-semibold text-gray-900">By Category</h2></div>
            <div className="overflow-x-auto">
              <table className="w-full"><thead className="bg-gray-50 border-b"><tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Category</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Products</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Total Value</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">% of Total</th>
              </tr></thead><tbody className="divide-y">
                {categoryData?.map((cat: any, idx: number) => (
                  <tr key={cat.name} className="hover:bg-gray-50">
                    <td className="px-4 py-3"><div className="flex items-center gap-3"><div className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: COLORS[idx % COLORS.length] }} /><span className="font-medium">{cat.name}</span></div></td>
                    <td className="px-4 py-3 text-right">{formatNumber(cat.count)}</td>
                    <td className="px-4 py-3 text-right font-medium">{formatMoney(cat.value)}</td>
                    <td className="px-4 py-3 text-right text-gray-500">{totalValue > 0 ? ((cat.value / totalValue) * 100).toFixed(1) : 0}%</td>
                  </tr>
                ))}
              </tbody></table>
            </div>
          </div>
        </div>
      )}

      {/* Current Stock */}
      {activeTab === 'current' && (
        <div className="card overflow-hidden">
          {currentLoading ? renderLoading() : (<>
            <div className="overflow-x-auto"><table className="w-full"><thead className="bg-gray-50 border-b"><tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Product</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Category</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden md:table-cell">Status</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Current Qty</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Sold Qty</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">COGS</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden md:table-cell">Retail Value</th>
            </tr></thead><tbody className="divide-y">
              {currentData?.items?.length === 0 && <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-500">No data</td></tr>}
              {currentData?.items?.map((i: any) => (
                <tr key={i.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm"><button onClick={() => navigate(`/products?search=${encodeURIComponent(i.product)}&tab=catalog`)} className="font-medium text-emerald-600 hover:text-emerald-700 hover:underline text-left">{i.product}</button></td>
                  <td className="px-4 py-3 text-sm text-gray-600 hidden sm:table-cell">{i.category}</td>
                  <td className="px-4 py-3 text-sm hidden md:table-cell"><span className={`px-2 py-1 rounded-full text-xs ${i.status === 'Active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>{i.status}</span></td>
                  <td className="px-4 py-3 text-sm text-right font-medium">{(i.current_quantity || 0).toFixed(1)}</td>
                  <td className="px-4 py-3 text-sm text-right text-gray-600 hidden sm:table-cell">{(i.sold_quantity || 0).toFixed(1)}</td>
                  <td className="px-4 py-3 text-sm text-right">{formatMoney(i.current_cogs || 0)}</td>
                  <td className="px-4 py-3 text-sm text-right font-medium hidden md:table-cell">{formatMoney(i.retail_value || 0)}</td>
                </tr>
              ))}
            </tbody></table></div>
            {renderPagination()}
          </>)}
        </div>
      )}

      {/* Aging */}
      {activeTab === 'aging' && (
        <div className="card overflow-hidden">
          {agingLoading ? renderLoading() : (<>
            <div className="overflow-x-auto"><table className="w-full"><thead className="bg-gray-50 border-b"><tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Product</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Category</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">0-30d</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">31-45d</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">46-60d</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden md:table-cell">61-90d</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">90+d</th>
            </tr></thead><tbody className="divide-y">
              {agingData?.items?.length === 0 && <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-500">No data</td></tr>}
              {agingData?.items?.map((i: any) => (
                <tr key={i.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm"><button onClick={() => navigate(`/products?search=${encodeURIComponent(i.product_name)}&tab=catalog`)} className="font-medium text-emerald-600 hover:text-emerald-700 hover:underline text-left">{i.product_name}</button></td>
                  <td className="px-4 py-3 text-sm text-gray-600 hidden sm:table-cell">{i.product_category}</td>
                  <td className="px-4 py-3 text-sm text-right">{(i.days_0_30_qty || 0).toFixed(1)}</td>
                  <td className="px-4 py-3 text-sm text-right">{(i.days_31_45_qty || 0).toFixed(1)}</td>
                  <td className="px-4 py-3 text-sm text-right hidden sm:table-cell">{(i.days_46_60_qty || 0).toFixed(1)}</td>
                  <td className="px-4 py-3 text-sm text-right hidden md:table-cell">{(i.days_61_90_qty || 0).toFixed(1)}</td>
                  <td className={`px-4 py-3 text-sm text-right font-medium ${(i.days_90_plus_qty || 0) > 0 ? 'text-red-600' : ''}`}>{(i.days_90_plus_qty || 0).toFixed(1)}</td>
                </tr>
              ))}
            </tbody></table></div>
            {renderPagination()}
          </>)}
        </div>
      )}

      {/* Valuation */}
      {activeTab === 'valuation' && (
        <div className="card overflow-hidden">
          {valLoading ? renderLoading() : (<>
            <div className="overflow-x-auto"><table className="w-full"><thead className="bg-gray-50 border-b"><tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Product</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Category</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Avg Cost</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Avg Retail</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Margin</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Qty</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden md:table-cell">Total COGS</th>
            </tr></thead><tbody className="divide-y">
              {valData?.items?.length === 0 && <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-500">No data</td></tr>}
              {valData?.items?.map((i: any) => (
                <tr key={i.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm"><button onClick={() => navigate(`/products?search=${encodeURIComponent(i.product_name)}&tab=catalog`)} className="font-medium text-emerald-600 hover:text-emerald-700 hover:underline text-left">{i.product_name}</button></td>
                  <td className="px-4 py-3 text-sm text-gray-600 hidden sm:table-cell">{i.category}</td>
                  <td className="px-4 py-3 text-sm text-right">{formatMoney(i.avg_unit_cost || 0)}</td>
                  <td className="px-4 py-3 text-sm text-right">{formatMoney(i.avg_retail_price || 0)}</td>
                  <td className={`px-4 py-3 text-sm text-right font-medium hidden sm:table-cell ${(i.avg_margin_pct || 0) > 50 ? 'text-green-600' : (i.avg_margin_pct || 0) > 20 ? 'text-gray-900' : 'text-red-600'}`}>{(i.avg_margin_pct || 0).toFixed(1)}%</td>
                  <td className="px-4 py-3 text-sm text-right">{(i.total_available_qty || 0).toFixed(1)}</td>
                  <td className="px-4 py-3 text-sm text-right hidden md:table-cell">{formatMoney(i.total_available_cogs || 0)}</td>
                </tr>
              ))}
            </tbody></table></div>
            {renderPagination()}
          </>)}
        </div>
      )}

      {/* Distribution */}
      {activeTab === 'distribution' && (
        <div className="card overflow-hidden">
          {distLoading ? renderLoading() : (<>
            <div className="overflow-x-auto"><table className="w-full"><thead className="bg-gray-50 border-b"><tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Product</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Category</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Total</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Exchange</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden md:table-cell">Fulfillment</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden md:table-cell">Safe</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden lg:table-cell">Vault</th>
            </tr></thead><tbody className="divide-y">
              {distData?.items?.length === 0 && <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-500">No data</td></tr>}
              {distData?.items?.map((i: any) => (
                <tr key={i.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm"><button onClick={() => navigate(`/products?search=${encodeURIComponent(i.product)}&tab=catalog`)} className="font-medium text-emerald-600 hover:text-emerald-700 hover:underline text-left">{i.product}</button></td>
                  <td className="px-4 py-3 text-sm text-gray-600 hidden sm:table-cell">{i.category}</td>
                  <td className="px-4 py-3 text-sm text-right font-medium">{(i.total || 0).toFixed(1)}</td>
                  <td className="px-4 py-3 text-sm text-right hidden sm:table-cell">{(i.exchange || 0).toFixed(1)}</td>
                  <td className="px-4 py-3 text-sm text-right hidden md:table-cell">{(i.fulfillment || 0).toFixed(1)}</td>
                  <td className="px-4 py-3 text-sm text-right hidden md:table-cell">{(i.safe || 0).toFixed(1)}</td>
                  <td className="px-4 py-3 text-sm text-right hidden lg:table-cell">{(i.vault || 0).toFixed(1)}</td>
                </tr>
              ))}
            </tbody></table></div>
            {renderPagination()}
          </>)}
        </div>
      )}

      {/* Sell-Through */}
      {activeTab === 'sellthrough' && (
        <div className="card overflow-hidden">
          {sellLoading ? renderLoading() : (<>
            <div className="overflow-x-auto"><table className="w-full"><thead className="bg-gray-50 border-b"><tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Product</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Category</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Avg Sold/Day</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Days Left</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">On Hand</th>
            </tr></thead><tbody className="divide-y">
              {sellData?.items?.length === 0 && <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-500">No data</td></tr>}
              {sellData?.items?.map((i: any) => (
                <tr key={i.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm"><button onClick={() => navigate(`/products?search=${encodeURIComponent(i.product_name)}&tab=catalog`)} className="font-medium text-emerald-600 hover:text-emerald-700 hover:underline text-left">{i.product_name}</button></td>
                  <td className="px-4 py-3 text-sm text-gray-600 hidden sm:table-cell">{i.category}</td>
                  <td className="px-4 py-3 text-sm text-right">{(i.avg_qty_sold_per_day || 0).toFixed(2)}</td>
                  <td className={`px-4 py-3 text-sm text-right font-medium ${(i.days_remaining || 0) < 7 ? 'text-red-600' : (i.days_remaining || 0) < 30 ? 'text-orange-600' : 'text-green-600'}`}>{(i.days_remaining || 0).toFixed(0)}</td>
                  <td className="px-4 py-3 text-sm text-right">{(i.qty_on_hand || 0).toFixed(1)}</td>
                </tr>
              ))}
            </tbody></table></div>
            {renderPagination()}
          </>)}
        </div>
      )}

      {/* Transfers */}
      {activeTab === 'transfers' && (
        <div className="card overflow-hidden">
          {transferLoading ? renderLoading() : (<>
            <div className="overflow-x-auto"><table className="w-full"><thead className="bg-gray-50 border-b"><tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Date</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Product</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Employee</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden md:table-cell">Origin</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden md:table-cell">Destination</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Amount</th>
            </tr></thead><tbody className="divide-y">
              {transferData?.items?.length === 0 && <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-500">No data</td></tr>}
              {transferData?.items?.map((i: any) => (
                <tr key={i.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm text-gray-600">{i.date}</td>
                  <td className="px-4 py-3 text-sm"><button onClick={() => navigate(`/products?search=${encodeURIComponent(i.product)}&tab=catalog`)} className="font-medium text-emerald-600 hover:text-emerald-700 hover:underline text-left">{i.product}</button></td>
                  <td className="px-4 py-3 text-sm text-gray-600 hidden sm:table-cell">{i.employee}</td>
                  <td className="px-4 py-3 text-sm text-gray-600 hidden md:table-cell">{i.origin_inventory || i.origin_shop}</td>
                  <td className="px-4 py-3 text-sm text-gray-600 hidden md:table-cell">{i.destination || i.destination_shop}</td>
                  <td className="px-4 py-3 text-sm text-right font-medium">{(i.amount || 0).toFixed(1)}</td>
                </tr>
              ))}
            </tbody></table></div>
            {renderPagination()}
          </>)}
        </div>
      )}

      {/* Snapshots */}
      {activeTab === 'snapshots' && (
        <div className="card overflow-hidden">
          {snapshotsLoading ? renderLoading() : (<>
            <div className="overflow-x-auto"><table className="w-full"><thead className="bg-gray-50 border-b"><tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden md:table-cell">Date</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Product</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Category</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">On Hand</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Available</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden md:table-cell">Unit Cost</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Value</th>
            </tr></thead><tbody className="divide-y">
              {snapshotsData?.items?.length === 0 && <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-500">No data</td></tr>}
              {snapshotsData?.items?.map((i: any) => (
                <tr key={i.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm hidden md:table-cell">{i.snapshot_date}</td>
                  <td className="px-4 py-3 text-sm"><button onClick={() => navigate(`/products?search=${encodeURIComponent(i.product_name)}&tab=catalog`)} className="font-medium text-emerald-600 hover:text-emerald-700 hover:underline text-left">{i.product_name}</button></td>
                  <td className="px-4 py-3 text-sm text-gray-600 hidden sm:table-cell">{i.category}</td>
                  <td className="px-4 py-3 text-sm text-right">{i.quantity_on_hand?.toFixed(2)}</td>
                  <td className="px-4 py-3 text-sm text-right hidden sm:table-cell">{i.quantity_available?.toFixed(2)}</td>
                  <td className="px-4 py-3 text-sm text-right hidden md:table-cell">{formatMoney(i.unit_cost || 0)}</td>
                  <td className="px-4 py-3 text-sm text-right font-medium">{formatMoney(i.total_value || 0)}</td>
                </tr>
              ))}
            </tbody></table></div>
            {renderPagination()}
          </>)}
        </div>
      )}

      {/* Actions */}
      {activeTab === 'actions' && (
        <div className="card overflow-hidden">
          {actionsLoading ? renderLoading() : (<>
            <div className="overflow-x-auto"><table className="w-full"><thead className="bg-gray-50 border-b"><tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Date</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Action</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Product</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Category</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Qty</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Value</th>
            </tr></thead><tbody className="divide-y">
              {actionsData?.items?.length === 0 && <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-500">No data</td></tr>}
              {actionsData?.items?.map((i: any) => (
                <tr key={i.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm">{i.date}</td>
                  <td className="px-4 py-3 text-sm"><span className={`px-2 py-1 rounded-full text-xs font-medium ${i.action === 'Sale' ? 'bg-green-100 text-green-700' : i.action === 'Refund' ? 'bg-red-100 text-red-700' : i.action === 'AddBatch' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-700'}`}>{i.action}</span></td>
                  <td className="px-4 py-3 text-sm"><button onClick={() => navigate(`/products?search=${encodeURIComponent(i.product)}&tab=catalog`)} className="font-medium text-emerald-600 hover:text-emerald-700 hover:underline text-left">{i.product}</button></td>
                  <td className="px-4 py-3 text-sm text-gray-600 hidden sm:table-cell">{i.category}</td>
                  <td className={`px-4 py-3 text-sm text-right font-medium ${(i.quantity || 0) < 0 ? 'text-red-600' : 'text-green-600'}`}>{i.quantity?.toFixed(2)}</td>
                  <td className="px-4 py-3 text-sm text-right hidden sm:table-cell">{formatMoney(i.inventory_value || 0)}</td>
                </tr>
              ))}
            </tbody></table></div>
            {renderPagination()}
          </>)}
        </div>
      )}

      {/* Reconciliation */}
      {activeTab === 'reconciliation' && (
        <div className="card overflow-hidden">
          {reconLoading ? renderLoading() : (<>
            <div className="overflow-x-auto"><table className="w-full"><thead className="bg-gray-50 border-b"><tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Date</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Product</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Employee</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Old</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">New</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Diff</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden md:table-cell">Reason</th>
            </tr></thead><tbody className="divide-y">
              {reconData?.items?.length === 0 && <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-500">No data</td></tr>}
              {reconData?.items?.map((i: any) => (
                <tr key={i.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm">{i.date}</td>
                  <td className="px-4 py-3 text-sm"><button onClick={() => navigate(`/products?search=${encodeURIComponent(i.product_name)}&tab=catalog`)} className="font-medium text-emerald-600 hover:text-emerald-700 hover:underline text-left">{i.product_name}</button></td>
                  <td className="px-4 py-3 text-sm text-gray-500 hidden sm:table-cell">{i.employee_name}</td>
                  <td className="px-4 py-3 text-sm text-right">{i.old_quantity?.toFixed(2)}</td>
                  <td className="px-4 py-3 text-sm text-right">{i.new_quantity?.toFixed(2)}</td>
                  <td className={`px-4 py-3 text-sm text-right font-medium ${(i.difference || 0) < 0 ? 'text-red-600' : (i.difference || 0) > 0 ? 'text-green-600' : ''}`}>{i.difference?.toFixed(2)}</td>
                  <td className="px-4 py-3 text-sm text-gray-500 hidden md:table-cell">{i.reason || '-'}</td>
                </tr>
              ))}
            </tbody></table></div>
            {renderPagination()}
          </>)}
        </div>
      )}

      {/* Received */}
      {activeTab === 'received' && (
        <div className="card overflow-hidden">
          {receivedLoading ? renderLoading() : (<>
            <div className="overflow-x-auto"><table className="w-full"><thead className="bg-gray-50 border-b"><tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Date</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">PO #</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden md:table-cell">Vendor</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Product</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Qty</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Unit Cost</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Total</th>
            </tr></thead><tbody className="divide-y">
              {receivedData?.items?.length === 0 && <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-500">No data</td></tr>}
              {receivedData?.items?.map((i: any) => (
                <tr key={i.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm">{i.date}</td>
                  <td className="px-4 py-3 text-sm font-medium hidden sm:table-cell">{i.po_number}</td>
                  <td className="px-4 py-3 text-sm hidden md:table-cell">{i.vendor}</td>
                  <td className="px-4 py-3 text-sm"><button onClick={() => navigate(`/products?search=${encodeURIComponent(i.product)}&tab=catalog`)} className="font-medium text-emerald-600 hover:text-emerald-700 hover:underline text-left">{i.product}</button></td>
                  <td className="px-4 py-3 text-sm text-right">{i.received_quantity?.toFixed(2)}</td>
                  <td className="px-4 py-3 text-sm text-right hidden sm:table-cell">{formatMoney(i.unit_cost || 0)}</td>
                  <td className="px-4 py-3 text-sm text-right font-medium">{formatMoney(i.grand_total || 0)}</td>
                </tr>
              ))}
            </tbody></table></div>
            {renderPagination()}
          </>)}
        </div>
      )}
    </div>
  )
}
