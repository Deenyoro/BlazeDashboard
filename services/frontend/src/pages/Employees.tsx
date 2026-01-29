import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import {
  UserCheck,
  TrendingUp,
  DollarSign,
  Receipt,
  X,
  ChevronRight,
  ChevronLeft,
  Search,
  Clock,
  Activity,
  BarChart3,
} from 'lucide-react'
import { api } from '../api/client'

interface Employee {
  id: string
  employee_id: string
  name: string
  transaction_count: number
  total_sales: number
  total_refunds: number
  net_sales: number
  average_transaction: number
}

interface EmployeeListResponse {
  employees: Employee[]
  total: number
}

function formatMoney(val: number) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(val)
}

type Tab = 'overview' | 'performance' | 'activity' | 'timeclock'

export default function Employees() {
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<Tab>('overview')
  const [selectedEmployee, setSelectedEmployee] = useState<Employee | null>(null)
  const [searchInput, setSearchInput] = useState('')
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(0)
  const limit = 25

  useEffect(() => {
    const timer = setTimeout(() => setSearch(searchInput), 300)
    return () => clearTimeout(timer)
  }, [searchInput])

  const handleTabChange = (tab: Tab) => {
    setActiveTab(tab)
    setPage(0)
  }

  const { data, isLoading } = useQuery({
    queryKey: ['employees'],
    queryFn: async (): Promise<EmployeeListResponse> => {
      const { data } = await api.get('/employees')
      return data
    },
  })

  const { data: perfData, isLoading: perfLoading } = useQuery({
    queryKey: ['employee-performance', page, search],
    queryFn: async () => {
      const { data } = await api.get('/employees/performance', {
        params: { skip: page * limit, limit, search: search || undefined },
      })
      return data
    },
    enabled: activeTab === 'performance',
  })

  const { data: activityData, isLoading: activityLoading } = useQuery({
    queryKey: ['employee-activity', page, search],
    queryFn: async () => {
      const { data } = await api.get('/employees/activity', {
        params: { skip: page * limit, limit, search: search || undefined },
      })
      return data
    },
    enabled: activeTab === 'activity',
  })

  const { data: timeClockData, isLoading: timeClockLoading } = useQuery({
    queryKey: ['employee-timeclock', page, search],
    queryFn: async () => {
      const { data } = await api.get('/employees/time-clock', {
        params: { skip: page * limit, limit, search: search || undefined },
      })
      return data
    },
    enabled: activeTab === 'timeclock',
  })

  const handleViewTransactions = (employeeName: string) => {
    navigate(`/transactions?employee=${encodeURIComponent(employeeName)}`)
  }

  const chartData = data?.employees
    ?.slice(0, 10)
    .map((e) => ({
      name: e.name?.split(' ')[0] || 'Unknown',
      sales: e.net_sales,
      transactions: e.transaction_count,
    }))
    .sort((a, b) => b.sales - a.sales)

  const totalSales = data?.employees?.reduce((sum, e) => sum + e.net_sales, 0) || 0
  const totalTransactions = data?.employees?.reduce((sum, e) => sum + e.transaction_count, 0) || 0
  const avgPerEmployee = data?.employees?.length ? totalSales / data.employees.length : 0

  const getCurrentTotal = () => {
    switch (activeTab) {
      case 'performance': return perfData?.total || 0
      case 'activity': return activityData?.total || 0
      case 'timeclock': return timeClockData?.total || 0
      default: return 0
    }
  }
  const totalPages = Math.ceil(getCurrentTotal() / limit)

  const tabs = [
    { id: 'overview' as Tab, label: 'Overview', icon: BarChart3 },
    { id: 'performance' as Tab, label: 'Performance', icon: TrendingUp },
    { id: 'activity' as Tab, label: 'Activity Log', icon: Activity },
    { id: 'timeclock' as Tab, label: 'Time Clock', icon: Clock },
  ]

  const filteredEmployees = data?.employees
    ?.filter((e) => !search || e.name.toLowerCase().includes(search.toLowerCase()))
    ?.sort((a, b) => b.net_sales - a.net_sales)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Employees</h1>
        <p className="text-gray-500">
          {data?.total || 0} employees with sales activity
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card p-4 sm:p-5">
          <div className="p-2 bg-blue-100 rounded-lg w-fit">
            <UserCheck className="w-5 h-5 text-blue-600" />
          </div>
          <div className="mt-3">
            <div className="text-xl sm:text-2xl font-bold text-gray-900">
              {isLoading ? '...' : data?.total || 0}
            </div>
            <div className="text-xs sm:text-sm text-gray-500">Active Employees</div>
          </div>
        </div>
        <div className="card p-4 sm:p-5">
          <div className="p-2 bg-green-100 rounded-lg w-fit">
            <DollarSign className="w-5 h-5 text-green-600" />
          </div>
          <div className="mt-3">
            <div className="text-xl sm:text-2xl font-bold text-gray-900">
              {isLoading ? '...' : formatMoney(totalSales)}
            </div>
            <div className="text-xs sm:text-sm text-gray-500">Total Sales</div>
          </div>
        </div>
        <div className="card p-4 sm:p-5">
          <div className="p-2 bg-purple-100 rounded-lg w-fit">
            <Receipt className="w-5 h-5 text-purple-600" />
          </div>
          <div className="mt-3">
            <div className="text-xl sm:text-2xl font-bold text-gray-900">
              {isLoading ? '...' : totalTransactions.toLocaleString()}
            </div>
            <div className="text-xs sm:text-sm text-gray-500">Total Transactions</div>
          </div>
        </div>
        <div className="card p-4 sm:p-5">
          <div className="p-2 bg-orange-100 rounded-lg w-fit">
            <TrendingUp className="w-5 h-5 text-orange-600" />
          </div>
          <div className="mt-3">
            <div className="text-xl sm:text-2xl font-bold text-gray-900">
              {isLoading ? '...' : formatMoney(avgPerEmployee)}
            </div>
            <div className="text-xs sm:text-sm text-gray-500">Avg per Employee</div>
          </div>
        </div>
      </div>

      {/* Tabs + Search */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="border-b border-gray-200 w-full sm:w-auto sm:border-0 -mx-4 sm:mx-0">
          <nav className="flex space-x-6 sm:space-x-1 overflow-x-auto px-4 sm:px-0 scrollbar-hide sm:bg-gray-100 sm:rounded-lg sm:p-1">
            {tabs.map((tab) => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => handleTabChange(tab.id)}
                  className={`flex items-center gap-1.5 py-3 sm:py-2 px-1 sm:px-3 border-b-2 sm:border-0 font-medium text-sm transition-colors whitespace-nowrap flex-shrink-0 sm:rounded-md ${
                    activeTab === tab.id
                      ? 'border-emerald-500 text-emerald-600 sm:bg-white sm:text-gray-900 sm:shadow-sm sm:border-transparent'
                      : 'border-transparent text-gray-500 hover:text-gray-700 sm:hover:text-gray-900'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                </button>
              )
            })}
          </nav>
        </div>
        {activeTab !== 'overview' && (
          <div className="relative w-full sm:w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search employees..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
        )}
        {activeTab === 'overview' && (
          <div className="relative w-full sm:w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Filter employees..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
        )}
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <>
          {/* Chart */}
          <div className="card p-5">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Top 10 by Sales</h2>
            <div className="h-72 sm:h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" tickFormatter={(val) => `$${(val / 1000).toFixed(0)}k`} fontSize={12} />
                  <YAxis type="category" dataKey="name" width={70} fontSize={12} />
                  <Tooltip formatter={(val: number) => formatMoney(val)} labelFormatter={(label) => `Employee: ${label}`} />
                  <Bar dataKey="sales" fill="#2563eb" name="Net Sales" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Employees Table */}
          <div className="card overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Employee</th>
                    <th className="px-4 py-3 text-center text-xs font-semibold text-gray-600 uppercase">Trans</th>
                    <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Gross</th>
                    <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Refunds</th>
                    <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Net Sales</th>
                    <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Avg</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {isLoading ? (
                    <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-500">Loading employees...</td></tr>
                  ) : filteredEmployees?.length === 0 ? (
                    <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-500">No employees found</td></tr>
                  ) : (
                    filteredEmployees?.map((e) => (
                      <tr key={e.id} onClick={() => setSelectedEmployee(e)} className="hover:bg-blue-50 cursor-pointer transition-colors">
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                              <UserCheck className="w-4 h-4 text-blue-600" />
                            </div>
                            <div className="font-medium text-gray-900 truncate">{e.name}</div>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-center text-gray-900 font-medium">{e.transaction_count?.toLocaleString()}</td>
                        <td className="px-4 py-3 text-right text-gray-900">{formatMoney(e.total_sales)}</td>
                        <td className="px-4 py-3 text-right text-red-600 hidden sm:table-cell">{formatMoney(e.total_refunds)}</td>
                        <td className="px-4 py-3 text-right font-medium text-gray-900">{formatMoney(e.net_sales)}</td>
                        <td className="px-4 py-3 text-right text-gray-600 hidden sm:table-cell">
                          <div className="flex items-center justify-end gap-2">
                            {formatMoney(e.average_transaction)}
                            <ChevronRight className="w-4 h-4 text-gray-400" />
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
            <div className="px-5 py-3 border-t border-gray-200 text-sm text-gray-500">
              {filteredEmployees?.length || 0} employees
            </div>
          </div>
        </>
      )}

      {/* Performance Tab */}
      {activeTab === 'performance' && (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Date</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Employee</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Gross</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">Trans</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Avg Trans</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden md:table-cell">Avg Time</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden md:table-cell">Discounts</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase hidden lg:table-cell">Tips</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {perfLoading ? (
                  <tr><td colSpan={8} className="px-4 py-8 text-center text-gray-500">Loading...</td></tr>
                ) : perfData?.items?.length === 0 ? (
                  <tr><td colSpan={8} className="px-4 py-8 text-center text-gray-500">No performance data found</td></tr>
                ) : (
                  perfData?.items?.map((p: any) => (
                    <tr key={p.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm text-gray-600">{p.date}</td>
                      <td className="px-4 py-3 text-sm"><button onClick={() => { const emp = data?.employees?.find(e => e.name === p.employee_name); if (emp) setSelectedEmployee(emp); else navigate(`/transactions?employee=${encodeURIComponent(p.employee_name)}`) }} className="font-medium text-blue-600 hover:text-blue-700 hover:underline text-left">{p.employee_name}</button></td>
                      <td className="px-4 py-3 text-sm text-right font-medium text-gray-900">{formatMoney(p.gross_receipts || 0)}</td>
                      <td className="px-4 py-3 text-sm text-right text-gray-900">{p.transaction_count || 0}</td>
                      <td className="px-4 py-3 text-sm text-right text-gray-600 hidden sm:table-cell">{formatMoney(p.avg_transaction || 0)}</td>
                      <td className="px-4 py-3 text-sm text-right text-gray-600 hidden md:table-cell">{p.avg_transaction_time || '-'}</td>
                      <td className="px-4 py-3 text-sm text-right text-orange-600 hidden md:table-cell">{formatMoney(p.discounts || 0)}</td>
                      <td className="px-4 py-3 text-sm text-right text-green-600 hidden lg:table-cell">{formatMoney(p.tips || 0)}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          <div className="px-4 py-3 border-t bg-gray-50 flex flex-col sm:flex-row items-center justify-between gap-2">
            <div className="text-sm text-gray-500">
              {(perfData?.total || 0) > 0
                ? `Showing ${page * limit + 1} - ${Math.min((page + 1) * limit, perfData?.total || 0)} of ${(perfData?.total || 0).toLocaleString()}`
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
        </div>
      )}

      {/* Activity Tab */}
      {activeTab === 'activity' && (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Time</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Employee</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Action</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Category</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden md:table-cell">Terminal</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {activityLoading ? (
                  <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-500">Loading...</td></tr>
                ) : activityData?.items?.length === 0 ? (
                  <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-500">No activity records found</td></tr>
                ) : (
                  activityData?.items?.map((a: any) => (
                    <tr key={a.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm text-gray-600 whitespace-nowrap">{a.time || '-'}</td>
                      <td className="px-4 py-3 text-sm"><button onClick={() => { const emp = data?.employees?.find(e => e.name === a.employee); if (emp) setSelectedEmployee(emp); else navigate(`/transactions?employee=${encodeURIComponent(a.employee)}`) }} className="font-medium text-blue-600 hover:text-blue-700 hover:underline text-left">{a.employee}</button></td>
                      <td className="px-4 py-3 text-sm">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          a.action?.includes('Login') ? 'bg-green-100 text-green-700' :
                          a.action?.includes('Logout') ? 'bg-red-100 text-red-700' :
                          a.action?.includes('Sale') ? 'bg-blue-100 text-blue-700' :
                          'bg-gray-100 text-gray-700'
                        }`}>
                          {a.action}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600 hidden sm:table-cell">{a.category || '-'}</td>
                      <td className="px-4 py-3 text-sm text-gray-500 hidden md:table-cell">{a.terminal || '-'}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          <div className="px-4 py-3 border-t bg-gray-50 flex flex-col sm:flex-row items-center justify-between gap-2">
            <div className="text-sm text-gray-500">
              {(activityData?.total || 0) > 0
                ? `Showing ${page * limit + 1} - ${Math.min((page + 1) * limit, activityData?.total || 0)} of ${(activityData?.total || 0).toLocaleString()}`
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
        </div>
      )}

      {/* Time Clock Tab */}
      {activeTab === 'timeclock' && (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Date</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Employee</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Clock In</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Terminal In</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Clock Out</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase hidden sm:table-cell">Terminal Out</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Hours</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {timeClockLoading ? (
                  <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-500">Loading...</td></tr>
                ) : timeClockData?.items?.length === 0 ? (
                  <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-500">No time clock records found</td></tr>
                ) : (
                  timeClockData?.items?.map((t: any) => (
                    <tr key={t.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm text-gray-600">{t.date}</td>
                      <td className="px-4 py-3 text-sm"><button onClick={() => { const emp = data?.employees?.find(e => e.name === t.employee); if (emp) setSelectedEmployee(emp); else navigate(`/transactions?employee=${encodeURIComponent(t.employee)}`) }} className="font-medium text-blue-600 hover:text-blue-700 hover:underline text-left">{t.employee}</button></td>
                      <td className="px-4 py-3 text-sm text-green-600 whitespace-nowrap">{t.clock_in || '-'}</td>
                      <td className="px-4 py-3 text-sm text-gray-500 hidden sm:table-cell">{t.terminal_in || '-'}</td>
                      <td className="px-4 py-3 text-sm text-red-600 whitespace-nowrap">{t.clock_out || '-'}</td>
                      <td className="px-4 py-3 text-sm text-gray-500 hidden sm:table-cell">{t.terminal_out || '-'}</td>
                      <td className="px-4 py-3 text-sm font-medium text-gray-900">{t.time_clocked_in || '-'}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          <div className="px-4 py-3 border-t bg-gray-50 flex flex-col sm:flex-row items-center justify-between gap-2">
            <div className="text-sm text-gray-500">
              {(timeClockData?.total || 0) > 0
                ? `Showing ${page * limit + 1} - ${Math.min((page + 1) * limit, timeClockData?.total || 0)} of ${(timeClockData?.total || 0).toLocaleString()}`
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
        </div>
      )}

      {/* Employee Detail Modal */}
      {selectedEmployee && (
        <EmployeeDetailModal employee={selectedEmployee} onClose={() => setSelectedEmployee(null)} onViewTransactions={handleViewTransactions} />
      )}
    </div>
  )
}

function EmployeeDetailModal({ employee, onClose, onViewTransactions }: { employee: Employee; onClose: () => void; onViewTransactions: (name: string) => void }) {
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleEscape)
    return () => window.removeEventListener('keydown', handleEscape)
  }, [onClose])

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-white rounded-xl shadow-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
              <UserCheck className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900">{employee.name}</h2>
              <p className="text-sm text-gray-500">Employee Details</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-lg transition-colors" aria-label="Close">
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>
        <div className="p-6 space-y-6">
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-blue-50 rounded-lg p-4">
              <p className="text-sm text-blue-600 font-medium">Transactions</p>
              <p className="text-2xl font-bold text-blue-900">{employee.transaction_count.toLocaleString()}</p>
            </div>
            <div className="bg-green-50 rounded-lg p-4">
              <p className="text-sm text-green-600 font-medium">Net Sales</p>
              <p className="text-2xl font-bold text-green-900">{formatMoney(employee.net_sales)}</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-600 font-medium">Gross Sales</p>
              <p className="text-xl font-bold text-gray-900">{formatMoney(employee.total_sales)}</p>
            </div>
            <div className="bg-red-50 rounded-lg p-4">
              <p className="text-sm text-red-600 font-medium">Refunds</p>
              <p className="text-xl font-bold text-red-900">{formatMoney(employee.total_refunds)}</p>
            </div>
          </div>
          <div className="bg-purple-50 rounded-lg p-4">
            <p className="text-sm text-purple-600 font-medium">Average Transaction</p>
            <p className="text-2xl font-bold text-purple-900">{formatMoney(employee.average_transaction)}</p>
          </div>
          <button
            onClick={() => onViewTransactions(employee.name)}
            className="w-full btn btn-primary flex items-center justify-center gap-2"
          >
            <Receipt className="w-5 h-5" />
            View All Transactions
          </button>
        </div>
      </div>
    </div>
  )
}
