import { useEffect, useState, useCallback } from 'react'
import { api } from '../lib/api'

function currency(n) {
  return `₹${Number(n).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`
}

/**
 * "What's inside Food bucket" / "Personal care bucket" for the CURRENT month
 * only. This used to be its own reference_items table with no month at all --
 * that was the exact bug reported: delete an item in July, it vanished from
 * June too, because there was only ever one shared list.
 *
 * Fixed by not inventing a second data source at all: this is just purchases,
 * filtered to the Food/Personal category id + the month being viewed. Purchases
 * are already correctly month-scoped (each has its own date), so there's no
 * separate bug surface to maintain here.
 */
export default function ReferenceItems({ month, categories, onPurchaseChange }) {
  const [bucket, setBucket] = useState('food')
  const [items, setItems] = useState([])
  const [form, setForm] = useState({ name: '', amount: '' })
  const [expanded, setExpanded] = useState(false)
  const [error, setError] = useState('')

  const bucketCategory = categories.find((c) =>
    bucket === 'food' ? c.category_name.toLowerCase().includes('food') : c.category_name.toLowerCase().includes('personal')
  )

  const load = useCallback(async () => {
    if (!bucketCategory) { setItems([]); return }
    try {
      const data = await api.listPurchases(month, bucketCategory.category_id)
      setItems(data)
    } catch (e) {
      setError(e.message)
    }
  }, [month, bucketCategory?.category_id])

  useEffect(() => { load() }, [load])

  const total = items.reduce((sum, i) => sum + i.amount, 0)

  async function handleAdd(e) {
    e.preventDefault()
    const amount = parseFloat(form.amount)
    if (!bucketCategory || !form.name.trim() || isNaN(amount)) return
    try {
      await api.createPurchase(bucketCategory.category_id, form.name.trim(), amount)
      setForm({ name: '', amount: '' })
      await load()
      onPurchaseChange?.()
    } catch (e) {
      setError(e.message)
    }
  }

  if (!bucketCategory) {
    return <p className="text-sm text-subink italic">No Food/Personal care category found for this month.</p>
  }

  return (
    <div className="rounded-md bg-card border border-line p-4">
      <div className="flex items-center gap-2 mb-3">
        {['food', 'personal'].map((b) => (
          <button
            key={b}
            onClick={() => setBucket(b)}
            className={`text-xs px-3 py-1.5 rounded-full border ${bucket === b ? 'bg-ink text-card border-ink' : 'border-line text-subink'}`}
          >
            {b === 'food' ? 'Food' : 'Personal care'}
          </button>
        ))}
      </div>

      {error && <p className="text-clay text-sm mb-2">{error}</p>}

      <button onClick={() => setExpanded((s) => !s)} className="text-sm text-turmeric underline underline-offset-2 mb-3">
        {expanded ? 'Hide' : 'Show'} what's inside — {currency(total)}
      </button>

      {expanded && (
        <div className="space-y-2 mb-3">
          {items.length === 0 && <p className="text-sm text-subink italic">Nothing logged here yet this month.</p>}
          {items.map((i) => (
            <div key={i.id} className="flex items-center justify-between text-sm border-b border-line pb-1.5">
              <span className="text-ink">{i.name}</span>
              <div className="flex items-center gap-3">
                <span className="font-mono text-subink">{currency(i.amount)}</span>
                <button
                  onClick={async () => { await api.deletePurchase(i.id); await load(); onPurchaseChange?.() }}
                  className="text-subink hover:text-clay text-xs"
                >✕</button>
              </div>
            </div>
          ))}
          <div className="flex justify-between text-sm font-medium pt-1">
            <span>Total</span>
            <span className="font-mono">{currency(total)}</span>
          </div>

          <form onSubmit={handleAdd} className="flex gap-2 pt-2">
            <input
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              placeholder="Item — e.g. Badam 500g"
              className="flex-1 rounded border border-line px-2 py-1.5 text-sm outline-none focus:border-turmeric"
            />
            <input
              value={form.amount}
              onChange={(e) => setForm((f) => ({ ...f, amount: e.target.value }))}
              type="number"
              placeholder="₹"
              className="w-20 rounded border border-line px-2 py-1.5 text-sm outline-none focus:border-turmeric"
            />
            <button type="submit" className="rounded bg-ink text-card px-3 text-sm hover:bg-turmeric">+</button>
          </form>
        </div>
      )}
    </div>
  )
}
