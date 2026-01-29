import { useQuery } from '@tanstack/react-query'
import { Link, useNavigate } from 'react-router-dom'
import { format } from 'date-fns'
import {
  DollarSign,
  Receipt,
  Users,
  TrendingUp,
  ArrowUpRight,
  ChevronRight,
} from 'lucide-react'
import { transactionApi, ingestionApi } from '../api/client'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts'

function formatMoney(val: number) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(val)
}

const COLORS = ['#16a34a', '#2563eb', '#dc2626', '#f59e0b', '#8b5cf6', '#ec4899']

export default function Dashboard() {
  const navigate = useNavigate()
  const { data: status, isLoading: statusLoading } = useQuery({
    queryKey: ['ingestion-status'],
    queryFn: ingestionApi.getStatus,
  })

  const { data: overview, isLoading: overviewLoading } = useQuery({
    queryKey: ['overview'],
    queryFn: () => transactionApi.getOverview(),
  })

  const { data: recentTransactions } = useQuery({
    queryKey: ['recent-transactions'],
    queryFn: () => transactionApi.list({ limit: 5 }),
  })

  const isLoading = statusLoading || overviewLoading

  const stats = overview?.stats
  const dailyData = overview?.daily_breakdown?.slice(-14) || []

  const paymentData = Object.entries(overview?.by_payment_type || {}).map(([name, data]) => ({
    name,
    value: data.total,
    count: data.count,
  }))

  // Queue data available via overview?.by_queue_type if needed

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-500">
            {status?.date_range?.start && status?.date_range?.end
              ? `Data from ${format(new Date(status.date_range.start), 'MMM d, yyyy')} to ${format(new Date(status.date_range.end), 'MMM d, yyyy')}`
              : 'Sales analytics overview'}
          </p>
        </div>
        <div className="flex gap-2">
          <Link to="/transactions" className="btn btn-secondary">
            View All Transactions
          </Link>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card p-5">
          <div className="flex items-center justify-between">
            <div className="p-2 bg-green-100 rounded-lg">
              <DollarSign className="w-5 h-5 text-green-600" />
            </div>
            {stats && stats.gross_margin > 0 && (
              <span className="text-xs font-medium text-green-600 flex items-center">
                <ArrowUpRight className="w-3 h-3" />
                {stats.gross_margin}%
              </span>
            )}
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold text-gray-900">
              {isLoading ? '...' : formatMoney(stats?.net_revenue || 0)}
            </div>
            <div className="text-sm text-gray-500">Net Revenue</div>
          </div>
        </div>

        <div className="card p-5">
          <div className="flex items-center justify-between">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Receipt className="w-5 h-5 text-blue-600" />
            </div>
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold text-gray-900">
              {isLoading ? '...' : (stats?.total_transactions || 0).toLocaleString()}
            </div>
            <div className="text-sm text-gray-500">Total Transactions</div>
          </div>
        </div>

        <div className="card p-5">
          <div className="flex items-center justify-between">
            <div className="p-2 bg-purple-100 rounded-lg">
              <TrendingUp className="w-5 h-5 text-purple-600" />
            </div>
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold text-gray-900">
              {isLoading ? '...' : formatMoney(stats?.average_transaction || 0)}
            </div>
            <div className="text-sm text-gray-500">Avg Transaction</div>
          </div>
        </div>

        <div className="card p-5">
          <div className="flex items-center justify-between">
            <div className="p-2 bg-orange-100 rounded-lg">
              <Users className="w-5 h-5 text-orange-600" />
            </div>
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold text-gray-900">
              {statusLoading ? '...' : (status?.members || 0).toLocaleString()}
            </div>
            <div className="text-sm text-gray-500">Customers</div>
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Daily Sales Chart */}
        <div className="card p-5">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Daily Sales (Last 14 Days)</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={dailyData}>
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
                <Bar dataKey="gross_sales" fill="#16a34a" name="Gross Sales" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Payment Types */}
        <div className="card p-5">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Payment Methods</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={paymentData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                  {paymentData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(val: number) => formatMoney(val)} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Bottom Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Transactions */}
        <div className="card">
          <div className="px-5 py-4 border-b border-gray-200 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Recent Transactions</h2>
            <Link to="/transactions" className="text-sm text-primary-600 hover:text-primary-700 flex items-center">
              View all <ChevronRight className="w-4 h-4" />
            </Link>
          </div>
          <div className="divide-y divide-gray-100">
            {recentTransactions?.transactions?.map((t) => (
              <div key={t.id} onClick={() => navigate(`/transactions?search=${encodeURIComponent(t.trans_no || '')}`)} className="px-5 py-3 flex items-center justify-between hover:bg-gray-50 cursor-pointer transition-colors">
                <div>
                  <div className="font-medium text-emerald-600">#{t.trans_no}</div>
                  <div className="text-sm text-gray-500">
                    {format(new Date(t.date), 'MMM d, h:mm a')} • {t.payment_type}
                  </div>
                </div>
                <div className="text-right">
                  <div className={`font-medium ${t.trans_type === 'Refund' ? 'text-red-600' : 'text-gray-900'}`}>
                    {t.trans_type === 'Refund' ? '-' : ''}{formatMoney(Math.abs(t.total_due))}
                  </div>
                  <div className="text-sm text-gray-500">{t.queue_type}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Top Employees */}
        <div className="card">
          <div className="px-5 py-4 border-b border-gray-200 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Top Employees</h2>
            <Link to="/employees" className="text-sm text-primary-600 hover:text-primary-700 flex items-center">
              View all <ChevronRight className="w-4 h-4" />
            </Link>
          </div>
          <div className="divide-y divide-gray-100">
            {Object.entries(overview?.by_employee || {})
              .slice(0, 5)
              .map(([name, data]) => (
                <div key={name} onClick={() => navigate(`/transactions?employee=${encodeURIComponent(name)}`)} className="px-5 py-3 flex items-center justify-between hover:bg-gray-50 cursor-pointer transition-colors">
                  <div>
                    <div className="font-medium text-blue-600">{name}</div>
                    <div className="text-sm text-gray-500">{data.count} transactions</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-gray-900">{formatMoney(data.total)}</span>
                    <ChevronRight className="w-4 h-4 text-gray-400" />
                  </div>
                </div>
              ))}
          </div>
        </div>
      </div>

      {/* Quick Stats Footer */}
      <div className="card p-5 bg-gray-50">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
          <div>
            <div className="text-2xl font-bold text-gray-900">
              {formatMoney(stats?.total_tax_collected || 0)}
            </div>
            <div className="text-sm text-gray-500">Tax Collected</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-red-600">
              {formatMoney(stats?.total_refunds || 0)}
            </div>
            <div className="text-sm text-gray-500">Refunds</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-gray-900">
              {formatMoney(stats?.total_discounts || 0)}
            </div>
            <div className="text-sm text-gray-500">Discounts Given</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-gray-900">
              {formatMoney(stats?.total_cogs || 0)}
            </div>
            <div className="text-sm text-gray-500">COGS</div>
          </div>
        </div>
      </div>
    </div>
  )
}
