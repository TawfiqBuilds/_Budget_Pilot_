import { useState } from 'react'
import { useAuth } from '../lib/auth'
import { useNavigate } from 'react-router-dom'

export default function Login() {
  const { signIn, signUp } = useAuth()
  const navigate = useNavigate()
  const [mode, setMode] = useState('signin')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setBusy(true)
    const fn = mode === 'signin' ? signIn : signUp
    const { error } = await fn(email, password)
    setBusy(false)
    if (error) {
      setError(error.message)
    } else if (mode === 'signin') {
      navigate('/')
    } else {
      setError('Check your email to confirm your account, then sign in.')
      setMode('signin')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-paper px-4">
      <div className="w-full max-w-sm">
        <h1 className="font-display text-3xl text-ink mb-1">Budget Pilot</h1>
        <p className="text-subink text-sm mb-8">A ledger for what matters, month after month.</p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-subink mb-1" htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-md border border-line bg-card px-3 py-2.5 text-ink outline-none focus:border-turmeric"
            />
          </div>
          <div>
            <label className="block text-sm text-subink mb-1" htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              required
              minLength={6}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-md border border-line bg-card px-3 py-2.5 text-ink outline-none focus:border-turmeric"
            />
          </div>

          {error && <p className="text-sm text-clay">{error}</p>}

          <button
            type="submit"
            disabled={busy}
            className="w-full rounded-md bg-ink text-card py-2.5 font-medium hover:bg-turmeric transition-colors disabled:opacity-60"
          >
            {busy ? 'Please wait…' : mode === 'signin' ? 'Sign in' : 'Create account'}
          </button>
        </form>

        <button
          onClick={() => setMode(mode === 'signin' ? 'signup' : 'signin')}
          className="mt-4 text-sm text-subink hover:text-ink underline underline-offset-2"
        >
          {mode === 'signin' ? "New here? Create an account" : 'Already have an account? Sign in'}
        </button>
      </div>
    </div>
  )
}
