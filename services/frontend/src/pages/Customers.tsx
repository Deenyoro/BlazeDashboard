import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { Users, UserCheck, UserX, Search, Star, ChevronLeft, ChevronRight, X, Phone, Mail, Calendar, Receipt, ExternalLink } from 'lucide-react'
import { api } from '../api/client'

function formatMoney(val: number) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(val)
}

// Customer Detail Modal
function CustomerDetailModal({ customer, onClose }: { customer: any; onClose: () => void }) {
  const navigate = useNavigate()

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleEscape)
    return () => window.removeEventListener('keydown', handleEscape)
  }, [onClose])

  const name = [customer.first_name, customer.last_name].filter(Boolean).join(' ') || customer.member_name || 'Unknown'

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-white rounded-xl shadow-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-emerald-100 rounded-full flex items-center justify-center">
              <Users className="w-6 h-6 text-emerald-600" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900">{name}</h2>
              <p className="text-sm text-gray-500">Customer Details</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-5">
          {/* Contact Info */}
          <div className="space-y-3">
            {customer.email && (
              <div className="flex items-center gap-3 text-sm">
                <Mail className="w-4 h-4 text-gray-400 flex-shrink-0" />
                <span className="text-gray-900">{customer.email}</span>
              </div>
            )}
            {(customer.phone || customer.cell_phone) && (
              <div className="flex items-center gap-3 text-sm">
                <Phone className="w-4 h-4 text-gray-400 flex-shrink-0" />
                <span className="text-gray-900">{customer.phone || customer.cell_phone}</span>
              </div>
            )}
            {customer.date_joined && (
              <div className="flex items-center gap-3 text-sm">
                <Calendar className="w-4 h-4 text-gray-400 flex-shrink-0" />
                <span className="text-gray-900">Joined {new Date(customer.date_joined).toLocaleDateString()}</span>
              </div>
            )}
          </div>

          {/* Status & Type */}
          <div className="flex flex-wrap gap-2">
            {customer.status && (
              <span className={`px-3 py-1 text-sm font-medium rounded-full ${customer.status === 'Active' || customer.status === 'Accepted' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>
                {customer.status}
              </span>
            )}
            {customer.consumer_type && (
              <span className="px-3 py-1 text-sm font-medium rounded-full bg-blue-100 text-blue-700">
                {customer.consumer_type}
              </span>
            )}
            {customer.member_group && (
              <span className="px-3 py-1 text-sm font-medium rounded-full bg-purple-100 text-purple-700">
                {customer.member_group}
              </span>
            )}
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-2 gap-3">
            {customer.num_visits !== undefined && (
              <div className="bg-blue-50 rounded-lg p-3">
                <p className="text-xs text-blue-600 font-medium">Visits</p>
                <p className="text-xl font-bold text-blue-900">{(customer.num_visits || 0).toLocaleString()}</p>
              </div>
            )}
            {customer.num_sales !== undefined && (
              <div className="bg-green-50 rounded-lg p-3">
                <p className="text-xs text-green-600 font-medium">Sales</p>
                <p className="text-xl font-bold text-green-900">{(customer.num_sales || 0).toLocaleString()}</p>
              </div>
            )}
            {customer.gross_sales_receipts !== undefined && (
              <div className="bg-emerald-50 rounded-lg p-3">
                <p className="text-xs text-emerald-600 font-medium">Gross Receipts</p>
                <p className="text-xl font-bold text-emerald-900">{formatMoney(customer.gross_sales_receipts || 0)}</p>
              </div>
            )}
            {customer.avg_sales_receipts !== undefined && (
              <div className="bg-purple-50 rounded-lg p-3">
                <p className="text-xs text-purple-600 font-medium">Avg Receipt</p>
                <p className="text-xl font-bold text-purple-900">{formatMoney(customer.avg_sales_receipts || 0)}</p>
              </div>
            )}
            {customer.total_amount_spent !== undefined && (
              <div className="bg-emerald-50 rounded-lg p-3 col-span-2">
                <p className="text-xs text-emerald-600 font-medium">Total Spent</p>
                <p className="text-xl font-bold text-emerald-900">{formatMoney(customer.total_amount_spent || 0)}</p>
              </div>
            )}
            {customer.loyalty_points !== undefined && (
              <div className="bg-orange-50 rounded-lg p-3">
                <p className="text-xs text-orange-600 font-medium">Loyalty Points</p>
                <p className="text-xl font-bold text-orange-900">{(customer.loyalty_points || 0).toLocaleString()}</p>
              </div>
            )}
            {customer.last_visit && (
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-600 font-medium">Last Visit</p>
                <p className="text-sm font-bold text-gray-900">{new Date(customer.last_visit).toLocaleDateString()}</p>
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="space-y-2">
            <button
              onClick={() => { onClose(); navigate(`/transactions?search=${encodeURIComponent(name)}`) }}
              className="w-full btn btn-primary flex items-center justify-center gap-2"
            >
              <Receipt className="w-4 h-4" />
              View Transactions
            </button>
            <button
              onClick={() => { onClose(); navigate(`/analytics`) }}
              className="w-full btn btn-secondary flex items-center justify-center gap-2"
            >
              <ExternalLink className="w-4 h-4" />
              View Analytics
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

type Tab = 'consumers' | 'performance' | 'inactive' | 'marketing'

export default function Customers() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [activeTab, setActiveTab] = useState<Tab>('consumers')
  const [searchInput, setSearchInput] = useState('')
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(0)
  const [selectedCustomer, setSelectedCustomer] = useState<any>(null)
  const limit = 25

  // Read URL params on mount
  useEffect(() => {
    const searchParam = searchParams.get('search')
    const tabParam = searchParams.get('tab')
    if (tabParam && ['consumers', 'performance', 'inactive', 'marketing'].includes(tabParam)) {
      setActiveTab(tabParam as Tab)
    }
    if (searchParam) {
      setSearchInput(searchParam)
      setSearch(searchParam)
    }
    if (searchParam || tabParam) {
      setSearchParams({})
    }
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
    queryKey: ['customer-stats'],
    queryFn: async () => {
      const { data } = await api.get('/customers/stats')
      return data
    },
  })

  const { data: consumers, isLoading: consumersLoading } = useQuery({
    queryKey: ['consumers', search, page],
    queryFn: async () => {
      const { data } = await api.get('/customers', { params: { skip: page * limit, limit, search: search || undefined } })
      return data
    },
    enabled: activeTab === 'consumers',
  })

  const { data: performance, isLoading: perfLoading } = useQuery({
    queryKey: ['member-performance', search, page],
    queryFn: async () => {
      const { data } = await api.get('/customers/performance', { params: { skip: page * limit, limit, search: search || undefined } })
      return data
    },
    enabled: activeTab === 'performance',
  })

  const { data: inactive, isLoading: inactiveLoading } = useQuery({
    queryKey: ['inactive-members', search, page],
    queryFn: async () => {
      const { data } = await api.get('/customers/inactive', { params: { skip: page * limit, limit, search: search || undefined } })
      return data
    },
    enabled: activeTab === 'inactive',
  })

  const { data: marketing, isLoading: marketingLoading } = useQuery({
    queryKey: ['marketing-contacts', search, page],
    queryFn: async () => {
      const { data } = await api.get('/customers/marketing', { params: { skip: page * limit, limit, search: search || undefined } })
      return data
    },
    enabled: activeTab === 'marketing',
  })

  const tabs: { key: Tab; label: string }[] = [
    { key: 'consumers', label: 'All Consumers' },
    { key: 'performance', label: 'Performance' },
    { key: 'inactive', label: 'Inactive' },
    { key: 'marketing', label: 'Marketing' },
  ]

  const getCurrentData = () => {
    switch (activeTab) {
      case 'consumers': return { data: consumers, loading: consumersLoading }
      case 'performance': return { data: performance, loading: perfLoading }
      case 'inactive': return { data: inactive, loading: inactiveLoading }
      case 'marketing': return { data: marketing, loading: marketingLoading }
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

  const renderEmpty = (msg: string) => (
    <tr><td colSpan={20} className="px-4 py-8 text-center text-gray-500">{msg}</td></tr>
  )

  return (
    <div className="space-y-6">
      {/* Customer Detail Modal */}
      {selectedCustomer && (
        <CustomerDetailModal customer={selectedCustomer} onClose={() => setSelectedCustomer(null)} />
      )}

      <div>
        <h1 className="text-2xl font-bold text-gray-900">Customers</h1>
        <p className="text-gray-500">Consumer data, performance metrics, and marketing contacts</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card p-5">
          <div className="p-2 bg-blue-100 rounded-lg w-fit"><Users className="w-5 h-5 text-blue-600" /></div>
          <div className="mt-3">
            <div className="text-2xl font-bold text-gray-900">{statsLoading ? '...' : (stats?.total_consumers || 0).toLocaleString()}</div>
            <div className="text-sm text-gray-500">Total Consumers</div>
          </div>
        </div>
        <div className="card p-5">
          <div className="p-2 bg-green-100 rounded-lg w-fit"><UserCheck className="w-5 h-5 text-green-600" /></div>
          <div className="mt-3">
            <div className="text-2xl font-bold text-gray-900">{statsLoading ? '...' : (stats?.active || 0).toLocaleString()}</div>
            <div className="text-sm text-gray-500">Active</div>
          </div>
        </div>
        <div className="card p-5">
          <div className="p-2 bg-red-100 rounded-lg w-fit"><UserX className="w-5 h-5 text-red-600" /></div>
          <div className="mt-3">
            <div className="text-2xl font-bold text-gray-900">{statsLoading ? '...' : (stats?.inactive || 0).toLocaleString()}</div>
            <div className="text-sm text-gray-500">Inactive</div>
          </div>
        </div>
        <div className="card p-5">
          <div className="p-2 bg-purple-100 rounded-lg w-fit"><Star className="w-5 h-5 text-purple-600" /></div>
          <div className="mt-3">
            <div className="text-2xl font-bold text-gray-900">{statsLoading ? '...' : (stats?.members_with_performance || 0).toLocaleString()}</div>
            <div className="text-sm text-gray-500">w/ Performance</div>
          </div>
        </div>
      </div>

      {/* Tabs + Search */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="overflow-x-auto w-full sm:w-auto scrollbar-hide -mx-4 px-4 sm:mx-0 sm:px-0">
          <div className="flex space-x-1 bg-gray-100 rounded-lg p-1 w-max sm:w-auto">
            {tabs.map((tab) => (
              <button
                key={tab.key}
                onClick={() => handleTabChange(tab.key)}
                className={`px-3 sm:px-4 py-2 text-sm font-medium rounded-md transition-colors whitespace-nowrap ${
                  activeTab === tab.key ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
        <div className="relative w-full sm:w-64">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search customers..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          />
        </div>
      </div>

      {/* Tab Content */}
      <div className="card overflow-hidden">
        {loading ? (
          <div className="p-8 text-center">
            <div className="animate-spin w-8 h-8 border-4 border-emerald-500 border-t-transparent rounded-full mx-auto" />
            <p className="mt-4 text-gray-500">Loading...</p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              {activeTab === 'consumers' && (
                <table className="w-full">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Name</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Email</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden md:table-cell">Phone</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Status</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Type</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden md:table-cell">Date Joined</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {consumers?.items?.length === 0 && renderEmpty('No consumers found')}
                    {consumers?.items?.map((c: any) => (
                      <tr key={c.id} onClick={() => setSelectedCustomer(c)} className="hover:bg-blue-50 cursor-pointer transition-colors">
                        <td className="px-4 py-3 font-medium text-emerald-600">{c.first_name} {c.last_name}</td>
                        <td className="px-4 py-3 text-gray-600 hidden sm:table-cell">{c.email || '-'}</td>
                        <td className="px-4 py-3 text-gray-600 hidden md:table-cell">{c.phone || '-'}</td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${c.status === 'Active' || c.status === 'Accepted' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>
                            {c.status || '-'}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-gray-600 hidden sm:table-cell">{c.consumer_type || '-'}</td>
                        <td className="px-4 py-3 text-gray-600 hidden md:table-cell">{c.date_joined ? new Date(c.date_joined).toLocaleDateString() : '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}

              {activeTab === 'performance' && (
                <table className="w-full">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Member</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Visits</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Sales</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Gross</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Avg Receipt</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden md:table-cell">Loyalty Pts</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {performance?.items?.length === 0 && renderEmpty('No performance data found')}
                    {performance?.items?.map((m: any) => (
                      <tr key={m.id} onClick={() => setSelectedCustomer(m)} className="hover:bg-blue-50 cursor-pointer transition-colors">
                        <td className="px-4 py-3 font-medium text-emerald-600">{m.member_name}</td>
                        <td className="px-4 py-3 text-right text-gray-900">{m.num_visits || 0}</td>
                        <td className="px-4 py-3 text-right text-gray-900 hidden sm:table-cell">{m.num_sales || 0}</td>
                        <td className="px-4 py-3 text-right text-gray-900">{formatMoney(m.gross_sales_receipts || 0)}</td>
                        <td className="px-4 py-3 text-right text-gray-600 hidden sm:table-cell">{formatMoney(m.avg_sales_receipts || 0)}</td>
                        <td className="px-4 py-3 text-right text-gray-600 hidden md:table-cell">{(m.loyalty_points || 0).toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}

              {activeTab === 'inactive' && (
                <table className="w-full">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Name</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Phone</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden md:table-cell">Email</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Last Visit</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Total Spent</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {inactive?.items?.length === 0 && renderEmpty('No inactive members found')}
                    {inactive?.items?.map((m: any) => (
                      <tr key={m.id} onClick={() => setSelectedCustomer(m)} className="hover:bg-blue-50 cursor-pointer transition-colors">
                        <td className="px-4 py-3 font-medium text-emerald-600">{m.first_name} {m.last_name}</td>
                        <td className="px-4 py-3 text-gray-600 hidden sm:table-cell">{m.cell_phone || '-'}</td>
                        <td className="px-4 py-3 text-gray-600 hidden md:table-cell">{m.email || '-'}</td>
                        <td className="px-4 py-3 text-gray-600">{m.last_visit ? new Date(m.last_visit).toLocaleDateString() : '-'}</td>
                        <td className="px-4 py-3 text-right text-gray-900">{formatMoney(m.total_amount_spent || 0)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}

              {activeTab === 'marketing' && (
                <table className="w-full">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Name</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Email</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Group</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden md:table-cell">Marketing Source</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Loyalty Pts</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {marketing?.items?.length === 0 && renderEmpty('No marketing contacts found')}
                    {marketing?.items?.map((m: any) => (
                      <tr key={m.id} onClick={() => setSelectedCustomer(m)} className="hover:bg-blue-50 cursor-pointer transition-colors">
                        <td className="px-4 py-3 font-medium text-emerald-600">{m.first_name} {m.last_name}</td>
                        <td className="px-4 py-3 text-gray-600 hidden sm:table-cell">{m.email || '-'}</td>
                        <td className="px-4 py-3 text-gray-600 hidden sm:table-cell">{m.membership_group || '-'}</td>
                        <td className="px-4 py-3 text-gray-600 hidden md:table-cell">{m.marketing_source || '-'}</td>
                        <td className="px-4 py-3 text-right text-gray-600">{(m.loyalty_points || 0).toLocaleString()}</td>
                      </tr>
                    ))}
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
