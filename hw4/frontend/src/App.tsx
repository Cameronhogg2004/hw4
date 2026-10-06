import { useEffect } from 'react'
import { Link, Route, Routes, matchPath, useLocation } from 'react-router-dom'
import ChatPicks from './components/ChatPicks'
import ChatWidget from './components/ChatWidget'
import NavBar from './components/NavBar'
import About from './pages/About'
import CreateAccount from './pages/CreateAccount'
import Home from './pages/Home'
import Login from './pages/Login'
import ProductDetail from './pages/ProductDetail'
import Products from './pages/Products'

export default function App() {
  const { pathname } = useLocation()
  // Chat picks sit above the page, except on a product page where they follow the item.
  const onDetail = matchPath('/products/:productId', pathname) !== null

  useEffect(() => {
    window.scrollTo({ top: 0 })
  }, [pathname])

  return (
    <div className="app">
      <NavBar />
      <main className="page">
        {!onDetail && <ChatPicks />}
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/products" element={<Products />} />
          <Route path="/products/:productId" element={<ProductDetail />} />
          <Route path="/about" element={<About />} />
          <Route path="/login" element={<Login />} />
          <Route path="/create-account" element={<CreateAccount />} />
          <Route path="*" element={<h1 className="page-title">Wrong drop zone — page not found</h1>} />
        </Routes>
        {onDetail && <ChatPicks />}
      </main>
      <footer className="footer">
        <div className="footer-inner">
          <div>
            <strong className="footer-brand">Campus Customs</strong>
            <p>Officially licensed Yale gear, made for Bulldogs and the people who cheer for them.</p>
          </div>
          <div>
            <strong>Visit</strong>
            <p>57 Broadway, New Haven, CT 06511</p>
          </div>
          <div>
            <strong>Shop</strong>
            <p>
              <Link to="/products?cat=hoodies">Hoodies</Link> · <Link to="/products?cat=crewnecks">Crewnecks</Link> ·{' '}
              <Link to="/products?cat=tees">Tees</Link>
            </p>
          </div>
        </div>
        <p className="footer-fine">Fan-made storefront demo for AI for Managers · Item shop theme inspired by Fortnite</p>
      </footer>
      <ChatWidget />
    </div>
  )
}
