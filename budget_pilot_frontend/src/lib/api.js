import { supabase } from './supabaseClient'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

async function request(path, options = {}) {
  const { data: { session } } = await supabase.auth.getSession()
  const token = session?.access_token

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  })

  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail || detail
    } catch {
      // response had no JSON body
    }
    throw new Error(detail)
  }

  if (res.status === 204) return null
  return res.json()
}

export const api = {
  listCategories: (includeArchived = false) =>
    request(`/categories${includeArchived ? '?include_archived=true' : ''}`),
  createCategory: (name, type = 'expense') =>
    request('/categories', { method: 'POST', body: JSON.stringify({ name, type }) }),
  renameCategory: (id, name) =>
    request(`/categories/${id}`, { method: 'PATCH', body: JSON.stringify({ name }) }),
  archiveCategory: (id) => request(`/categories/${id}/archive`, { method: 'POST' }),
  restoreCategory: (id) => request(`/categories/${id}/restore`, { method: 'POST' }),
  deleteCategory: (id, cascade = false) =>
    request(`/categories/${id}${cascade ? '?cascade=true' : ''}`, { method: 'DELETE' }),
  listArchivedCategories: () => request('/categories/archived'),

  getMonth: (month) => request(`/months/${month}`),
  getMonthSummary: (month) => request(`/months/${month}/summary`),
  upsertMonthEntry: (month, categoryId, body) =>
    request(`/months/${month}/${categoryId}`, { method: 'PUT', body: JSON.stringify(body) }),
  cloneMonth: (toMonth, fromMonth) =>
    request(`/months/${toMonth}/clone-from/${fromMonth}`, { method: 'POST' }),
  pushLeftoverToSavings: (month, savingsCategoryId) =>
    request(`/months/${month}/push-leftover`, {
      method: 'POST',
      body: JSON.stringify({ savings_category_id: savingsCategoryId }),
    }),

  listIncome: (month) => request(`/months/${month}/income`),
  addIncome: (month, source, amount) =>
    request(`/months/${month}/income`, { method: 'POST', body: JSON.stringify({ source, amount }) }),
  updateIncome: (incomeId, body) =>
    request(`/months/income/${incomeId}`, { method: 'PATCH', body: JSON.stringify(body) }),
  deleteIncome: (incomeId) => request(`/months/income/${incomeId}`, { method: 'DELETE' }),

  listPurchases: (month, categoryId) => {
    const params = new URLSearchParams()
    if (month) params.set('month', month)
    if (categoryId) params.set('category_id', categoryId)
    const qs = params.toString()
    return request(`/purchases${qs ? `?${qs}` : ''}`)
  },
  createPurchase: (categoryId, name, amount, date) =>
    request('/purchases', {
      method: 'POST',
      body: JSON.stringify({ category_id: categoryId, name, amount, ...(date ? { date } : {}) }),
    }),
  deletePurchase: (id) => request(`/purchases/${id}`, { method: 'DELETE' }),

  getHistory: (endMonth, months = 12) => request(`/reports/history?end_month=${endMonth}&months=${months}`),
  getSavingsLifetime: () => request('/reports/savings-lifetime'),

  deleteAccount: (confirmEmail) =>
    request('/account', { method: 'DELETE', body: JSON.stringify({ confirm_email: confirmEmail }) }),
}
