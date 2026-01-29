import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { format } from 'date-fns'
import {
  Package,
  CreditCard,
  Calculator,
  Tag,
  RotateCcw,
  XCircle,
  Truck,
  Gift,
  TrendingUp,
  MapPin,
  Clock,
  ShoppingBag,
  Layers,
  Store,
  Users,
  Search,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { api } from '../api/client'

function formatMoney(val: number) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(val)
}

type ReportTab =
  | 'inventory' | 'payments' | 'accounting' | 'discounts' | 'refunds' | 'canceled'
  | 'delivery' | 'promotions' | 'profitloss'
  | 'bycity' | 'byhour' | 'byproduct' | 'bycategory' | 'byvendor' | 'byconsumer'

const tabGroups = [
  {
    label: 'General',
    tabs: [
      { id: 'inventory' as ReportTab, label: 'Inventory', icon: Package },
      { id: 'payments' as ReportTab, label: 'Payments', icon: CreditCard },
      { id: 'accounting' as ReportTab, label: 'Accounting', icon: Calculator },
      { id: 'discounts' as ReportTab, label: 'Discounts', icon: Tag },
      { id: 'refunds' as ReportTab, label: 'Refunds', icon: RotateCcw },
      { id: 'canceled' as ReportTab, label: 'Canceled/Void', icon: XCircle },
    ],
  },
  {
    label: 'Sales & Financial',
    tabs: [
      { id: 'delivery' as ReportTab, label: 'Delivery Sales', icon: Truck },
      { id: 'promotions' as ReportTab, label: 'Promotions', icon: Gift },
      { id: 'profitloss' as ReportTab, label: 'Profit & Loss', icon: TrendingUp },
    ],
  },
  {
    label: 'Sales Breakdowns',
    tabs: [
      { id: 'bycity' as ReportTab, label: 'By City', icon: MapPin },
      { id: 'byhour' as ReportTab, label: 'By Hour', icon: Clock },
      { id: 'byproduct' as ReportTab, label: 'By Product', icon: ShoppingBag },
      { id: 'bycategory' as ReportTab, label: 'By Category', icon: Layers },
      { id: 'byvendor' as ReportTab, label: 'By Vendor', icon: Store },
      { id: 'byconsumer' as ReportTab, label: 'By Consumer Type', icon: Users },
    ],
  },
]

export default function Reports() {
  const navigate = useNavigate()
  const [urlParams, setUrlParams] = useSearchParams()
  const [activeTab, setActiveTab] = useState<ReportTab>('inventory')
  const [page, setPage] = useState(0)
  const [searchInput, setSearchInput] = useState('')
  const [search, setSearch] = useState('')
  const limit = 25

  // Read URL params on mount
  useEffect(() => {
    const tabParam = urlParams.get('tab')
    const searchParam = urlParams.get('search')
    if (tabParam) {
      const allTabIds = tabGroups.flatMap(g => g.tabs.map(t => t.id))
      if (allTabIds.includes(tabParam as ReportTab)) {
        setActiveTab(tabParam as ReportTab)
      }
    }
    if (searchParam) {
      setSearchInput(searchParam)
      setSearch(searchParam)
    }
    if (tabParam || searchParam) {
      setUrlParams({})
    }
  }, [])

  useEffect(() => {
    const timer = setTimeout(() => setSearch(searchInput), 300)
    return () => clearTimeout(timer)
  }, [searchInput])

  const handleTabChange = (tab: ReportTab) => {
    setActiveTab(tab)
    setPage(0)
  }

  // Determine which tabs support search
  const searchableTabs: ReportTab[] = ['inventory', 'payments', 'accounting', 'discounts', 'refunds', 'canceled', 'delivery', 'promotions', 'byproduct']

  // --- Queries ---

  const { data: inventoryData, isLoading: inventoryLoading } = useQuery({
    queryKey: ['rpt-inventory', page, search],
    queryFn: async () => {
      const { data } = await api.get('/reports/inventory/snapshots', { params: { skip: page * limit, limit } })
      return data
    },
    enabled: activeTab === 'inventory',
  })

  const { data: paymentsData, isLoading: paymentsLoading } = useQuery({
    queryKey: ['rpt-payments', page],
    queryFn: async () => {
      const { data } = await api.get('/reports/payments/integrated', { params: { skip: page * limit, limit } })
      return data
    },
    enabled: activeTab === 'payments',
  })

  const { data: accountingData, isLoading: accountingLoading } = useQuery({
    queryKey: ['rpt-accounting', page],
    queryFn: async () => {
      const { data } = await api.get('/reports/accounting/daily', { params: { skip: page * limit, limit } })
      return data
    },
    enabled: activeTab === 'accounting',
  })

  const { data: discountsData, isLoading: discountsLoading } = useQuery({
    queryKey: ['rpt-discounts', page],
    queryFn: async () => {
      const { data } = await api.get('/reports/discounts', { params: { skip: page * limit, limit } })
      return data
    },
    enabled: activeTab === 'discounts',
  })

  const { data: refundsData, isLoading: refundsLoading } = useQuery({
    queryKey: ['rpt-refunds', page],
    queryFn: async () => {
      const { data } = await api.get('/reports/refunds', { params: { skip: page * limit, limit } })
      return data
    },
    enabled: activeTab === 'refunds',
  })

  const { data: canceledData, isLoading: canceledLoading } = useQuery({
    queryKey: ['rpt-canceled', page],
    queryFn: async () => {
      const { data } = await api.get('/reports/canceled-void', { params: { skip: page * limit, limit } })
      return data
    },
    enabled: activeTab === 'canceled',
  })

  const { data: deliveryData, isLoading: deliveryLoading } = useQuery({
    queryKey: ['rpt-delivery', page],
    queryFn: async () => {
      const { data } = await api.get('/reports/delivery-sales', { params: { skip: page * limit, limit } })
      return data
    },
    enabled: activeTab === 'delivery',
  })

  const { data: promoData, isLoading: promoLoading } = useQuery({
    queryKey: ['rpt-promotions', page],
    queryFn: async () => {
      const { data } = await api.get('/reports/promotions', { params: { skip: page * limit, limit } })
      return data
    },
    enabled: activeTab === 'promotions',
  })

  const { data: plData, isLoading: plLoading } = useQuery({
    queryKey: ['rpt-profitloss', page],
    queryFn: async () => {
      const { data } = await api.get('/reports/profit-loss', { params: { skip: page * limit, limit } })
      return data
    },
    enabled: activeTab === 'profitloss',
  })

  const { data: cityData, isLoading: cityLoading } = useQuery({
    queryKey: ['rpt-bycity'],
    queryFn: async () => {
      const { data } = await api.get('/reports/sales/by-city')
      return data
    },
    enabled: activeTab === 'bycity',
  })

  const { data: hourData, isLoading: hourLoading } = useQuery({
    queryKey: ['rpt-byhour'],
    queryFn: async () => {
      const { data } = await api.get('/reports/sales/by-hour')
      return data
    },
    enabled: activeTab === 'byhour',
  })

  const { data: productData, isLoading: productLoading } = useQuery({
    queryKey: ['rpt-byproduct', page, search],
    queryFn: async () => {
      const { data } = await api.get('/reports/sales/by-product', { params: { skip: page * limit, limit, search: search || undefined } })
      return data
    },
    enabled: activeTab === 'byproduct',
  })

  const { data: categoryData, isLoading: categoryLoading } = useQuery({
    queryKey: ['rpt-bycategory'],
    queryFn: async () => {
      const { data } = await api.get('/reports/sales/by-product-category')
      return data
    },
    enabled: activeTab === 'bycategory',
  })

  const { data: vendorData, isLoading: vendorLoading } = useQuery({
    queryKey: ['rpt-byvendor'],
    queryFn: async () => {
      const { data } = await api.get('/reports/sales/by-vendor')
      return data
    },
    enabled: activeTab === 'byvendor',
  })

  const { data: consumerData, isLoading: consumerLoading } = useQuery({
    queryKey: ['rpt-byconsumer'],
    queryFn: async () => {
      const { data } = await api.get('/reports/sales/by-consumer-type')
      return data
    },
    enabled: activeTab === 'byconsumer',
  })

  // --- Data helpers ---

  const getCurrentData = () => {
    const map: Record<ReportTab, { data: any; loading: boolean }> = {
      inventory: { data: inventoryData, loading: inventoryLoading },
      payments: { data: paymentsData, loading: paymentsLoading },
      accounting: { data: accountingData, loading: accountingLoading },
      discounts: { data: discountsData, loading: discountsLoading },
      refunds: { data: refundsData, loading: refundsLoading },
      canceled: { data: canceledData, loading: canceledLoading },
      delivery: { data: deliveryData, loading: deliveryLoading },
      promotions: { data: promoData, loading: promoLoading },
      profitloss: { data: plData, loading: plLoading },
      bycity: { data: cityData, loading: cityLoading },
      byhour: { data: hourData, loading: hourLoading },
      byproduct: { data: productData, loading: productLoading },
      bycategory: { data: categoryData, loading: categoryLoading },
      byvendor: { data: vendorData, loading: vendorLoading },
      byconsumer: { data: consumerData, loading: consumerLoading },
    }
    return map[activeTab]
  }

  const { data: currentData, loading } = getCurrentData()
  const totalPages = Math.ceil((currentData?.total || 0) / limit)

  // Non-paginated tabs (API returns all rows)
  const nonPaginated: ReportTab[] = ['bycity', 'byhour', 'bycategory', 'byvendor', 'byconsumer']
  const showPagination = !nonPaginated.includes(activeTab)

  const renderLoading = () => (
    <div className="p-8 text-center">
      <div className="animate-spin w-8 h-8 border-4 border-emerald-500 border-t-transparent rounded-full mx-auto" />
      <p className="mt-4 text-gray-500">Loading...</p>
    </div>
  )

  const renderEmpty = (msg: string) => (
    <tr><td colSpan={20} className="px-4 py-8 text-center text-gray-500">{msg}</td></tr>
  )

  const renderPagination = () => {
    if (!showPagination) {
      return (
        <div className="px-4 py-3 border-t bg-gray-50 text-sm text-gray-500">
          {(currentData?.total || 0).toLocaleString()} records
        </div>
      )
    }
    return (
      <div className="px-4 py-3 border-t bg-gray-50 flex flex-col sm:flex-row items-center justify-between gap-2">
        <div className="text-sm text-gray-500">
          {(currentData?.total || 0) > 0
            ? `Showing ${page * limit + 1} - ${Math.min((page + 1) * limit, currentData?.total || 0)} of ${(currentData?.total || 0).toLocaleString()}`
            : 'No records'}
        </div>
        <div className="flex gap-2">
          <button onClick={() => setPage(Math.max(0, page - 1))} disabled={page === 0} className="p-2 rounded hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed">
            <ChevronLeft className="w-5 h-5" />
          </button>
          <span className="px-4 py-2 text-sm">Page {page + 1} of {totalPages || 1}</span>
          <button onClick={() => setPage(page + 1)} disabled={page >= totalPages - 1} className="p-2 rounded hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed">
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Reports</h1>
          <p className="text-gray-500">Sales breakdowns, financials, inventory, and more</p>
        </div>
        {searchableTabs.includes(activeTab) && (
          <div className="relative w-full sm:w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search reports..."
              value={searchInput}
              onChange={(e) => { setSearchInput(e.target.value); setPage(0) }}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
        )}
      </div>

      {/* Tab Groups */}
      {tabGroups.map((group) => (
        <div key={group.label}>
          <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1 px-1">{group.label}</div>
          <div className="overflow-x-auto scrollbar-hide -mx-4 px-4 sm:mx-0 sm:px-0">
            <div className="flex space-x-1 w-max">
              {group.tabs.map((tab) => {
                const Icon = tab.icon
                const isActive = activeTab === tab.id
                return (
                  <button
                    key={tab.id}
                    onClick={() => handleTabChange(tab.id)}
                    className={`flex items-center gap-1.5 px-3 py-2 text-xs sm:text-sm font-medium rounded-lg transition-colors whitespace-nowrap ${
                      isActive
                        ? 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200'
                        : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                    }`}
                  >
                    <Icon className="w-3.5 h-3.5" />
                    {tab.label}
                  </button>
                )
              })}
            </div>
          </div>
        </div>
      ))}

      {/* Content */}
      <div className="card overflow-hidden">
        {loading ? renderLoading() : (
          <>
            <div className="overflow-x-auto">
              {/* Inventory Tab */}
              {activeTab === 'inventory' && (
                <table className="w-full">
                  <thead className="bg-gray-50 border-b">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Date</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Product</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">SKU</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden md:table-cell">Category</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">On Hand</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Available</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden md:table-cell">Unit Cost</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Total Value</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {inventoryData?.items?.length === 0 && renderEmpty('No inventory data found')}
                    {inventoryData?.items?.map((item: any) => (
                      <tr key={item.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm">{item.snapshot_date}</td>
                        <td className="px-4 py-3 text-sm"><button onClick={() => navigate(`/products?search=${encodeURIComponent(item.product_name)}&tab=catalog`)} className="font-medium text-emerald-600 hover:text-emerald-700 hover:underline text-left">{item.product_name}</button></td>
                        <td className="px-4 py-3 text-sm text-gray-500 hidden sm:table-cell">{item.sku}</td>
                        <td className="px-4 py-3 text-sm hidden md:table-cell">{item.category}</td>
                        <td className="px-4 py-3 text-sm text-right">{item.quantity_on_hand?.toFixed(2)}</td>
                        <td className="px-4 py-3 text-sm text-right hidden sm:table-cell">{item.quantity_available?.toFixed(2)}</td>
                        <td className="px-4 py-3 text-sm text-right hidden md:table-cell">{formatMoney(item.unit_cost || 0)}</td>
                        <td className="px-4 py-3 text-sm text-right font-medium">{formatMoney(item.total_value || 0)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}

              {/* Payments Tab */}
              {activeTab === 'payments' && (
                <table className="w-full">
                  <thead className="bg-gray-50 border-b">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Date</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Service</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Trans #</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden md:table-cell">Customer</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Status</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Due</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Paid</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden md:table-cell">Tip</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden md:table-cell">Fee</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {paymentsData?.items?.length === 0 && renderEmpty('No payment records found')}
                    {paymentsData?.items?.map((item: any) => (
                      <tr key={item.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm">{item.transaction_completion_date}</td>
                        <td className="px-4 py-3 text-sm font-medium">{item.payment_service_name}</td>
                        <td className="px-4 py-3 text-sm hidden sm:table-cell">{item.transaction_number}</td>
                        <td className="px-4 py-3 text-sm hidden md:table-cell">{item.customer}</td>
                        <td className="px-4 py-3 text-sm">
                          <span className={`px-2 py-1 rounded-full text-xs ${item.transaction_status === 'Completed' ? 'bg-green-100 text-green-700' : 'bg-gray-100'}`}>
                            {item.transaction_status}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm text-right hidden sm:table-cell">{formatMoney(item.total_due || 0)}</td>
                        <td className="px-4 py-3 text-sm text-right font-medium">{formatMoney(item.paid_amount || 0)}</td>
                        <td className="px-4 py-3 text-sm text-right text-green-600 hidden md:table-cell">{formatMoney(item.tip || 0)}</td>
                        <td className="px-4 py-3 text-sm text-right text-gray-500 hidden md:table-cell">{formatMoney(item.payment_fee || 0)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}

              {/* Accounting Tab */}
              {activeTab === 'accounting' && (
                <table className="w-full">
                  <thead className="bg-gray-50 border-b">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Date</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden md:table-cell">Shop</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Trans</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Gross</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Net</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Tax</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden md:table-cell">Discounts</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden md:table-cell">Tips</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden lg:table-cell">COGS</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {accountingData?.items?.length === 0 && renderEmpty('No accounting records found')}
                    {accountingData?.items?.map((item: any) => (
                      <tr key={item.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm font-medium">{item.date}</td>
                        <td className="px-4 py-3 text-sm hidden md:table-cell">{item.shop}</td>
                        <td className="px-4 py-3 text-sm text-right hidden sm:table-cell">{item.num_transactions}</td>
                        <td className="px-4 py-3 text-sm text-right">{formatMoney(item.gross_sales || 0)}</td>
                        <td className="px-4 py-3 text-sm text-right font-medium">{formatMoney(item.net_sales || 0)}</td>
                        <td className="px-4 py-3 text-sm text-right hidden sm:table-cell">{formatMoney(item.total_tax || 0)}</td>
                        <td className="px-4 py-3 text-sm text-right text-orange-600 hidden md:table-cell">{formatMoney(item.pre_tax_discount || 0)}</td>
                        <td className="px-4 py-3 text-sm text-right text-green-600 hidden md:table-cell">{formatMoney(item.total_tips || 0)}</td>
                        <td className="px-4 py-3 text-sm text-right text-gray-500 hidden lg:table-cell">{formatMoney(item.total_cogs || 0)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}

              {/* Discounts Tab */}
              {activeTab === 'discounts' && (
                <table className="w-full">
                  <thead className="bg-gray-50 border-b">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Date</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Name</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Type</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden md:table-cell">Applied To</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden md:table-cell">Applied By</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Amount</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Percent</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {discountsData?.items?.length === 0 && renderEmpty('No discount records found')}
                    {discountsData?.items?.map((item: any) => (
                      <tr key={item.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm">{item.usage_date ? format(new Date(item.usage_date), 'MM/dd/yyyy') : ''}</td>
                        <td className="px-4 py-3 text-sm font-medium">{item.discount_name}</td>
                        <td className="px-4 py-3 text-sm hidden sm:table-cell">
                          <span className="px-2 py-1 rounded-full text-xs bg-purple-100 text-purple-700">{item.discount_type}</span>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-500 hidden md:table-cell">{item.applied_to_product || '-'}</td>
                        <td className="px-4 py-3 text-sm hidden md:table-cell">{item.applied_by}</td>
                        <td className="px-4 py-3 text-sm text-right text-orange-600">{formatMoney(item.discount_amount || 0)}</td>
                        <td className="px-4 py-3 text-sm text-right hidden sm:table-cell">{item.discount_percent ? `${item.discount_percent}%` : '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}

              {/* Refunds Tab */}
              {activeTab === 'refunds' && (
                <table className="w-full">
                  <thead className="bg-gray-50 border-b">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Date</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Trans #</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Employee</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden md:table-cell">Customer</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Product</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Refund As</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden md:table-cell">Qty</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Amount</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {refundsData?.items?.length === 0 && renderEmpty('No refund records found')}
                    {refundsData?.items?.map((item: any) => (
                      <tr key={item.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm">{item.date}</td>
                        <td className="px-4 py-3 text-sm font-medium">{item.trans_no}</td>
                        <td className="px-4 py-3 text-sm hidden sm:table-cell">{item.employee}</td>
                        <td className="px-4 py-3 text-sm hidden md:table-cell">{item.customer}</td>
                        <td className="px-4 py-3 text-sm text-gray-500 hidden sm:table-cell">{item.product}</td>
                        <td className="px-4 py-3 text-sm">
                          <span className="px-2 py-1 rounded-full text-xs bg-red-100 text-red-700">{item.refund_as}</span>
                        </td>
                        <td className="px-4 py-3 text-sm text-right hidden md:table-cell">{item.quantity}</td>
                        <td className="px-4 py-3 text-sm text-right font-medium text-red-600">{formatMoney(item.refund_amount || 0)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}

              {/* Canceled/Void Tab */}
              {activeTab === 'canceled' && (
                <table className="w-full">
                  <thead className="bg-gray-50 border-b">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Date</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Trans #</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Member</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Status</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Reason</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden md:table-cell">Employee</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Gross</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {canceledData?.items?.length === 0 && renderEmpty('No canceled/void transactions found')}
                    {canceledData?.items?.map((item: any) => (
                      <tr key={item.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm">{item.date}</td>
                        <td className="px-4 py-3 text-sm font-medium">{item.transaction_no || '-'}</td>
                        <td className="px-4 py-3 text-sm hidden sm:table-cell">{item.member || '-'}</td>
                        <td className="px-4 py-3 text-sm">
                          <span className="px-2 py-1 rounded-full text-xs bg-red-100 text-red-700">{item.trans_status || 'Canceled'}</span>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-500 hidden sm:table-cell">{item.cancellation_reason || '-'}</td>
                        <td className="px-4 py-3 text-sm hidden md:table-cell">{item.employee || '-'}</td>
                        <td className="px-4 py-3 text-sm text-right font-medium text-red-600">{formatMoney(item.gross_receipt || 0)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}

              {/* Delivery Sales Tab */}
              {activeTab === 'delivery' && (
                <table className="w-full">
                  <thead className="bg-gray-50 border-b">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Date</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Trans ID</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Customer</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">City</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden md:table-cell">Employee</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Sales</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Gross</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {deliveryData?.items?.length === 0 && renderEmpty('No delivery sales found')}
                    {deliveryData?.items?.map((item: any) => (
                      <tr key={item.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm">{item.date}</td>
                        <td className="px-4 py-3 text-sm font-medium">{item.transaction_id || '-'}</td>
                        <td className="px-4 py-3 text-sm">{[item.customer_first_name, item.customer_last_name].filter(Boolean).join(' ') || '-'}</td>
                        <td className="px-4 py-3 text-sm hidden sm:table-cell">{item.city || '-'}</td>
                        <td className="px-4 py-3 text-sm hidden md:table-cell">{item.employee || '-'}</td>
                        <td className="px-4 py-3 text-sm text-right hidden sm:table-cell">{formatMoney(item.sales || 0)}</td>
                        <td className="px-4 py-3 text-sm text-right font-medium">{formatMoney(item.gross_receipts || 0)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}

              {/* Promotions Tab */}
              {activeTab === 'promotions' && (
                <table className="w-full">
                  <thead className="bg-gray-50 border-b">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Date</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Trans #</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Promo Name</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Type</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Cash Value</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden md:table-cell">Employee</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden md:table-cell">Member</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {promoData?.items?.length === 0 && renderEmpty('No promotions activity found')}
                    {promoData?.items?.map((item: any) => (
                      <tr key={item.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm">{item.date}</td>
                        <td className="px-4 py-3 text-sm">{item.transaction_no || '-'}</td>
                        <td className="px-4 py-3 text-sm font-medium">{item.promo_name || '-'}</td>
                        <td className="px-4 py-3 text-sm hidden sm:table-cell">
                          <span className="px-2 py-1 rounded-full text-xs bg-purple-100 text-purple-700">{item.promo_type || '-'}</span>
                        </td>
                        <td className="px-4 py-3 text-sm text-right font-medium text-green-600">{formatMoney(item.cash_value || 0)}</td>
                        <td className="px-4 py-3 text-sm hidden md:table-cell">{item.employee || '-'}</td>
                        <td className="px-4 py-3 text-sm hidden md:table-cell">{item.member || '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}

              {/* Profit & Loss Tab */}
              {activeTab === 'profitloss' && (
                <table className="w-full">
                  <thead className="bg-gray-50 border-b">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Date</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Gross Receipts</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Cost</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Loss</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Profit</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden md:table-cell">Discount</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Margin</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {plData?.items?.length === 0 && renderEmpty('No profit & loss data found')}
                    {plData?.items?.map((item: any) => (
                      <tr key={item.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm font-medium">{item.date}</td>
                        <td className="px-4 py-3 text-sm text-right">{formatMoney(item.gross_receipts || 0)}</td>
                        <td className="px-4 py-3 text-sm text-right hidden sm:table-cell">{formatMoney(item.cost || 0)}</td>
                        <td className="px-4 py-3 text-sm text-right text-red-600 hidden sm:table-cell">{formatMoney(item.loss || 0)}</td>
                        <td className="px-4 py-3 text-sm text-right font-medium text-green-600">{formatMoney(item.profit || 0)}</td>
                        <td className="px-4 py-3 text-sm text-right text-orange-600 hidden md:table-cell">{formatMoney(item.discount || 0)}</td>
                        <td className="px-4 py-3 text-sm text-right">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            (item.margin_pct || 0) >= 50 ? 'bg-green-100 text-green-700' :
                            (item.margin_pct || 0) >= 30 ? 'bg-yellow-100 text-yellow-700' :
                            'bg-red-100 text-red-700'
                          }`}>
                            {(item.margin_pct || 0).toFixed(1)}%
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}

              {/* Sales by City Tab */}
              {activeTab === 'bycity' && (
                <table className="w-full">
                  <thead className="bg-gray-50 border-b">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">City</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">State</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Transactions</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Subtotal</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden md:table-cell">Discount</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Gross</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">% of Sales</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {cityData?.items?.length === 0 && renderEmpty('No sales by city data found')}
                    {cityData?.items?.map((item: any) => (
                      <tr key={item.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm font-medium">{item.city || '-'}</td>
                        <td className="px-4 py-3 text-sm hidden sm:table-cell">{item.state || '-'}</td>
                        <td className="px-4 py-3 text-sm text-right">{(item.transactions || 0).toLocaleString()}</td>
                        <td className="px-4 py-3 text-sm text-right hidden sm:table-cell">{formatMoney(item.subtotal_sales || 0)}</td>
                        <td className="px-4 py-3 text-sm text-right text-orange-600 hidden md:table-cell">{formatMoney(item.discount || 0)}</td>
                        <td className="px-4 py-3 text-sm text-right font-medium">{formatMoney(item.gross_receipts || 0)}</td>
                        <td className="px-4 py-3 text-sm text-right hidden sm:table-cell">
                          <span className="px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-700">{(item.percentage_of_sales || 0).toFixed(1)}%</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}

              {/* Sales by Hour Tab */}
              {activeTab === 'byhour' && (
                <table className="w-full">
                  <thead className="bg-gray-50 border-b">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Hour</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Rec Sales</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Med Sales</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Total Sales</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Gross</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Transactions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {hourData?.items?.length === 0 && renderEmpty('No sales by hour data found')}
                    {hourData?.items?.map((item: any) => {
                      const hourNum = parseInt(item.hour)
                      const label = isNaN(hourNum) ? item.hour : `${hourNum === 0 ? 12 : hourNum > 12 ? hourNum - 12 : hourNum}:00 ${hourNum >= 12 ? 'PM' : 'AM'}`
                      return (
                        <tr key={item.id} className="hover:bg-gray-50">
                          <td className="px-4 py-3 text-sm font-medium">{label}</td>
                          <td className="px-4 py-3 text-sm text-right hidden sm:table-cell">{formatMoney(item.recreational_sales || 0)}</td>
                          <td className="px-4 py-3 text-sm text-right hidden sm:table-cell">{formatMoney(item.medical_sales || 0)}</td>
                          <td className="px-4 py-3 text-sm text-right font-medium">{formatMoney(item.total_sales || 0)}</td>
                          <td className="px-4 py-3 text-sm text-right">{formatMoney(item.gross_receipts || 0)}</td>
                          <td className="px-4 py-3 text-sm text-right hidden sm:table-cell">{(item.num_transactions || 0).toLocaleString()}</td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              )}

              {/* Sales by Product Tab */}
              {activeTab === 'byproduct' && (
                <table className="w-full">
                  <thead className="bg-gray-50 border-b">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Product</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden md:table-cell">SKU</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Category</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden lg:table-cell">Vendor</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Units</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">COGS</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Net Sales</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden md:table-cell">Margin</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {productData?.items?.length === 0 && renderEmpty('No sales by product data found')}
                    {productData?.items?.map((item: any) => (
                      <tr key={item.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm max-w-[200px] truncate"><button onClick={() => navigate(`/products?search=${encodeURIComponent(item.product)}&tab=catalog`)} className="font-medium text-emerald-600 hover:text-emerald-700 hover:underline text-left">{item.product}</button></td>
                        <td className="px-4 py-3 text-sm text-gray-500 hidden md:table-cell">{item.sku || '-'}</td>
                        <td className="px-4 py-3 text-sm hidden sm:table-cell">{item.category || '-'}</td>
                        <td className="px-4 py-3 text-sm hidden lg:table-cell">{item.vendor ? <button onClick={() => navigate(`/products?search=${encodeURIComponent(item.vendor)}&tab=byvendor`)} className="text-blue-600 hover:text-blue-700 hover:underline">{item.vendor}</button> : '-'}</td>
                        <td className="px-4 py-3 text-sm text-right">{(item.units_sold || 0).toLocaleString()}</td>
                        <td className="px-4 py-3 text-sm text-right hidden sm:table-cell">{formatMoney(item.cogs || 0)}</td>
                        <td className="px-4 py-3 text-sm text-right font-medium">{formatMoney(item.net_sales || 0)}</td>
                        <td className="px-4 py-3 text-sm text-right hidden md:table-cell">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            (item.margin || 0) >= 50 ? 'bg-green-100 text-green-700' :
                            (item.margin || 0) >= 30 ? 'bg-yellow-100 text-yellow-700' :
                            'bg-red-100 text-red-700'
                          }`}>
                            {(item.margin || 0).toFixed(1)}%
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}

              {/* Sales by Category Tab */}
              {activeTab === 'bycategory' && (
                <table className="w-full">
                  <thead className="bg-gray-50 border-b">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Category</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Trans</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">COGS</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Retail</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Net Sales</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Gross</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Units</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {categoryData?.items?.length === 0 && renderEmpty('No sales by category data found')}
                    {categoryData?.items?.map((item: any) => (
                      <tr key={item.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm font-medium">{item.product_category || '-'}</td>
                        <td className="px-4 py-3 text-sm text-right">{(item.num_trans || 0).toLocaleString()}</td>
                        <td className="px-4 py-3 text-sm text-right hidden sm:table-cell">{formatMoney(item.cogs || 0)}</td>
                        <td className="px-4 py-3 text-sm text-right hidden sm:table-cell">{formatMoney(item.retail_value || 0)}</td>
                        <td className="px-4 py-3 text-sm text-right font-medium">{formatMoney(item.net_sales || 0)}</td>
                        <td className="px-4 py-3 text-sm text-right">{formatMoney(item.gross_receipt || 0)}</td>
                        <td className="px-4 py-3 text-sm text-right hidden sm:table-cell">{(item.units_sold || 0).toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}

              {/* Sales by Vendor Tab */}
              {activeTab === 'byvendor' && (
                <table className="w-full">
                  <thead className="bg-gray-50 border-b">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Vendor</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Type</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Subtotal</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden md:table-cell">Discounts</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden md:table-cell">Tax</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Gross</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {vendorData?.items?.length === 0 && renderEmpty('No sales by vendor data found')}
                    {vendorData?.items?.map((item: any) => (
                      <tr key={item.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm">{item.vendor ? <button onClick={() => navigate(`/products?search=${encodeURIComponent(item.vendor)}&tab=byvendor`)} className="font-medium text-blue-600 hover:text-blue-700 hover:underline text-left">{item.vendor}</button> : '-'}</td>
                        <td className="px-4 py-3 text-sm hidden sm:table-cell">{item.transaction_type || '-'}</td>
                        <td className="px-4 py-3 text-sm text-right hidden sm:table-cell">{formatMoney(item.subtotal_sales || 0)}</td>
                        <td className="px-4 py-3 text-sm text-right text-orange-600 hidden md:table-cell">{formatMoney(item.discounts || 0)}</td>
                        <td className="px-4 py-3 text-sm text-right hidden md:table-cell">{formatMoney(item.tax || 0)}</td>
                        <td className="px-4 py-3 text-sm text-right font-medium">{formatMoney(item.gross_receipt || 0)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}

              {/* Sales by Consumer Type Tab */}
              {activeTab === 'byconsumer' && (
                <table className="w-full">
                  <thead className="bg-gray-50 border-b">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Breakdown</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Cannabis</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Non-Cannabis</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Gross</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden md:table-cell">COGS</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden md:table-cell">Net Profit</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Visits</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {consumerData?.items?.length === 0 && renderEmpty('No consumer type data found')}
                    {consumerData?.items?.map((item: any) => (
                      <tr key={item.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm font-medium">{item.breakdown || '-'}</td>
                        <td className="px-4 py-3 text-sm text-right hidden sm:table-cell">{formatMoney(item.cannabis_retail_value || 0)}</td>
                        <td className="px-4 py-3 text-sm text-right hidden sm:table-cell">{formatMoney(item.non_cannabis_retail_value || 0)}</td>
                        <td className="px-4 py-3 text-sm text-right font-medium">{formatMoney(item.gross_receipt || 0)}</td>
                        <td className="px-4 py-3 text-sm text-right hidden md:table-cell">{formatMoney(item.cogs || 0)}</td>
                        <td className="px-4 py-3 text-sm text-right text-green-600 hidden md:table-cell">{formatMoney(item.net_profit || 0)}</td>
                        <td className="px-4 py-3 text-sm text-right">{(item.num_visits || 0).toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            {/* Pagination */}
            {renderPagination()}
          </>
        )}
      </div>
    </div>
  )
}
