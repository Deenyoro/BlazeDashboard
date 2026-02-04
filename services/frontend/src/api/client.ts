import axios from 'axios'

export const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Function to set the auth token for all requests
export const setAuthToken = (token: string | undefined) => {
  if (token) {
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`
  } else {
    delete api.defaults.headers.common['Authorization']
  }
}

// Types
export interface Transaction {
  id: string
  blaze_trans_id: string
  trans_no: string | null
  date: string
  shop: string | null
  company: string | null
  trans_type: string | null
  trans_status: string | null
  queue_type: string | null
  order_source: string | null
  gross_sales: number
  net_sales: number
  total_tax: number
  total_due: number
  tips: number
  cogs: number
  pre_tax_discounts: number
  after_tax_discount: number
  payment_type: string | null
  payment_tendered: number
  sold_by_name: string | null
  created_by_name: string | null
  terminal: string | null
  region: string | null
  delivery_city: string | null
  loyalty_points_spent: number
  loyalty_points_earned: number
  compliance_system: string | null
  compliance_order_id: string | null
}

export interface TransactionListResponse {
  transactions: Transaction[]
  total: number
  skip: number
  limit: number
}

export interface TransactionStats {
  total_transactions: number
  total_sales: number
  total_refunds: number
  net_revenue: number
  total_tax_collected: number
  total_tips: number
  total_discounts: number
  average_transaction: number
  total_cogs: number
  gross_margin: number
}

export interface DailySales {
  date: string
  transaction_count: number
  gross_sales: number
  net_sales: number
  total_tax: number
  tips: number
  refunds: number
}

export interface SalesOverview {
  period_start: string
  period_end: string
  stats: TransactionStats
  daily_breakdown: DailySales[]
  by_payment_type: Record<string, { count: number; total: number }>
  by_queue_type: Record<string, { count: number; total: number }>
  by_employee: Record<string, { count: number; total: number }>
  top_customers: Array<{
    name: string
    member_id: string
    transactions: number
    total_spent: number
  }>
}

export interface IngestionStatus {
  transactions: number
  members: number
  employees: number
  date_range: {
    start: string | null
    end: string | null
  }
  by_type: Record<string, number>
}

export interface ProductSale {
  id: string
  trans_no: string
  sale_date: string
  product_name: string | null
  sku: string | null
  category: string | null
  brand: string | null
  vendor: string | null
  batch: string | null
  is_cannabis: boolean
  quantity: number
  retail_price: number
  effective_retail_price: number
  net_sales: number
  cogs: number
  product_discounts: number
  cart_discounts: number
  total_discount: number
  total_tax: number
  metrc_tag: string | null
  metrc_sale_id: string | null
  promotions: string | null
}

export interface TransactionDetail {
  id: string
  blaze_trans_id: string
  trans_no: string | null
  date: string
  created_date: string | null
  prepared_date: string | null
  packed_date: string | null
  shop: string | null
  company: string | null
  terminal: string | null
  region: string | null
  delivery_city: string | null
  trans_type: string | null
  trans_status: string | null
  queue_type: string | null
  order_source: string | null
  member_name: string | null
  member_group: string | null
  consumer_tax_type: string | null
  retail_value: number
  gross_sales: number
  net_sales: number
  net_sales_wo_fees: number
  delivery_fees: number
  pre_tax_discounts: number
  after_tax_discount: number
  product_promotions: string | null
  cart_promotions: string | null
  discount_notes: string | null
  pre_al_excise_tax: number
  pre_nal_excise_tax: number
  city_tax: number
  county_tax: number
  state_tax: number
  federal_tax: number
  total_tax: number
  total_due: number
  tips: number
  cogs: number
  payment_type: string | null
  blazepay_id: string | null
  payment_tendered: number
  cash_change: number
  change_due: number
  sold_by_name: string | null
  created_by_name: string | null
  prepared_by: string | null
  packed_by: string | null
  marketing_source: string | null
  order_tags: string | null
  loyalty_points_spent: number
  loyalty_points_earned: number
  compliance_system: string | null
  compliance_order_id: string | null
  items: ProductSale[]
  item_count: number
}

// API functions
export const transactionApi = {
  list: async (params?: {
    skip?: number
    limit?: number
    start_date?: string
    end_date?: string
    trans_type?: string
    queue_type?: string
    payment_type?: string
    employee?: string
    search?: string
    min_amount?: number
    max_amount?: number
  }): Promise<TransactionListResponse> => {
    const { data } = await api.get('/transactions', { params })
    return data
  },

  getStats: async (params?: {
    start_date?: string
    end_date?: string
  }): Promise<TransactionStats> => {
    const { data } = await api.get('/transactions/stats', { params })
    return data
  },

  getOverview: async (params?: {
    start_date?: string
    end_date?: string
  }): Promise<SalesOverview> => {
    const { data } = await api.get('/transactions/overview', { params })
    return data
  },

  getById: async (id: string): Promise<Transaction> => {
    const { data } = await api.get(`/transactions/${id}`)
    return data
  },

  getDetail: async (transNo: string): Promise<TransactionDetail> => {
    const { data } = await api.get(`/transactions/detail/${transNo}`)
    return data
  },
}

export const ingestionApi = {
  getStatus: async (): Promise<IngestionStatus> => {
    const { data } = await api.get('/ingest/status')
    return data
  },

  getAllStatus: async () => {
    const { data } = await api.get('/ingest/all/status')
    return data
  },

  triggerIngest: async (): Promise<{ status: string; inserted: number; errors: number }> => {
    const { data } = await api.post('/ingest/csv?use_default=true')
    return data
  },

  triggerIngestAll: async () => {
    const { data } = await api.post('/ingest/all')
    return data
  },
}

export const customersApi = {
  list: async (params?: { skip?: number; limit?: number; search?: string; status?: string }) => {
    const { data } = await api.get('/customers', { params })
    return data
  },
  getStats: async () => {
    const { data } = await api.get('/customers/stats')
    return data
  },
  getPerformance: async (params?: { skip?: number; limit?: number; search?: string }) => {
    const { data } = await api.get('/customers/performance', { params })
    return data
  },
  getInactive: async (params?: { skip?: number; limit?: number; search?: string }) => {
    const { data } = await api.get('/customers/inactive', { params })
    return data
  },
  getMarketing: async (params?: { skip?: number; limit?: number; search?: string }) => {
    const { data } = await api.get('/customers/marketing', { params })
    return data
  },
}

export const productsApi = {
  list: async (params?: { skip?: number; limit?: number; search?: string; category?: string; brand?: string }) => {
    const { data } = await api.get('/products', { params })
    return data
  },
  getStats: async () => {
    const { data } = await api.get('/products/stats')
    return data
  },
  getBatches: async (params?: { skip?: number; limit?: number; search?: string }) => {
    const { data } = await api.get('/products/batches', { params })
    return data
  },
  getVendors: async (params?: { skip?: number; limit?: number; search?: string }) => {
    const { data } = await api.get('/products/vendors', { params })
    return data
  },
  getByVendor: async (params?: { skip?: number; limit?: number; vendor?: string }) => {
    const { data } = await api.get('/products/by-vendor', { params })
    return data
  },
  getSellByExpire: async (params?: { skip?: number; limit?: number; category?: string }) => {
    const { data } = await api.get('/products/sell-by-expire', { params })
    return data
  },
}

export const reportsApi = {
  getProfitLoss: async (params?: { skip?: number; limit?: number; start_date?: string; end_date?: string }) => {
    const { data } = await api.get('/reports/profit-loss', { params })
    return data
  },
  getSalesByCity: async () => {
    const { data } = await api.get('/reports/sales/by-city')
    return data
  },
  getSalesByHour: async () => {
    const { data } = await api.get('/reports/sales/by-hour')
    return data
  },
  getSalesByProduct: async (params?: { skip?: number; limit?: number; category?: string; search?: string }) => {
    const { data } = await api.get('/reports/sales/by-product', { params })
    return data
  },
  getSalesByCategory: async () => {
    const { data } = await api.get('/reports/sales/by-product-category')
    return data
  },
  getSalesByVendor: async () => {
    const { data } = await api.get('/reports/sales/by-vendor')
    return data
  },
  getSalesByConsumerType: async () => {
    const { data } = await api.get('/reports/sales/by-consumer-type')
    return data
  },
  getDeliverySales: async (params?: { skip?: number; limit?: number; start_date?: string; end_date?: string }) => {
    const { data } = await api.get('/reports/delivery-sales', { params })
    return data
  },
  getCanceledVoid: async (params?: { skip?: number; limit?: number; start_date?: string; end_date?: string }) => {
    const { data } = await api.get('/reports/canceled-void', { params })
    return data
  },
  getPromotions: async (params?: { skip?: number; limit?: number; start_date?: string; end_date?: string }) => {
    const { data } = await api.get('/reports/promotions', { params })
    return data
  },
}

export const employeesApi = {
  list: async () => {
    const { data } = await api.get('/employees')
    return data
  },
  getPerformance: async (params?: { skip?: number; limit?: number; start_date?: string; end_date?: string; employee?: string }) => {
    const { data } = await api.get('/employees/performance', { params })
    return data
  },
  getActivity: async (params?: { skip?: number; limit?: number; start_date?: string; end_date?: string; employee?: string }) => {
    const { data } = await api.get('/employees/activity', { params })
    return data
  },
  getTimeClock: async (params?: { skip?: number; limit?: number; start_date?: string; end_date?: string; employee?: string }) => {
    const { data } = await api.get('/employees/time-clock', { params })
    return data
  },
}
