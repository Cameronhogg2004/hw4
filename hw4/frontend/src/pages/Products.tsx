import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { fetchProducts, type Product } from '../api'
import ProductCard from '../components/ProductCard'
import { CATEGORIES, SIZES } from '../shop'

// Problem 9: category, size, in-stock and sort filters, kept in the URL so
// Back works and filtered views can be shared (/products?cat=hoodies&size=M).
const SORTS = [
  { key: 'featured', label: 'Featured' },
  { key: 'price-asc', label: 'Price: low → high' },
  { key: 'price-desc', label: 'Price: high → low' },
  { key: 'name', label: 'Name A–Z' },
]

export default function Products() {
  const [products, setProducts] = useState<Product[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [params, setParams] = useSearchParams()

  const cat = params.get('cat') ?? 'all'
  const size = params.get('size')
  const inStock = params.get('stock') === '1'
  const sort = params.get('sort') ?? 'featured'
  const query = params.get('q') ?? ''

  useEffect(() => {
    fetchProducts()
      .then(setProducts)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  function update(key: string, value: string | null) {
    setParams(
      (prev) => {
        const next = new URLSearchParams(prev)
        if (value === null || value === '' || (key === 'cat' && value === 'all') || (key === 'sort' && value === 'featured')) {
          next.delete(key)
        } else {
          next.set(key, value)
        }
        return next
      },
      { replace: key === 'q' },
    )
  }

  // Everything except the category, so each tab can show how many items it would hold.
  const baseFiltered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return products.filter(
      (p) =>
        (!size || p.sizes_in_stock.includes(size)) &&
        (!inStock || p.total_stock > 0) &&
        (!q || [p.name, p.garment_type, p.short_info, ...p.colors].join(' ').toLowerCase().includes(q)),
    )
  }, [products, size, inStock, query])

  const visible = useMemo(() => {
    const list = baseFiltered.filter((p) => cat === 'all' || p.family === cat)
    const sorted = [...list]
    if (sort === 'price-asc') sorted.sort((a, b) => a.price - b.price || a.name.localeCompare(b.name))
    else if (sort === 'price-desc') sorted.sort((a, b) => b.price - a.price || a.name.localeCompare(b.name))
    else if (sort === 'name') sorted.sort((a, b) => a.name.localeCompare(b.name))
    else sorted.sort((a, b) => Number(b.total_stock > 0) - Number(a.total_stock > 0) || b.price - a.price)
    return sorted
  }, [baseFiltered, cat, sort])

  const countFor = (key: string) => (key === 'all' ? baseFiltered.length : baseFiltered.filter((p) => p.family === key).length)
  const filtersOn = cat !== 'all' || size || inStock || sort !== 'featured' || query

  return (
    <>
      <div className="shop-head">
        <div>
          <span className="eyebrow">Campus Customs</span>
          <h1 className="page-title">Item Shop</h1>
        </div>
        <input
          className="search"
          value={query}
          onChange={(e) => update('q', e.target.value)}
          placeholder="Search hoodies, colors, colleges…"
          aria-label="Search products"
        />
      </div>

      <div className="filters" role="region" aria-label="Filters">
        <div className="tabs" role="tablist" aria-label="Category">
          {CATEGORIES.map((c) => (
            <button
              key={c.key}
              role="tab"
              aria-selected={cat === c.key}
              className={cat === c.key ? 'tab tab-active' : 'tab'}
              onClick={() => update('cat', c.key)}
            >
              {c.label}
              <span className="tab-count">{countFor(c.key)}</span>
            </button>
          ))}
        </div>
        <div className="filter-row">
          <div className="size-filter" aria-label="My size">
            <span className="filter-label">My size</span>
            {SIZES.map((s) => (
              <button
                key={s}
                className={size === s ? 'size-chip size-chip-active' : 'size-chip'}
                aria-pressed={size === s}
                onClick={() => update('size', size === s ? null : s)}
              >
                {s}
              </button>
            ))}
          </div>
          <label className="toggle">
            <input type="checkbox" checked={inStock} onChange={(e) => update('stock', e.target.checked ? '1' : null)} />
            <span className="toggle-track">
              <span className="toggle-thumb" />
            </span>
            In stock only
          </label>
          <label className="sort">
            <span className="filter-label">Sort</span>
            <select value={sort} onChange={(e) => update('sort', e.target.value)}>
              {SORTS.map((s) => (
                <option key={s.key} value={s.key}>
                  {s.label}
                </option>
              ))}
            </select>
          </label>
        </div>
      </div>

      {loading && <p className="muted">Loading the item shop…</p>}
      {error && <p className="error">Couldn't load products ({error}). Is the backend running on :8000?</p>}
      {!loading && !error && (
        <>
          <div className="result-bar">
            <span>
              Showing <strong>{visible.length}</strong> of {products.length}
              {size && ` · in stock in ${size}`}
            </span>
            {filtersOn && (
              <button className="link-button" onClick={() => setParams(new URLSearchParams())}>
                Reset filters
              </button>
            )}
          </div>
          {visible.length === 0 ? (
            <div className="empty">
              <strong>No loot here.</strong> Try another size or category, or ask the llama for similar items.
            </div>
          ) : (
            <div className="grid">
              {visible.map((p, i) => (
                <ProductCard key={p.product_id} product={p} index={i} />
              ))}
            </div>
          )}
        </>
      )}
    </>
  )
}
