import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import { format } from 'date-fns'
import {
  Search,
  Filter,
  ChevronLeft,
  ChevronRight,
  X,
  Download,
  Package,
  User,
  CreditCard,
  MapPin,
  Tag,
  Receipt,
  Users,
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { transactionApi, Transaction, ProductSale } from '../api/client'

function formatMoney(val: number) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(val)
}

// Transaction Detail Modal Component
function TransactionDetailModal({
  transNo,
  onClose,
}: {
  transNo: string
  onClose: () => void
}) {
  const navigate = useNavigate()
  const { data: detail, isLoading } = useQuery({
    queryKey: ['transaction-detail', transNo],
    queryFn: () => transactionApi.getDetail(transNo),
    enabled: !!transNo,
  })

  // Close on escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleEscape)
    return () => window.removeEventListener('keydown', handleEscape)
  }, [onClose])

  if (isLoading) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8">
          <div className="animate-spin w-8 h-8 border-4 border-emerald-500 border-t-transparent rounded-full mx-auto" />
          <p className="mt-4 text-gray-600">Loading transaction...</p>
        </div>
      </div>
    )
  }

  if (!detail) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div
        className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between bg-gray-50">
          <div>
            <h2 className="text-xl font-bold text-gray-900">
              Transaction #{detail.trans_no}
            </h2>
            <p className="text-sm text-gray-500">
              {format(new Date(detail.date), 'MMMM d, yyyy h:mm a')}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-200 rounded-full transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Status Row */}
          <div className="flex flex-wrap gap-2">
            <span
              className={`inline-flex px-3 py-1 text-sm font-medium rounded-full ${
                detail.trans_type === 'Refund'
                  ? 'bg-red-100 text-red-700'
                  : 'bg-green-100 text-green-700'
              }`}
            >
              {detail.trans_type}
            </span>
            <span className="inline-flex px-3 py-1 text-sm font-medium rounded-full bg-blue-100 text-blue-700">
              {detail.trans_status}
            </span>
            <span className="inline-flex px-3 py-1 text-sm font-medium rounded-full bg-purple-100 text-purple-700">
              {detail.queue_type}
            </span>
            {detail.order_source && (
              <span className="inline-flex px-3 py-1 text-sm font-medium rounded-full bg-gray-100 text-gray-700">
                {detail.order_source}
              </span>
            )}
          </div>

          {/* Info Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Customer */}
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center gap-2 text-gray-500 mb-2">
                <User className="w-4 h-4" />
                <span className="text-sm font-medium">Customer</span>
              </div>
              {detail.member_name && detail.member_name !== 'Walk-in' ? (
                <button onClick={() => { onClose(); navigate(`/customers?search=${encodeURIComponent(detail.member_name || '')}`) }} className="font-semibold text-emerald-600 hover:text-emerald-700 hover:underline text-left">
                  {detail.member_name}
                </button>
              ) : (
                <p className="font-semibold text-gray-900">Walk-in</p>
              )}
              {detail.member_group && (
                <p className="text-sm text-gray-500">{detail.member_group}</p>
              )}
            </div>

            {/* Payment */}
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center gap-2 text-gray-500 mb-2">
                <CreditCard className="w-4 h-4" />
                <span className="text-sm font-medium">Payment</span>
              </div>
              <p className="font-semibold text-gray-900">{detail.payment_type || 'N/A'}</p>
              {detail.payment_tendered > 0 && (
                <p className="text-sm text-gray-500">
                  Tendered: {formatMoney(detail.payment_tendered)}
                </p>
              )}
            </div>

            {/* Sold By */}
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center gap-2 text-gray-500 mb-2">
                <User className="w-4 h-4" />
                <span className="text-sm font-medium">Sold By</span>
              </div>
              {detail.sold_by_name ? (
                <button onClick={() => { onClose(); navigate(`/transactions?employee=${encodeURIComponent(detail.sold_by_name || '')}`) }} className="font-semibold text-blue-600 hover:text-blue-700 hover:underline text-left">
                  {detail.sold_by_name}
                </button>
              ) : (
                <p className="font-semibold text-gray-900">N/A</p>
              )}
              {detail.terminal && (
                <p className="text-sm text-gray-500">{detail.terminal}</p>
              )}
            </div>

            {/* Location */}
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center gap-2 text-gray-500 mb-2">
                <MapPin className="w-4 h-4" />
                <span className="text-sm font-medium">Location</span>
              </div>
              <p className="font-semibold text-gray-900">{detail.shop || 'N/A'}</p>
              {detail.region && detail.region !== 'No Region' && (
                <p className="text-sm text-gray-500">{detail.region}</p>
              )}
            </div>
          </div>

          {/* Staff Timeline */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <Users className="w-5 h-5 text-gray-500" />
              <h3 className="text-lg font-semibold text-gray-900">Staff & Timeline</h3>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
                <div>
                  <p className="text-gray-500">Created By</p>
                  <p className="font-medium">{detail.created_by_name || 'N/A'}</p>
                  {detail.created_date && (
                    <p className="text-xs text-gray-400">
                      {format(new Date(detail.created_date), 'MMM d, h:mm a')}
                    </p>
                  )}
                </div>
                <div>
                  <p className="text-gray-500">Prepared By</p>
                  <p className="font-medium">{detail.prepared_by || 'N/A'}</p>
                  {detail.prepared_date && (
                    <p className="text-xs text-gray-400">
                      {format(new Date(detail.prepared_date), 'MMM d, h:mm a')}
                    </p>
                  )}
                </div>
                <div>
                  <p className="text-gray-500">Packed By</p>
                  <p className="font-medium">{detail.packed_by || 'N/A'}</p>
                  {detail.packed_date && (
                    <p className="text-xs text-gray-400">
                      {format(new Date(detail.packed_date), 'MMM d, h:mm a')}
                    </p>
                  )}
                </div>
                <div>
                  <p className="text-gray-500">Sold By</p>
                  <p className="font-medium">{detail.sold_by_name || 'N/A'}</p>
                  <p className="text-xs text-gray-400">
                    {format(new Date(detail.date), 'MMM d, h:mm a')}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Items Section */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <Package className="w-5 h-5 text-gray-500" />
              <h3 className="text-lg font-semibold text-gray-900">
                Items ({detail.item_count})
              </h3>
            </div>

            {detail.items.length === 0 ? (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-yellow-800">
                <p>No item details available for this transaction.</p>
                <p className="text-sm mt-1">This may be a recent transaction not yet in the sales details report.</p>
              </div>
            ) : (
              <div className="border border-gray-200 rounded-lg overflow-hidden">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-semibold text-gray-600 uppercase">
                        Product
                      </th>
                      <th className="px-4 py-2 text-left text-xs font-semibold text-gray-600 uppercase">
                        Category
                      </th>
                      <th className="px-4 py-2 text-right text-xs font-semibold text-gray-600 uppercase">
                        Qty
                      </th>
                      <th className="px-4 py-2 text-right text-xs font-semibold text-gray-600 uppercase">
                        Price
                      </th>
                      <th className="px-4 py-2 text-right text-xs font-semibold text-gray-600 uppercase">
                        Tax
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {detail.items.map((item: ProductSale) => (
                      <tr key={item.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3">
                          <div>
                            <button onClick={() => { onClose(); navigate(`/products?search=${encodeURIComponent(item.product_name || '')}&tab=catalog`) }} className="font-medium text-emerald-600 hover:text-emerald-700 hover:underline text-left">
                              {item.product_name}
                            </button>
                            <p className="text-xs text-gray-500">
                              {item.brand} • SKU: {item.sku}
                            </p>
                            {item.metrc_tag && (
                              <p className="text-xs text-gray-400 font-mono mt-1">
                                METRC: {item.metrc_tag}
                              </p>
                            )}
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <span className="inline-flex px-2 py-1 text-xs font-medium rounded bg-gray-100 text-gray-700">
                            {item.category}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-right text-gray-600">
                          {item.quantity || 1}
                        </td>
                        <td className="px-4 py-3 text-right font-medium text-gray-900">
                          {formatMoney(item.net_sales)}
                        </td>
                        <td className="px-4 py-3 text-right text-gray-600">
                          {formatMoney(item.total_tax)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Financial Summary */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <Receipt className="w-5 h-5 text-gray-500" />
              <h3 className="text-lg font-semibold text-gray-900">Financial Summary</h3>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-600">Subtotal</span>
                  <span className="font-medium">{formatMoney(detail.gross_sales)}</span>
                </div>
                {detail.pre_tax_discounts > 0 && (
                  <div className="flex justify-between text-red-600">
                    <span>Discounts</span>
                    <span>-{formatMoney(detail.pre_tax_discounts)}</span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span className="text-gray-600">Tax</span>
                  <span className="font-medium">{formatMoney(detail.total_tax)}</span>
                </div>
                {detail.tips > 0 && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Tips</span>
                    <span className="font-medium">{formatMoney(detail.tips)}</span>
                  </div>
                )}
                <div className="border-t border-gray-300 pt-2 mt-2 flex justify-between text-lg">
                  <span className="font-semibold text-gray-900">Total</span>
                  <span className="font-bold text-emerald-600">
                    {formatMoney(detail.total_due)}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Tax Breakdown (collapsed by default) */}
          {(detail.city_tax > 0 || detail.county_tax > 0 || detail.state_tax > 0) && (
            <details className="group">
              <summary className="cursor-pointer text-sm text-gray-500 hover:text-gray-700">
                View tax breakdown
              </summary>
              <div className="mt-2 bg-gray-50 rounded-lg p-4 text-sm space-y-1">
                {detail.city_tax > 0 && (
                  <div className="flex justify-between">
                    <span>City Tax</span>
                    <span>{formatMoney(detail.city_tax)}</span>
                  </div>
                )}
                {detail.county_tax > 0 && (
                  <div className="flex justify-between">
                    <span>County Tax</span>
                    <span>{formatMoney(detail.county_tax)}</span>
                  </div>
                )}
                {detail.state_tax > 0 && (
                  <div className="flex justify-between">
                    <span>State Tax</span>
                    <span>{formatMoney(detail.state_tax)}</span>
                  </div>
                )}
                {detail.pre_al_excise_tax > 0 && (
                  <div className="flex justify-between">
                    <span>Pre AL Excise Tax</span>
                    <span>{formatMoney(detail.pre_al_excise_tax)}</span>
                  </div>
                )}
              </div>
            </details>
          )}

          {/* Compliance Info */}
          {detail.compliance_system && (
            <div className="text-sm text-gray-500 flex items-center gap-2">
              <Tag className="w-4 h-4" />
              <span>
                {detail.compliance_system} Order: {detail.compliance_order_id}
              </span>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 flex justify-end">
          <button onClick={onClose} className="btn btn-secondary">
            Close
          </button>
        </div>
      </div>
    </div>
  )
}

export default function Transactions() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [page, setPage] = useState(0)
  const [limit] = useState(25)
  const [search, setSearch] = useState('')
  const [searchInput, setSearchInput] = useState('')
  const [filters, setFilters] = useState<{
    trans_type?: string
    queue_type?: string
    payment_type?: string
    employee?: string
    start_date?: string
    end_date?: string
  }>({})
  const [showFilters, setShowFilters] = useState(false)
  const [selectedTransNo, setSelectedTransNo] = useState<string | null>(null)

  // Read URL params on mount
  useEffect(() => {
    const employeeParam = searchParams.get('employee')
    const searchParam = searchParams.get('search')
    if (employeeParam) {
      setFilters(prev => ({ ...prev, employee: employeeParam }))
      setShowFilters(true)
    }
    if (searchParam) {
      setSearchInput(searchParam)
      setSearch(searchParam)
    }
    if (employeeParam || searchParam) {
      setSearchParams({})
    }
  }, [])

  const { data, isLoading } = useQuery({
    queryKey: ['transactions', page, limit, search, filters],
    queryFn: async () => {
      return transactionApi.list({
        skip: page * limit,
        limit,
        search: search || undefined,
        trans_type: filters.trans_type || undefined,
        queue_type: filters.queue_type || undefined,
        payment_type: filters.payment_type || undefined,
        employee: filters.employee || undefined,
        start_date: filters.start_date || undefined,
        end_date: filters.end_date || undefined,
      })
    },
  })

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setSearch(searchInput)
    setPage(0)
  }

  // Also search on input change after debounce
  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchInput !== search) {
        setSearch(searchInput)
        setPage(0)
      }
    }, 500)
    return () => clearTimeout(timer)
  }, [searchInput])

  const clearFilters = () => {
    setFilters({})
    setSearch('')
    setSearchInput('')
    setPage(0)
  }

  const totalPages = Math.ceil((data?.total || 0) / limit)
  const hasActiveFilters = Object.values(filters).some(Boolean) || search

  return (
    <div className="space-y-6">
      {/* Transaction Detail Modal */}
      {selectedTransNo && (
        <TransactionDetailModal
          transNo={selectedTransNo}
          onClose={() => setSelectedTransNo(null)}
        />
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Transactions</h1>
          <p className="text-gray-500">
            {data?.total?.toLocaleString() || 0} total transactions
            {search && ` matching "${search}"`}
          </p>
        </div>
        <button className="btn btn-secondary">
          <Download className="w-4 h-4 mr-2" />
          Export CSV
        </button>
      </div>

      {/* Search and Filters */}
      <div className="card p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <form onSubmit={handleSearch} className="flex-1 flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search by trans #, employee, customer..."
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                className="input pl-9"
              />
            </div>
            <button type="submit" className="btn btn-primary">
              Search
            </button>
          </form>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`btn ${showFilters ? 'btn-primary' : 'btn-secondary'}`}
          >
            <Filter className="w-4 h-4 mr-2" />
            Filters
            {hasActiveFilters && (
              <span className="ml-2 w-2 h-2 bg-red-500 rounded-full" />
            )}
          </button>
        </div>

        {/* Filter Panel */}
        {showFilters && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Transaction Type
                </label>
                <select
                  value={filters.trans_type || ''}
                  onChange={(e) => {
                    setFilters({ ...filters, trans_type: e.target.value || undefined })
                    setPage(0)
                  }}
                  className="select"
                >
                  <option value="">All Types</option>
                  <option value="Sale">Sale</option>
                  <option value="Refund">Refund</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Queue Type
                </label>
                <select
                  value={filters.queue_type || ''}
                  onChange={(e) => {
                    setFilters({ ...filters, queue_type: e.target.value || undefined })
                    setPage(0)
                  }}
                  className="select"
                >
                  <option value="">All Queues</option>
                  <option value="WalkIn">Walk-in</option>
                  <option value="Special">Special</option>
                  <option value="Delivery">Delivery</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Payment Type
                </label>
                <select
                  value={filters.payment_type || ''}
                  onChange={(e) => {
                    setFilters({ ...filters, payment_type: e.target.value || undefined })
                    setPage(0)
                  }}
                  className="select"
                >
                  <option value="">All Payments</option>
                  <option value="Cash">Cash</option>
                  <option value="BlazePay">BlazePay</option>
                  <option value="Debit">Debit</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Employee
                </label>
                <input
                  type="text"
                  placeholder="Employee name..."
                  value={filters.employee || ''}
                  onChange={(e) => {
                    setFilters({ ...filters, employee: e.target.value || undefined })
                    setPage(0)
                  }}
                  className="input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Start Date
                </label>
                <input
                  type="date"
                  value={filters.start_date || ''}
                  onChange={(e) => {
                    setFilters({ ...filters, start_date: e.target.value || undefined })
                    setPage(0)
                  }}
                  className="input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  End Date
                </label>
                <input
                  type="date"
                  value={filters.end_date || ''}
                  onChange={(e) => {
                    setFilters({ ...filters, end_date: e.target.value || undefined })
                    setPage(0)
                  }}
                  className="input"
                />
              </div>
            </div>
            {hasActiveFilters && (
              <button
                onClick={clearFilters}
                className="mt-4 text-sm text-red-600 hover:text-red-700 flex items-center"
              >
                <X className="w-4 h-4 mr-1" />
                Clear all filters
              </button>
            )}
          </div>
        )}
      </div>

      {/* Transactions Table */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                  Trans #
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                  Date
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                  Queue
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                  Employee
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                  Payment
                </th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase tracking-wider">
                  Total
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {isLoading ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-gray-500">
                    <div className="animate-spin w-6 h-6 border-2 border-emerald-500 border-t-transparent rounded-full mx-auto mb-2" />
                    Loading transactions...
                  </td>
                </tr>
              ) : data?.transactions?.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-gray-500">
                    No transactions found
                    {search && ` for "${search}"`}
                  </td>
                </tr>
              ) : (
                data?.transactions?.map((t: Transaction) => (
                  <tr
                    key={t.id}
                    onClick={() => t.trans_no && setSelectedTransNo(t.trans_no)}
                    className="hover:bg-gray-50 cursor-pointer transition-colors"
                  >
                    <td className="px-4 py-3">
                      <span className="font-medium text-emerald-600 hover:text-emerald-700">
                        #{t.trans_no}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      {format(new Date(t.date), 'MMM d, yyyy h:mm a')}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                          t.trans_type === 'Refund'
                            ? 'bg-red-100 text-red-700'
                            : 'bg-green-100 text-green-700'
                        }`}
                      >
                        {t.trans_type}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-600">{t.queue_type}</td>
                    <td className="px-4 py-3 text-gray-600">{t.sold_by_name}</td>
                    <td className="px-4 py-3 text-gray-600">{t.payment_type}</td>
                    <td className="px-4 py-3 text-right">
                      <span
                        className={`font-medium ${
                          t.trans_type === 'Refund' ? 'text-red-600' : 'text-gray-900'
                        }`}
                      >
                        {t.trans_type === 'Refund' ? '-' : ''}
                        {formatMoney(Math.abs(t.total_due))}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="px-4 py-3 border-t border-gray-200 flex flex-col sm:flex-row items-center justify-between gap-2">
          <div className="text-sm text-gray-600">
            {(data?.total || 0) > 0
              ? `Showing ${page * limit + 1} to ${Math.min((page + 1) * limit, data?.total || 0)} of ${data?.total?.toLocaleString() || 0}`
              : 'No records'}
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage(Math.max(0, page - 1))}
              disabled={page === 0}
              className="btn btn-secondary disabled:opacity-50"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="text-sm text-gray-600">
              Page {page + 1} of {totalPages || 1}
            </span>
            <button
              onClick={() => setPage(Math.min(totalPages - 1, page + 1))}
              disabled={page >= totalPages - 1}
              className="btn btn-secondary disabled:opacity-50"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
