import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { format } from 'date-fns'
import {
  RefreshCw,
  Database,
  Calendar,
  Users,
  UserCheck,
  Receipt,
  CheckCircle,
  AlertCircle,
  Loader2,
} from 'lucide-react'
import { ingestionApi } from '../api/client'

export default function Settings() {
  const queryClient = useQueryClient()
  const [lastResult, setLastResult] = useState<{
    status: string
    inserted: number
    errors: number
  } | null>(null)

  const { data: status, isLoading } = useQuery({
    queryKey: ['ingestion-status'],
    queryFn: ingestionApi.getStatus,
  })

  const ingestMutation = useMutation({
    mutationFn: ingestionApi.triggerIngest,
    onSuccess: (data) => {
      setLastResult(data)
      queryClient.invalidateQueries({ queryKey: ['ingestion-status'] })
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      queryClient.invalidateQueries({ queryKey: ['overview'] })
    },
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-500">Manage data ingestion and system settings</p>
      </div>

      {/* Database Status */}
      <div className="card">
        <div className="px-5 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <Database className="w-5 h-5 text-primary-600" />
            Database Status
          </h2>
        </div>
        <div className="p-5">
          {isLoading ? (
            <div className="flex items-center gap-2 text-gray-500">
              <Loader2 className="w-5 h-5 animate-spin" />
              Loading status...
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="flex items-start gap-3">
                <div className="p-2 bg-green-100 rounded-lg">
                  <Receipt className="w-5 h-5 text-green-600" />
                </div>
                <div>
                  <div className="text-2xl font-bold text-gray-900">
                    {status?.transactions?.toLocaleString() || 0}
                  </div>
                  <div className="text-sm text-gray-500">Transactions</div>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Users className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <div className="text-2xl font-bold text-gray-900">
                    {status?.members?.toLocaleString() || 0}
                  </div>
                  <div className="text-sm text-gray-500">Customers</div>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <UserCheck className="w-5 h-5 text-purple-600" />
                </div>
                <div>
                  <div className="text-2xl font-bold text-gray-900">
                    {status?.employees?.toLocaleString() || 0}
                  </div>
                  <div className="text-sm text-gray-500">Employees</div>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="p-2 bg-orange-100 rounded-lg">
                  <Calendar className="w-5 h-5 text-orange-600" />
                </div>
                <div>
                  <div className="text-sm font-medium text-gray-900">
                    {status?.date_range?.start
                      ? format(new Date(status.date_range.start), 'MMM d, yyyy')
                      : 'N/A'}
                  </div>
                  <div className="text-sm text-gray-500">to</div>
                  <div className="text-sm font-medium text-gray-900">
                    {status?.date_range?.end
                      ? format(new Date(status.date_range.end), 'MMM d, yyyy')
                      : 'N/A'}
                  </div>
                </div>
              </div>
            </div>
          )}

          {status?.by_type && Object.keys(status.by_type).length > 0 && (
            <div className="mt-6 pt-6 border-t border-gray-200">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">
                Transactions by Type
              </h3>
              <div className="flex flex-wrap gap-3">
                {Object.entries(status.by_type).map(([type, count]) => (
                  <div
                    key={type}
                    className="px-3 py-2 bg-gray-100 rounded-lg text-sm"
                  >
                    <span className="font-medium text-gray-900">{type}:</span>{' '}
                    <span className="text-gray-600">{count.toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Data Ingestion */}
      <div className="card">
        <div className="px-5 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <RefreshCw className="w-5 h-5 text-primary-600" />
            Data Ingestion
          </h2>
        </div>
        <div className="p-5">
          <p className="text-gray-600 mb-4">
            Trigger a manual data ingestion from the default CSV file. This will process
            any new transactions and update the database.
          </p>

          <button
            onClick={() => ingestMutation.mutate()}
            disabled={ingestMutation.isPending}
            className="btn btn-primary disabled:opacity-50"
          >
            {ingestMutation.isPending ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Processing...
              </>
            ) : (
              <>
                <RefreshCw className="w-4 h-4 mr-2" />
                Run Ingestion
              </>
            )}
          </button>

          {lastResult && (
            <div
              className={`mt-4 p-4 rounded-lg flex items-start gap-3 ${
                lastResult.errors > 0
                  ? 'bg-yellow-50 border border-yellow-200'
                  : 'bg-green-50 border border-green-200'
              }`}
            >
              {lastResult.errors > 0 ? (
                <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0" />
              ) : (
                <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0" />
              )}
              <div>
                <div className="font-medium text-gray-900">
                  Ingestion Complete
                </div>
                <div className="text-sm text-gray-600 mt-1">
                  Inserted {lastResult.inserted.toLocaleString()} records
                  {lastResult.errors > 0 && (
                    <span className="text-yellow-700">
                      {' '}with {lastResult.errors} errors
                    </span>
                  )}
                </div>
              </div>
            </div>
          )}

          {ingestMutation.isError && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
              <div>
                <div className="font-medium text-red-900">Ingestion Failed</div>
                <div className="text-sm text-red-700 mt-1">
                  {(ingestMutation.error as Error)?.message || 'An error occurred'}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* About */}
      <div className="card p-5">
        <h2 className="text-lg font-semibold text-gray-900 mb-3">About BlazeDashboard</h2>
        <p className="text-gray-600">
          BlazeDashboard lets you view and explore exported Blaze POS data — transactions,
          customers, employees, inventory, and more — all in one place.
        </p>
        <div className="mt-4 text-sm text-gray-500">
          Version 1.0.0
        </div>
      </div>
    </div>
  )
}
