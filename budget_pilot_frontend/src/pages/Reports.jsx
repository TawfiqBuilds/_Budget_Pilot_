import { useEffect, useState, useCallback } from 'react'
import { BarChart, Bar, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { api } from '../lib/api'
import NavBar from '../components/NavBar'

function currency(n) {
  return `₹${Number(n).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`
}

function currentMonth() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}

function monthShortLabel(month) {
  const [y, m] = month.split('-').map(Number)
  return new Date(y, m - 1, 1).toLocaleDateString(undefined, { month: 'short', year: '2-digit' })
}

function quarterOf(month) {
  const [y, m] = month.split('-').map(Number)
  return `Q${Math.ceil(m / 3)} '${String(y).slice(2)}`
}

function yearOf(month) {
  return month.split('-')[0]
}

function withBalance(row) {
  return { ...row, balance: round2(row.planned - row.spent), overBudget: row.spent > row.planned }
}

function round2(n) {
  return Math.round(n * 100) / 100
}

function groupBy(history, grouping) {
  if (grouping === 'month') {
    return history.map((h) =>
      withBalance({
        label: monthShortLabel(h.month),
        planned: h.total_planned,
        spent: h.total_actual,
        income: h.total_income || 0,
      })
    )
  }
  const keyFn = grouping === 'quarter' ? quarterOf : yearOf
  const groups = {}
  for (const h of history) {
    const key = keyFn(h.month)
    if (!groups[key]) groups[key] = { label: key, planned: 0, spent: 0, income: 0 }
    groups[key].planned += h.total_planned
    groups[key].spent += h.total_actual
    groups[key].income += h.total_income || 0
  }
  return Object.values(groups).map(withBalance)
}

export default function Reports() {
  const [grouping, setGrouping] = useState('month')
  const [history, setHistory] = useState([])
  const [lifetimeSavings, setLifetimeSavings] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const months = grouping === 'year' ? 36 : 12
      const [data, savings] = await Promise.all([
        api.getHistory(currentMonth(), months),
        api.getSavingsLifetime(),
      ])
      setHistory(data)
      setLifetimeSavings(savings)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [grouping])

  useEffect(() => { load() }, [load])

  const chartData = groupBy(history, grouping)
  const totalPlanned = history.reduce((s, h) => s + h.total_planned, 0)
  const totalSpent = history.reduce((s, h) => s + h.total_actual, 0)

  return (
    <div className="min-h-screen bg-paper pb-24">
      <NavBar />
      <main className="max-w-4xl mx-auto px-4 pt-6">
        <div className="flex items-center justify-between mb-6 flex-wrap gap-3">
          <h2 className="font-display text-2xl text-ink">Reports</h2>
          <div className="flex gap-2">
            {['month', 'quarter', 'year'].map((g) => (
              <button
                key={g}
                onClick={() => setGrouping(g)}
                className={`text-xs px-3 py-1.5 rounded-full border capitalize ${grouping === g ? 'bg-ink text-card border-ink' : 'border-line text-subink'}`}
              >
                {g}
              </button>
            ))}
          </div>
        </div>

        {error && <p className="text-clay text-sm mb-4">{error}</p>}

        {loading ? (
          <p className="text-subink text-sm">Loading…</p>
        ) : (
          <>
            {lifetimeSavings.length > 0 && (
              <div className="grid grid-cols-2 gap-3 mb-6">
                {lifetimeSavings.map((s) => (
                  <div key={s.category_id} className="rounded-md bg-card border border-line p-4">
                    <p className="text-xs uppercase tracking-wide text-subink mb-1">{s.category_name} — lifetime total</p>
                    <p className="font-mono text-xl text-olive">{currency(s.lifetime_total)}</p>
                  </div>
                ))}
              </div>
            )}

            <div className="grid grid-cols-2 gap-3 mb-6">
              <div className="rounded-md bg-card border border-line p-4">
                <p className="text-xs uppercase tracking-wide text-subink mb-1">
                  Planned ({grouping === 'year' ? 'last 36 months' : 'last 12 months'})
                </p>
                <p className="font-mono text-2xl text-ink">{currency(totalPlanned)}</p>
              </div>
              <div className="rounded-md bg-card border border-line p-4">
                <p className="text-xs uppercase tracking-wide text-subink mb-1">Actually spent</p>
                <p className={`font-mono text-2xl ${totalSpent > totalPlanned ? 'text-clay' : 'text-ink'}`}>{currency(totalSpent)}</p>
              </div>
            </div>

            <div className="rounded-md bg-card border border-line p-4 mb-6">
              <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
                <h3 className="text-sm uppercase tracking-wide text-subink">Planned vs spent, by {grouping}</h3>
                <div className="flex items-center gap-3 text-[11px] text-subink">
                  <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-olive inline-block" /> within budget</span>
                  <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-clay inline-block" /> over budget</span>
                </div>
              </div>
              <div className="h-72 w-full">
                <ResponsiveContainer>
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#D3CBB5" />
                    <XAxis dataKey="label" tick={{ fontSize: 11, fill: '#6B6656' }} />
                    <YAxis tick={{ fontSize: 11, fill: '#6B6656' }} tickFormatter={(v) => `₹${v / 1000}k`} />
                    <Tooltip
                      formatter={(v, name) => [currency(v), name]}
                      labelFormatter={(label, payload) => {
                        const row = payload?.[0]?.payload
                        if (!row) return label
                        return `${label} — ${row.overBudget ? 'over budget' : 'within budget'} (balance ${currency(row.balance)})`
                      }}
                      contentStyle={{ background: '#FFFDF8', border: '1px solid #D3CBB5', fontSize: 12 }}
                    />
                    <Legend wrapperStyle={{ fontSize: 12 }} />
                    <Bar dataKey="planned" fill="#B9832A" radius={[3, 3, 0, 0]} name="Planned" />
                    <Bar dataKey="spent" radius={[3, 3, 0, 0]} name="Spent">
                      {chartData.map((row, i) => (
                        <Cell key={i} fill={row.overBudget ? '#A24B3B' : '#5C7A4F'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="rounded-md bg-card border border-line p-4">
              <h3 className="text-sm uppercase tracking-wide text-subink mb-3">Breakdown</h3>
              <div className="space-y-2">
                {chartData.map((row) => (
                  <div key={row.label} className="flex items-center justify-between text-sm border-b border-line last:border-0 pb-2">
                    <span className="text-ink">{row.label}</span>
                    <div className="flex gap-4 font-mono text-xs">
                      <span className="text-subink">plan {currency(row.planned)}</span>
                      <span className={row.overBudget ? 'text-clay' : 'text-olive'}>spent {currency(row.spent)}</span>
                      <span className={row.balance < 0 ? 'text-clay' : 'text-olive'}>
                        balance {row.balance < 0 ? '-' : '+'}{currency(Math.abs(row.balance))}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  )
}
