import { useEffect, useState, useCallback, useRef } from 'react'
import { api } from '../lib/api'
import NavBar from '../components/NavBar'

function monthLabel(month) {
  const [y, m] = month.split('-').map(Number)
  return new Date(y, m - 1, 1).toLocaleDateString(undefined, { month: 'long', year: 'numeric' })
}

function shiftMonth(month, delta) {
  const [y, m] = month.split('-').map(Number)
  const d = new Date(y, m - 1 + delta, 1)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}

function currency(n) {
  return `₹${Number(n).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`
}

function todayISO() {
  return new Date().toISOString().slice(0, 10)
}

export default function Transactions() {
  const [month, setMonth] = useState(() => {
    const d = new Date()
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
  })
  const [categories, setCategories] = useState([])
  const [purchases, setPurchases] = useState([])
  const [form, setForm] = useState({ category_id: '', name: '', amount: '', date: todayISO() })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const hasLoadedOnce = useRef(false)

  // Only the very first fetch shows the full "Loading…" state. Adding a
  // purchase, deleting one, or flipping months all call load() again, but
  // blanking the whole list back to a bare loading message every time --
  // even though the old data was still perfectly valid a moment ago -- is
  // exactly what made every add feel like "the page reloaded".
  const load = useCallback(async () => {
    if (!hasLoadedOnce.current) setLoading(true)
    setError('')
    try {
      const [cats, p] = await Promise.all([api.listCategories(), api.listPurchases(month)])
      setCategories(cats)
      setPurchases(p)
      // NOTE: categories from /categories use `id`, not `category_id` (that
      // field only exists on month-summary rows). Using the wrong key here
      // left form.category_id as '' even though the <select> visually showed
      // the first category -- so submitting without touching the dropdown
      // silently did nothing until you picked a different option and back.
      setForm((f) => ({ ...f, category_id: f.category_id || cats[0]?.id || '' }))
      hasLoadedOnce.current = true
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [month])

  useEffect(() => { load() }, [load])

  async function handleAdd(e) {
    e.preventDefault()
    const amount = parseFloat(form.amount)
    if (!form.category_id || !form.name.trim() || isNaN(amount)) return
    try {
      const isoDate = form.date ? new Date(form.date + 'T12:00:00').toISOString() : undefined
      await api.createPurchase(form.category_id, form.name.trim(), amount, isoDate)
      setForm((f) => ({ ...f, name: '', amount: '', date: todayISO() }))
      await load()
    } catch (e) {
      setError(e.message)
    }
  }

  const total = purchases.reduce((sum, p) => sum + p.amount, 0)

  return (
    <div className="min-h-screen bg-paper pb-24">
      <NavBar />
      <main className="max-w-3xl mx-auto px-4 pt-6">
        <div className="flex items-center justify-between mb-6">
          <button
            onClick={() => setMonth((m) => shiftMonth(m, -1))}
            className="h-9 w-9 rounded-full border border-line flex items-center justify-center text-subink hover:border-turmeric hover:text-turmeric"
            aria-label="Previous month"
          >←</button>
          <h2 className="font-display text-2xl text-ink">{monthLabel(month)}</h2>
          <button
            onClick={() => setMonth((m) => shiftMonth(m, 1))}
            className="h-9 w-9 rounded-full border border-line flex items-center justify-center text-subink hover:border-turmeric hover:text-turmeric"
            aria-label="Next month"
          >→</button>
        </div>

        {error && <p className="text-clay text-sm mb-4">{error}</p>}

        <form onSubmit={handleAdd} className="rounded-md bg-card border border-line p-4 mb-6 space-y-3">
          <select
            value={form.category_id}
            onChange={(e) => setForm((f) => ({ ...f, category_id: e.target.value }))}
            className="w-full rounded border border-line px-3 py-2 text-sm outline-none focus:border-turmeric"
          >
            {categories.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
          <div className="flex gap-2">
            <input
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              placeholder="What did you buy?"
              className="flex-1 rounded border border-line px-3 py-2 text-sm outline-none focus:border-turmeric"
            />
            <input
              value={form.amount}
              onChange={(e) => setForm((f) => ({ ...f, amount: e.target.value }))}
              type="number"
              placeholder="Amount"
              className="w-28 rounded border border-line px-3 py-2 text-sm outline-none focus:border-turmeric"
            />
            <input
              value={form.date}
              onChange={(e) => setForm((f) => ({ ...f, date: e.target.value }))}
              type="date"
              className="rounded border border-line px-2 py-2 text-sm outline-none focus:border-turmeric"
              title="Defaults to today -- change it to log a past purchase"
            />
          </div>
          <button type="submit" className="w-full rounded bg-ink text-card py-2 text-sm font-medium hover:bg-turmeric">
            Add purchase
          </button>
        </form>

        {loading ? (
          <p className="text-subink text-sm">Loading…</p>
        ) : (
          <div className="rounded-md bg-card border border-line p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm uppercase tracking-wide text-subink">This month's purchases</h3>
              <span className="font-mono text-sm text-ink">{currency(total)}</span>
            </div>
            {purchases.length === 0 && <p className="text-sm text-subink italic">Nothing logged yet this month.</p>}
            <div className="space-y-2">
              {purchases.map((p) => (
                <div key={p.id} className="flex items-center justify-between text-sm py-2 border-b border-line last:border-0">
                  <div>
                    <p className="text-ink">{p.name}</p>
                    <p className="text-xs text-subink">{new Date(p.date).toLocaleDateString()}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-ink">{currency(p.amount)}</span>
                    <button
                      onClick={async () => { await api.deletePurchase(p.id); await load() }}
                      className="text-subink hover:text-clay text-xs"
                      aria-label="Delete purchase"
                    >✕</button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
