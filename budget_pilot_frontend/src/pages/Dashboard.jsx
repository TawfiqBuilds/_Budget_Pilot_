import { useEffect, useState, useCallback } from 'react'
import { api } from '../lib/api'
import NavBar from '../components/NavBar'
import LedgerRail from '../components/LedgerRail'
import Stamp from '../components/Stamp'
import CategoryPie from '../components/CategoryPie'
import ReferenceItems from '../components/ReferenceItems'

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

export default function Dashboard() {
  const [month, setMonth] = useState(() => {
    const d = new Date()
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
  })
  const [summary, setSummary] = useState(null)
  const [prevSummary, setPrevSummary] = useState(null)
  const [lifetimeSavings, setLifetimeSavings] = useState([])
  const [income, setIncome] = useState([])
  const [archivedCategories, setArchivedCategories] = useState([])
  const [showArchived, setShowArchived] = useState(false)
  const [incomeForm, setIncomeForm] = useState({ source: '', amount: '' })
  const [pushingLeftover, setPushingLeftover] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [saveError, setSaveError] = useState('')
  const [newCategoryName, setNewCategoryName] = useState('')
  const [newCategoryType, setNewCategoryType] = useState('expense')
  const [showAddCategory, setShowAddCategory] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    const prevMonth = shiftMonth(month, -1)
    try {
      const [s, prev, savings, incomeRows, archived] = await Promise.all([
        api.getMonthSummary(month),
        api.getMonthSummary(prevMonth).catch(() => null),
        api.getSavingsLifetime(),
        api.listIncome(month),
        api.listArchivedCategories(),
      ])
      setSummary(s)
      setPrevSummary(prev)
      setLifetimeSavings(savings)
      setIncome(incomeRows)
      setArchivedCategories(archived)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [month])

  useEffect(() => { load() }, [load])

  // Editing a planned/actual/notes field can only change this month's summary
  // (and, if it's a saving category, the lifetime-savings total) -- it can't
  // change your income sources or archived-category list. Refetching those
  // two on every single field blur was unnecessary round-trip work that made
  // every edit feel slower than it needed to.
  const refreshAfterEdit = useCallback(async () => {
    const [s, savings] = await Promise.all([api.getMonthSummary(month), api.getSavingsLifetime()])
    setSummary(s)
    setLifetimeSavings(savings)
  }, [month])

  async function savePlanned(categoryId, rawValue) {
    const amount = parseFloat(rawValue)
    if (isNaN(amount) || amount < 0) return
    setSaveError('')
    try {
      await api.upsertMonthEntry(month, categoryId, { planned_amount: amount })
      await refreshAfterEdit()
    } catch (e) {
      setSaveError(`Couldn't save planned amount: ${e.message}`)
    }
  }

  async function saveActual(categoryId, rawValue) {
    const amount = parseFloat(rawValue)
    if (isNaN(amount) || amount < 0) return
    setSaveError('')
    try {
      await api.upsertMonthEntry(month, categoryId, { actual_amount: amount })
      await refreshAfterEdit()
    } catch (e) {
      setSaveError(`Couldn't save actual amount: ${e.message}`)
    }
  }

  async function saveNotes(categoryId, rawValue) {
    setSaveError('')
    try {
      await api.upsertMonthEntry(month, categoryId, { notes: rawValue })
      await refreshAfterEdit()
    } catch (e) {
      setSaveError(`Couldn't save notes: ${e.message}`)
    }
  }

  async function handleArchive(categoryId) {
    if (!confirm('Archive this category? It will disappear from future months, but stays visible in months where it already has data.')) return
    try {
      await api.archiveCategory(categoryId)
      await load()
    } catch (e) {
      alert(e.message)
    }
  }

  async function handleRestore(categoryId) {
    try {
      await api.restoreCategory(categoryId)
      await load()
    } catch (e) {
      alert(e.message)
    }
  }

  async function handleDeleteForever(categoryId, categoryName) {
    if (!confirm(`Permanently delete "${categoryName}"? This can't be undone.`)) return
    try {
      await api.deleteCategory(categoryId)
      await load()
    } catch (e) {
      // Backend returns 409 if this category has history -- ask before nuking it too.
      if (e.message.includes('history')) {
        if (confirm(`${e.message}\n\nDelete it AND all its history anyway?`)) {
          try {
            await api.deleteCategory(categoryId, true)
            await load()
          } catch (e2) {
            alert(e2.message)
          }
        }
      } else {
        alert(e.message)
      }
    }
  }

  async function handleAddCategory(e) {
    e.preventDefault()
    if (!newCategoryName.trim()) return
    await api.createCategory(newCategoryName.trim(), newCategoryType)
    setNewCategoryName('')
    setNewCategoryType('expense')
    setShowAddCategory(false)
    await load()
  }

  async function handleAddIncome(e) {
    e.preventDefault()
    const amount = parseFloat(incomeForm.amount)
    if (isNaN(amount) || amount <= 0) return
    try {
      await api.addIncome(month, incomeForm.source.trim() || 'Income', amount)
      setIncomeForm({ source: '', amount: '' })
      await load()
    } catch (e) {
      setSaveError(e.message)
    }
  }

  async function handleDeleteIncome(id) {
    try {
      await api.deleteIncome(id)
      await load()
    } catch (e) {
      alert(e.message)
    }
  }

  async function handlePushLeftover(savingsCategoryId) {
    setPushingLeftover(true)
    try {
      await api.pushLeftoverToSavings(month, savingsCategoryId)
      await load()
    } catch (e) {
      alert(e.message)
    } finally {
      setPushingLeftover(false)
    }
  }

  async function handleRestoreArchived(categoryId) {
    try {
      await api.restoreCategory(categoryId)
      await load()
    } catch (e) {
      alert(e.message)
    }
  }

  async function handleDeleteArchivedForever(categoryId, categoryName) {
    if (!confirm(`Permanently delete "${categoryName}"? This can't be undone.`)) return
    try {
      await api.deleteCategory(categoryId)
      await load()
    } catch (e) {
      if (e.message.includes('history')) {
        if (confirm(`${e.message}\n\nDelete it AND all its history anyway?`)) {
          try {
            await api.deleteCategory(categoryId, true)
            await load()
          } catch (e2) {
            alert(e2.message)
          }
        }
      } else {
        alert(e.message)
      }
    }
  }

  const totalIncome = income.reduce((sum, i) => sum + i.amount, 0)
  const savingCategories = summary?.categories.filter((c) => c.category_type === 'saving' && !c.is_archived) || []

  return (
    <div className="min-h-screen bg-paper pb-24">
      <NavBar />

      <main className="max-w-4xl mx-auto px-4 pt-6">
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
        {saveError && <p className="text-clay text-sm mb-4">{saveError}</p>}

        {loading ? (
          <p className="text-subink text-sm">Loading…</p>
        ) : summary && (
          <>
            {/* Income sources for this month */}
            <section className="rounded-md bg-card border border-line p-4 mb-6">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm uppercase tracking-wide text-subink">Income — {monthLabel(month)}</h3>
                <span className="font-mono text-lg text-ink">{currency(totalIncome)}</span>
              </div>
              <div className="space-y-1.5 mb-3">
                {income.length === 0 && (
                  <p className="text-sm text-subink italic">No income sources added for this month yet.</p>
                )}
                {income.map((i) => (
                  <div key={i.id} className="flex items-center justify-between text-sm border-b border-line last:border-0 pb-1.5">
                    <span className="text-ink">{i.source}</span>
                    <div className="flex items-center gap-3">
                      <span className="font-mono text-ink">{currency(i.amount)}</span>
                      <button onClick={() => handleDeleteIncome(i.id)} className="text-subink hover:text-clay text-xs" aria-label="Remove income source">✕</button>
                    </div>
                  </div>
                ))}
              </div>
              <form onSubmit={handleAddIncome} className="flex gap-2">
                <input
                  value={incomeForm.source}
                  onChange={(e) => setIncomeForm((f) => ({ ...f, source: e.target.value }))}
                  placeholder="Source — e.g. Salary, Freelance"
                  className="flex-1 rounded border border-line px-2 py-1.5 text-sm outline-none focus:border-turmeric"
                />
                <input
                  value={incomeForm.amount}
                  onChange={(e) => setIncomeForm((f) => ({ ...f, amount: e.target.value }))}
                  type="number"
                  min="0"
                  placeholder="₹"
                  className="w-28 rounded border border-line px-2 py-1.5 text-sm outline-none focus:border-turmeric"
                />
                <button type="submit" className="rounded bg-ink text-card px-3 text-sm hover:bg-turmeric">+</button>
              </form>
            </section>

            <div className="grid grid-cols-2 gap-3 mb-3">
              <div className="rounded-md bg-card border border-line p-4">
                <p className="text-xs uppercase tracking-wide text-subink mb-1">Planned</p>
                <p className="font-mono text-2xl text-ink">{currency(summary.total_planned)}</p>
                {summary.planned_pct_of_income != null && (
                  <p className="text-xs text-subink mt-1">{summary.planned_pct_of_income}% of income</p>
                )}
              </div>
              <div className="rounded-md bg-card border border-line p-4">
                <p className="text-xs uppercase tracking-wide text-subink mb-1">Spent so far</p>
                <p className={`font-mono text-2xl ${summary.total_actual > summary.total_planned ? 'text-clay' : 'text-ink'}`}>
                  {currency(summary.total_actual)}
                </p>
                {summary.spent_pct_of_income != null && (
                  <p className="text-xs text-subink mt-1">{summary.spent_pct_of_income}% of income</p>
                )}
              </div>
            </div>

            {/* Unplanned / leftover, mirroring "balance from income" the way other budgeting apps show it */}
            <div className="grid grid-cols-2 gap-3 mb-6">
              <div className={`rounded-md border p-4 ${summary.over_committed ? 'bg-clay/5 border-clay/30' : 'bg-card border-line'}`}>
                <p className="text-xs uppercase tracking-wide text-subink mb-1">Unplanned (income − planned)</p>
                <p className={`font-mono text-xl ${summary.over_committed ? 'text-clay' : 'text-olive'}`}>
                  {summary.unplanned_amount < 0 ? '-' : ''}{currency(Math.abs(summary.unplanned_amount))}
                </p>
                {summary.unplanned_pct != null && (
                  <p className="text-xs text-subink mt-1">
                    {summary.unplanned_pct}% of income{summary.over_committed ? ' — you\'ve planned more than you earn' : ' still unassigned'}
                  </p>
                )}
              </div>
              <div className="rounded-md bg-card border border-line p-4">
                <p className="text-xs uppercase tracking-wide text-subink mb-1">Leftover (income − spent)</p>
                <p className={`font-mono text-xl ${summary.leftover_amount < 0 ? 'text-clay' : 'text-olive'}`}>
                  {summary.leftover_amount < 0 ? '-' : ''}{currency(Math.abs(summary.leftover_amount))}
                </p>
                {summary.leftover_pct != null && <p className="text-xs text-subink mt-1">{summary.leftover_pct}% of income</p>}
                {summary.leftover_amount > 0 && savingCategories.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-2">
                    {savingCategories.map((sc) => (
                      <button
                        key={sc.category_id}
                        disabled={pushingLeftover}
                        onClick={() => handlePushLeftover(sc.category_id)}
                        className="text-xs rounded-full border border-olive text-olive px-2.5 py-1 hover:bg-olive hover:text-card disabled:opacity-50"
                      >
                        Push to {sc.category_name}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Lifetime EF / SIP totals */}
            {lifetimeSavings.length > 0 && (
              <div className="grid grid-cols-2 gap-3 mb-6">
                {lifetimeSavings.map((s) => (
                  <div key={s.category_id} className="rounded-md bg-card border border-line p-4">
                    <p className="text-xs uppercase tracking-wide text-subink mb-1">{s.category_name} — lifetime</p>
                    <p className="font-mono text-xl text-olive">{currency(s.lifetime_total)}</p>
                  </div>
                ))}
              </div>
            )}

            {/* This month's spend, by category */}
            <section className="rounded-md bg-card border border-line p-4 mb-8">
              <h3 className="text-sm uppercase tracking-wide text-subink mb-3">{monthLabel(month)} · spent by category</h3>
              <CategoryPie categories={summary.categories} totalIncome={summary.total_income} />
            </section>

            {/* Categories */}
            <section className="mb-8">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm uppercase tracking-wide text-subink">Categories</h3>
                <button onClick={() => setShowAddCategory((s) => !s)} className="text-sm text-turmeric hover:text-clay font-medium">
                  + Add category
                </button>
              </div>

              {showAddCategory && (
                <form onSubmit={handleAddCategory} className="flex gap-2 mb-4">
                  <input
                    autoFocus
                    value={newCategoryName}
                    onChange={(e) => setNewCategoryName(e.target.value)}
                    placeholder="Category name"
                    className="flex-1 rounded border border-line bg-card px-3 py-2 text-sm outline-none focus:border-turmeric"
                  />
                  <select
                    value={newCategoryType}
                    onChange={(e) => setNewCategoryType(e.target.value)}
                    className="rounded border border-line bg-card px-2 py-2 text-sm outline-none focus:border-turmeric"
                    title="Expense: spending you track. Saving: a goal you're putting money toward (shows up in lifetime totals)."
                  >
                    <option value="expense">Expense</option>
                    <option value="saving">Saving goal</option>
                  </select>
                  <button type="submit" className="rounded bg-ink text-card px-4 text-sm font-medium hover:bg-turmeric">Add</button>
                </form>
              )}

              <div className="space-y-3">
                {summary.categories.length === 0 && (
                  <p className="text-sm text-subink italic">No categories set up for this month yet.</p>
                )}
                {summary.categories.map((c) => {
                  const prev = prevSummary?.categories.find((p) => p.category_id === c.category_id)
                  return (
                  <div key={`${c.category_id}-${month}`} className="rounded-md bg-card border border-line p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-ink font-medium">{c.category_name}</span>
                        {c.is_default && <Stamp color="#B9832A">Fixed</Stamp>}
                        {c.is_archived && <Stamp color="#6B6656">Archived</Stamp>}
                      </div>
                      <div className="flex items-center gap-3">
                        {!c.is_default && !c.is_archived && (
                          <button onClick={() => handleArchive(c.category_id)} className="text-xs text-subink hover:text-clay">
                            Archive
                          </button>
                        )}
                        {!c.is_default && c.is_archived && (
                          <>
                            <button onClick={() => handleRestore(c.category_id)} className="text-xs text-olive hover:text-turmeric">
                              Restore
                            </button>
                            <button onClick={() => handleDeleteForever(c.category_id, c.category_name)} className="text-xs text-subink hover:text-clay">
                              Delete forever
                            </button>
                          </>
                        )}
                      </div>
                    </div>

                    <LedgerRail
                      planned={c.planned_amount}
                      actual={c.actual_amount}
                      pctElapsed={summary.days_elapsed / summary.days_in_month}
                      pace={c.pace}
                    />

                    <div className="flex items-center justify-between mt-2 text-xs">
                      <span className={c.balance < 0 ? 'text-clay' : 'text-olive'}>
                        This month: {c.balance < 0 ? '-' : '+'}{currency(Math.abs(c.balance))}
                      </span>
                      {c.carry_in !== 0 && (
                        <span className={c.carry_in < 0 ? 'text-clay' : 'text-subink'} title="Carried over from previous months (over/underspend adds up)">
                          Carried in: {c.carry_in < 0 ? '-' : '+'}{currency(Math.abs(c.carry_in))}
                        </span>
                      )}
                      <span className={`font-medium ${c.cumulative_balance < 0 ? 'text-clay' : 'text-olive'}`}>
                        Running balance: {c.cumulative_balance < 0 ? '-' : '+'}{currency(Math.abs(c.cumulative_balance))}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-3 mt-3">
                      <label className="block">
                        <span className="block text-[10px] uppercase tracking-wide text-subink mb-1">Planned</span>
                        <input
                          type="number"
                          min="0"
                          defaultValue={c.planned_amount}
                          onBlur={(e) => savePlanned(c.category_id, e.target.value)}
                          onKeyDown={(e) => e.key === 'Enter' && e.target.blur()}
                          className="w-full rounded border border-line px-2 py-1.5 font-mono text-sm outline-none focus:border-turmeric"
                        />
                      </label>
                      <label className="block">
                        <span className="block text-[10px] uppercase tracking-wide text-subink mb-1">
                          {c.category_type === 'saving' ? 'Actual (manual)' : 'Spent'}
                        </span>
                        {c.category_type === 'saving' ? (
                          <input
                            type="number"
                            min="0"
                            defaultValue={c.actual_amount}
                            onBlur={(e) => saveActual(c.category_id, e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && e.target.blur()}
                            className="w-full rounded border border-line px-2 py-1.5 font-mono text-sm outline-none focus:border-turmeric"
                          />
                        ) : (
                          <p className="font-mono text-sm text-ink py-1.5">{currency(c.actual_amount)}</p>
                        )}
                      </label>
                    </div>

                    {prev && (
                      <p className="text-xs text-subink mt-2">
                        {monthLabel(shiftMonth(month, -1))}: planned {currency(prev.planned_amount)}, spent {currency(prev.actual_amount)}
                      </p>
                    )}

                    <label className="block mt-3">
                      <span className="block text-[10px] uppercase tracking-wide text-subink mb-1">Notes</span>
                      <input
                        type="text"
                        defaultValue={c.notes || ''}
                        placeholder="e.g. splurged on a birthday gift"
                        onBlur={(e) => saveNotes(c.category_id, e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && e.target.blur()}
                        className="w-full rounded border border-line px-2 py-1.5 text-sm outline-none focus:border-turmeric"
                      />
                    </label>
                  </div>
                  )
                })}
              </div>
            </section>

            {/* Archived categories -- fixes the "archived it with no data, can't
                find it anywhere anymore" problem: a category with zero history
                never shows up in any month view, so it needs its own list here. */}
            {archivedCategories.length > 0 && (
              <section className="mb-8">
                <button
                  onClick={() => setShowArchived((s) => !s)}
                  className="text-sm text-turmeric hover:text-clay font-medium mb-3"
                >
                  {showArchived ? 'Hide' : 'Show'} archived categories ({archivedCategories.length})
                </button>
                {showArchived && (
                  <div className="space-y-2">
                    {archivedCategories.map((c) => (
                      <div key={c.id} className="rounded-md bg-card border border-line p-3 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="text-ink text-sm">{c.name}</span>
                          <Stamp color="#6B6656">Archived</Stamp>
                        </div>
                        <div className="flex items-center gap-3">
                          <button onClick={() => handleRestoreArchived(c.id)} className="text-xs text-olive hover:text-turmeric">
                            Restore
                          </button>
                          <button onClick={() => handleDeleteArchivedForever(c.id, c.name)} className="text-xs text-subink hover:text-clay">
                            Delete forever
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </section>
            )}

            {/* Food / Personal reference breakdown */}
            <section>
              <h3 className="text-sm uppercase tracking-wide text-subink mb-3">What's inside your buckets</h3>
              <ReferenceItems month={month} categories={summary.categories} />
            </section>
          </>
        )}
      </main>
    </div>
  )
}
