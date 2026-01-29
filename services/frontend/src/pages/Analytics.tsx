import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { format, subDays, startOfMonth, endOfMonth, subMonths } from 'date-fns'
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts'
import { Calendar, TrendingUp, DollarSign, Receipt } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { transactionApi } from '../api/client'

function formatMoney(val: number) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(val)
}

const COLORS = ['#16a34a', '#2563eb', '#dc2626', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16']

type DatePreset = 'last7' | 'last30' | 'thisMonth' | 'lastMonth' | 'custom'

export default function Analytics() {
  const navigate = useNavigate()
  const [preset, setPreset] = useState<DatePreset>('last30')
  const [customStart, setCustomStart] = useState('')
  const [customEnd, setCustomEnd] = useState('')

  const getDateRange = () => {
    const today = new Date()
    switch (preset) {
      case 'last7':
        return {
          start_date: format(subDays(today, 7), 'yyyy-MM-dd'),
          end_date: format(today, 'yyyy-MM-dd'),
        }
      case 'last30':
        return {
          start_date: format(subDays(today, 30), 'yyyy-MM-dd'),
          end_date: format(today, 'yyyy-MM-dd'),
        }
      case 'thisMonth':
        return {
          start_date: format(startOfMonth(today), 'yyyy-MM-dd'),
          end_date: format(endOfMonth(today), 'yyyy-MM-dd'),
        }
      case 'lastMonth':
        const lastMonth = subMonths(today, 1)
        return {
          start_date: format(startOfMonth(lastMonth), 'yyyy-MM-dd'),
          end_date: format(endOfMonth(lastMonth), 'yyyy-MM-dd'),
        }
      case 'custom':
        return {
          start_date: customStart || undefined,
          end_date: customEnd || undefined,
        }
      default:
        return {}
    }
  }

  const dateRange = getDateRange()

  const { data: overview, isLoading } = useQuery({
    queryKey: ['analytics-overview', dateRange],
    queryFn: () => transactionApi.getOverview(dateRange),
    enabled: preset !== 'custom' || (!!customStart && !!customEnd),
  })

  const dailyData = overview?.daily_breakdown || []
  const stats = overview?.stats

  const paymentData = Object.entries(overview?.by_payment_type || {}).map(([name, data]) => ({
    name,
    value: data.total,
    count: data.count,
  }))

  const queueData = Object.entries(overview?.by_queue_type || {}).map(([name, data]) => ({
    name,
    value: data.total,
    count: data.count,
  }))

  const employeeData = Object.entries(overview?.by_employee || {})
    .map(([name, data]) => ({
      name: name.split(' ')[0],
      fullName: name,
      total: data.total,
      count: data.count,
    }))
    .sort((a, b) => b.total - a.total)
    .slice(0, 8)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
          <p className="text-gray-500">Detailed sales analysis and trends</p>
        </div>
      </div>

      {/* Date Range Selector */}
      <div className="card p-4">
        <div className="flex flex-wrap items-center gap-2">
          <Calendar className="w-5 h-5 text-gray-400" />
          <span className="text-sm font-medium text-gray-700 mr-2">Period:</span>
          {[
            { key: 'last7', label: 'Last 7 Days' },
            { key: 'last30', label: 'Last 30 Days' },
            { key: 'thisMonth', label: 'This Month' },
            { key: 'lastMonth', label: 'Last Month' },
            { key: 'custom', label: 'Custom' },
          ].map((p) => (
            <button
              key={p.key}
              onClick={() => setPreset(p.key as DatePreset)}
              className={`px-3 py-1.5 text-sm rounded-lg font-medium transition-colors ${
                preset === p.key
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>
        {preset === 'custom' && (
          <div className="mt-4 flex gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Start Date
              </label>
              <input
                type="date"
                value={customStart}
                onChange={(e) => setCustomStart(e.target.value)}
                className="input"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                End Date
              </label>
              <input
                type="date"
                value={customEnd}
                onChange={(e) => setCustomEnd(e.target.value)}
                className="input"
              />
            </div>
          </div>
        )}
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="card p-4">
          <div className="flex items-center gap-2 text-gray-500 mb-1">
            <DollarSign className="w-4 h-4" />
            <span className="text-xs font-medium">Net Revenue</span>
          </div>
          <div className="text-xl font-bold text-gray-900">
            {isLoading ? '...' : formatMoney(stats?.net_revenue || 0)}
          </div>
        </div>
        <div className="card p-4">
          <div className="flex items-center gap-2 text-gray-500 mb-1">
            <Receipt className="w-4 h-4" />
            <span className="text-xs font-medium">Transactions</span>
          </div>
          <div className="text-xl font-bold text-gray-900">
            {isLoading ? '...' : (stats?.total_transactions || 0).toLocaleString()}
          </div>
        </div>
        <div className="card p-4">
          <div className="flex items-center gap-2 text-gray-500 mb-1">
            <TrendingUp className="w-4 h-4" />
            <span className="text-xs font-medium">Avg Transaction</span>
          </div>
          <div className="text-xl font-bold text-gray-900">
            {isLoading ? '...' : formatMoney(stats?.average_transaction || 0)}
          </div>
        </div>
        <div className="card p-4">
          <div className="flex items-center gap-2 text-gray-500 mb-1">
            <DollarSign className="w-4 h-4 text-red-500" />
            <span className="text-xs font-medium">Refunds</span>
          </div>
          <div className="text-xl font-bold text-red-600">
            {isLoading ? '...' : formatMoney(stats?.total_refunds || 0)}
          </div>
        </div>
        <div className="card p-4">
          <div className="flex items-center gap-2 text-gray-500 mb-1">
            <TrendingUp className="w-4 h-4 text-green-500" />
            <span className="text-xs font-medium">Gross Margin</span>
          </div>
          <div className="text-xl font-bold text-green-600">
            {isLoading ? '...' : `${stats?.gross_margin?.toFixed(1) || 0}%`}
          </div>
        </div>
      </div>

      {/* Sales Trend Chart */}
      <div className="card p-5">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Sales Trend</h2>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={dailyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="date"
                tickFormatter={(val) => format(new Date(val), 'MM/dd')}
                fontSize={12}
              />
              <YAxis
                tickFormatter={(val) => `$${(val / 1000).toFixed(0)}k`}
                fontSize={12}
              />
              <Tooltip
                formatter={(val: number) => formatMoney(val)}
                labelFormatter={(val) => format(new Date(val), 'MMM d, yyyy')}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="gross_sales"
                stroke="#16a34a"
                name="Gross Sales"
                strokeWidth={2}
              />
              <Line
                type="monotone"
                dataKey="net_sales"
                stroke="#2563eb"
                name="Net Sales"
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Payment Types Pie */}
        <div className="card p-5">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Sales by Payment Type</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={paymentData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {paymentData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(val: number) => formatMoney(val)} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Queue Types Pie */}
        <div className="card p-5">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Sales by Queue Type</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={queueData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {queueData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(val: number) => formatMoney(val)} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Employee Performance */}
      <div className="card p-5">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Top Employees by Sales</h2>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={employeeData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" fontSize={12} />
              <YAxis
                tickFormatter={(val) => `$${(val / 1000).toFixed(0)}k`}
                fontSize={12}
              />
              <Tooltip
                formatter={(val: number) => formatMoney(val)}
                labelFormatter={(_, payload) => payload[0]?.payload?.fullName || ''}
              />
              <Bar dataKey="total" fill="#2563eb" name="Total Sales" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Top Customers */}
      {overview?.top_customers && overview.top_customers.length > 0 && (
        <div className="card">
          <div className="px-5 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Top Customers</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase">
                    Customer
                  </th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-gray-600 uppercase">
                    Transactions
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 uppercase">
                    Total Spent
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {overview.top_customers.map((c, i) => (
                  <tr key={c.member_id} onClick={() => navigate(`/customers?search=${encodeURIComponent(c.name)}`)} className="hover:bg-blue-50 cursor-pointer transition-colors">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center text-sm font-medium text-primary-700">
                          {i + 1}
                        </div>
                        <div className="font-medium text-emerald-600">{c.name}</div>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-center text-gray-600">
                      {c.transactions}
                    </td>
                    <td className="px-4 py-3 text-right font-medium text-gray-900">
                      {formatMoney(c.total_spent)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
