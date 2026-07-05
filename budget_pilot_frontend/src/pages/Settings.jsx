import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../lib/auth'
import { api } from '../lib/api'

export default function Settings() {
  const { user, signOut } = useAuth()
  const navigate = useNavigate()
  const [confirmText, setConfirmText] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const matches = confirmText.trim().toLowerCase() === (user?.email || '').toLowerCase()

  async function handleDelete() {
    if (!matches) return
    setBusy(true)
    setError('')
    try {
      await api.deleteAccount(confirmText.trim())
      await signOut()
      navigate('/login')
    } catch (e) {
      setError(e.message)
      setBusy(false)
    }
  }

  return (
    <div className="min-h-screen bg-paper">
      <header className="border-b border-line">
        <div className="max-w-3xl mx-auto px-4 py-4 flex items-center gap-4">
          <Link to="/" className="text-subink hover:text-ink" aria-label="Back">←</Link>
          <h1 className="font-display text-xl text-ink">Settings</h1>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 py-8 space-y-8">
        <section className="rounded-md bg-card border border-line p-5">
          <h2 className="text-sm uppercase tracking-wide text-subink mb-2">Account</h2>
          <p className="text-ink">{user?.email}</p>
        </section>

        <section className="rounded-xl border border-clay/30 bg-clay/5 p-5">
          <h2 className="text-sm uppercase tracking-wide text-clay mb-2">Danger zone</h2>
          <p className="text-sm text-ink mb-4">
            Deleting your account permanently removes every category, month, and purchase you've
            logged. This can't be undone.
          </p>

          <label className="block text-sm text-subink mb-1" htmlFor="confirm-email">
            Type <span className="font-medium text-ink">{user?.email}</span> to confirm
          </label>
          <input
            id="confirm-email"
            value={confirmText}
            onChange={(e) => setConfirmText(e.target.value)}
            className="w-full rounded border border-line bg-card px-3 py-2.5 mb-3 outline-none focus:border-clay"
            placeholder="your@email.com"
          />

          {error && <p className="text-sm text-clay mb-3">{error}</p>}

          <button
            onClick={handleDelete}
            disabled={!matches || busy}
            className="w-full rounded bg-clay text-card py-2.5 font-medium disabled:opacity-40 disabled:cursor-not-allowed hover:bg-ink transition-colors"
          >
            {busy ? 'Deleting…' : 'Delete my account permanently'}
          </button>
        </section>
      </main>
    </div>
  )
}
