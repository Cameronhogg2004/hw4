import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchProducts, type Product } from '../api'
import BattleBus from '../components/BattleBus'
import Countdown from '../components/Countdown'
import LootLlama from '../components/LootLlama'
import ProductCard from '../components/ProductCard'
import { CATEGORIES } from '../shop'

const SQUAD_BLURBS: Record<string, string> = {
  hoodies: 'Pullovers & full-zips for late nights at Sterling',
  crewnecks: 'College crests, varsity sports, family pride',
  tees: 'Game-day graphics and everyday Yale tees',
  'quarter-zips': 'Sharp enough for SOM, cozy enough for class',
  jackets: 'Fleece and outerwear for a New Haven winter',
}

export default function Home() {
  const [products, setProducts] = useState<Product[]>([])

  useEffect(() => {
    fetchProducts()
      .then(setProducts)
      .catch(() => setProducts([]))
  }, [])

  // Featured: priciest in-stock items first, like the shop's "Featured" row.
  const featured = useMemo(
    () => [...products].filter((p) => p.total_stock > 0).sort((a, b) => b.price - a.price || b.total_stock - a.total_stock).slice(0, 5),
    [products],
  )
  const counts = useMemo(() => {
    const c: Record<string, number> = {}
    for (const p of products) c[p.family] = (c[p.family] ?? 0) + 1
    return c
  }, [products])

  return (
    <>
      <section className="hero">
        <div className="hero-text">
          <span className="eyebrow">Season 26 · Item shop is live</span>
          <h1 className="hero-title">
            <span className="hero-line">Drop in.</span>
            <span className="hero-line hero-line-gold">Gear up in</span>
            <span className="hero-line">Bulldog Blue.</span>
          </h1>
          <p>
            Campus Customs is New Haven's home for officially licensed Yale gear. We make hoodies, crewnecks and tees you'll actually
            want to live in, from the first lecture to the last tailgate.
          </p>
          <div className="hero-actions">
            <Link to="/products" className="btn btn-primary btn-big">
              Enter the item shop
            </Link>
            <Link to="/about" className="btn btn-ghost">
              Our story
            </Link>
          </div>
          <Countdown />
        </div>
        <div className="hero-art">
          <div className="storm-ring" />
          <BattleBus />
          <div className="pedestal">
            <div className="pedestal-beam" />
            <LootLlama />
            <div className="pedestal-base" />
          </div>
          <div className="cloud cloud-1" />
          <div className="cloud cloud-2" />
        </div>
      </section>

      <section className="trust-strip" aria-label="Why shop with us">
        <div className="trust-item">
          <span className="trust-icon trust-icon-shield" />
          <div>
            <strong>Officially licensed</strong>
            <span>Real Yale marks, made right</span>
          </div>
        </div>
        <div className="trust-item">
          <span className="trust-icon trust-icon-pin" />
          <div>
            <strong>57 Broadway</strong>
            <span>Try it on steps from campus</span>
          </div>
        </div>
        <div className="trust-item">
          <span className="trust-icon trust-icon-bolt" />
          <div>
            <strong>Live stock by size</strong>
            <span>No surprises at checkout</span>
          </div>
        </div>
      </section>

      {featured.length > 0 && (
        <section className="section">
          <div className="section-head">
            <div>
              <span className="eyebrow eyebrow-gold">Featured</span>
              <h2 className="section-title">Legendary drops</h2>
            </div>
            <Countdown label="Refreshes in" />
          </div>
          <div className="shop-grid">
            {featured.map((p, i) => (
              <ProductCard key={p.product_id} product={p} index={i} featured={i === 0} />
            ))}
          </div>
        </section>
      )}

      <section className="section">
        <div className="section-head">
          <div>
            <span className="eyebrow">Choose your loadout</span>
            <h2 className="section-title">Shop by squad</h2>
          </div>
        </div>
        <div className="squads">
          {CATEGORIES.filter((c) => c.key !== 'all').map((c, i) => (
            <Link key={c.key} to={`/products?cat=${c.key}`} className={`squad squad-${i}`}>
              <span className="squad-count">{counts[c.key] ?? 0} items</span>
              <span className="squad-name">{c.label}</span>
              <span className="squad-blurb">{SQUAD_BLURBS[c.key]}</span>
              <span className="squad-go">Shop →</span>
            </Link>
          ))}
        </div>
      </section>
    </>
  )
}
