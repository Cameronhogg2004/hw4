import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'

const MAIN_LINKS = [
  { to: '/', label: 'Home' },
  { to: '/products', label: 'Products' },
  { to: '/about', label: 'About Us' },
]

const TICKER = [
  'Game day drops are live',
  'Free pickup at 57 Broadway, New Haven',
  'Officially licensed Yale gear',
  'Ask the llama for your size',
  'All 14 residential colleges',
]

const linkClass =
  (extra?: string) =>
  ({ isActive }: { isActive: boolean }) =>
    ['nav-link', extra, isActive && 'active'].filter(Boolean).join(' ')

export default function NavBar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  return (
    <header className="header">
      <div className="ticker" aria-label="Store news">
        <div className="ticker-track">
          {[...TICKER, ...TICKER].map((item, i) => (
            <span key={i} className="ticker-item">
              <span className="ticker-star">★</span>
              {item}
            </span>
          ))}
        </div>
      </div>
      <div className="nav">
        <NavLink to="/" className="nav-brand" aria-label="Campus Customs home">
          <span className="nav-brand-mark">
            <span>Y</span>
          </span>
          <span className="nav-brand-text">
            Campus Customs
            <small>Yale Bulldog Blue · Item Shop</small>
          </span>
        </NavLink>
        <nav className="nav-links">
          {MAIN_LINKS.map((link) => (
            <NavLink key={link.to} to={link.to} end={link.to === '/'} className={linkClass()}>
              {link.label}
            </NavLink>
          ))}
          {user ? (
            <>
              <span className="nav-user">
                <span className="nav-user-avatar">{user.first_name.charAt(0).toUpperCase()}</span>
                {user.first_name}
              </span>
              <button
                className="nav-link nav-button"
                onClick={async () => {
                  await logout()
                  navigate('/')
                }}
              >
                Log out
              </button>
            </>
          ) : (
            <>
              <NavLink to="/login" className={linkClass()}>
                Login
              </NavLink>
              <NavLink to="/create-account" className={linkClass('nav-link-cta')}>
                Create Account
              </NavLink>
            </>
          )}
        </nav>
      </div>
    </header>
  )
}
