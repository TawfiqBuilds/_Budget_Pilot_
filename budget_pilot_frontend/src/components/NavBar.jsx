import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../lib/auth'

const links = [
  { to: '/', label: 'Dashboard' },
  { to: '/transactions', label: 'Transactions' },
  { to: '/reports', label: 'Reports' },
]

export default function NavBar() {
  const { signOut } = useAuth()
  const { pathname } = useLocation()

  return (
    <header className="border-b border-line bg-paper/95 backdrop-blur sticky top-0 z-10">
      <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between flex-wrap gap-3">
        <h1 className="font-display text-xl text-ink">Budget Pilot</h1>
        <nav className="flex items-center gap-4 flex-wrap">
          {links.map((l) => (
            <Link
              key={l.to}
              to={l.to}
              className={`text-sm ${pathname === l.to ? 'text-ink font-medium border-b-2 border-turmeric' : 'text-subink hover:text-ink'}`}
            >
              {l.label}
            </Link>
          ))}
          <Link to="/settings" className="text-sm text-subink hover:text-ink">Settings</Link>
          <button onClick={signOut} className="text-sm text-subink hover:text-ink">Sign out</button>
        </nav>
      </div>
    </header>
  )
}
