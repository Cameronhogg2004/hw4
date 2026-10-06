import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchProduct, type ProductDetail as Detail } from '../api'
import { useChatBridge } from '../chatBridge'
import { formatPrice, rarityFor } from '../rarity'
import { swatch } from '../shop'

const LOW_STOCK = 5
const METER_FULL = 25

export default function ProductDetail() {
  const { productId = '' } = useParams()
  const { askLlama } = useChatBridge()
  const [product, setProduct] = useState<Detail | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [selected, setSelected] = useState<string | null>(null)

  useEffect(() => {
    setProduct(null)
    setError(null)
    setSelected(null)
    fetchProduct(productId)
      .then(setProduct)
      .catch((e: Error) => setError(e.message))
  }, [productId])

  if (error) return <p className="error">Couldn't load this item ({error}).</p>
  if (!product) return <div className="detail-skeleton" aria-label="Loading" />

  const rarity = rarityFor(product.price)
  const chosen = product.sizes.find((s) => s.size === selected)

  return (
    <>
      <nav className="crumbs" aria-label="Breadcrumb">
        <Link to="/products">Item Shop</Link>
        <span>›</span>
        <Link to={`/products?cat=${product.family}`}>{product.family.replace('-', ' ')}</Link>
        <span>›</span>
        <span>{product.name}</span>
      </nav>
      <div className={`detail rarity-${rarity}`}>
        <div className="detail-stage">
          <div className="stage-rays" />
          <div className="stage-glow" />
          <img src={product.image_url} alt={product.name} />
          <div className="stage-floor" />
        </div>
        <div className="detail-info">
          <span className="rarity-label rarity-label-big">{rarity} · {product.garment_type}</span>
          <h1 className="detail-name">{product.name}</h1>
          <div className="detail-price-row">
            <span className="price-tag price-tag-big">{formatPrice(product.price)}</span>
            <span className={product.total_stock ? 'stock-pill' : 'stock-pill stock-pill-out'}>
              {product.total_stock ? `${product.total_stock} in stock` : 'Sold out'}
            </span>
          </div>
          <p className="detail-desc">{product.description}</p>

          <h3>Colors</h3>
          <div className="chips">
            {product.colors.map((c) => (
              <span key={c} className="chip chip-color">
                <span className="swatch-dot" style={{ background: swatch(c) }} />
                {c}
              </span>
            ))}
          </div>

          <h3>Pick your size</h3>
          <div className="sizes">
            {product.sizes.map((s) => (
              <button
                key={s.size}
                className={['size', s.size === selected && 'size-selected'].filter(Boolean).join(' ')}
                disabled={s.quantity === 0}
                onClick={() => setSelected(s.size)}
              >
                <strong>{s.size}</strong>
                <span>{s.quantity === 0 ? 'Sold out' : `${s.quantity} left`}</span>
                <span className="size-meter">
                  <span
                    className={s.quantity <= LOW_STOCK ? 'size-meter-fill size-meter-low' : 'size-meter-fill'}
                    style={{ width: `${Math.min(100, (s.quantity / METER_FULL) * 100)}%` }}
                  />
                </span>
              </button>
            ))}
          </div>
          <p className="stock-note">
            {chosen
              ? chosen.quantity <= LOW_STOCK
                ? `Only ${chosen.quantity} left in ${chosen.size}. Grab it before the storm closes in.`
                : `${chosen.size} is in stock (${chosen.quantity} available). Pick it up at 57 Broadway.`
              : `${product.total_stock} in stock across all sizes. Pick a size to check it.`}
          </p>

          <button
            className="btn btn-llama"
            onClick={() =>
              askLlama(
                selected
                  ? `Is this in stock in ${selected}, and do you have similar items?`
                  : 'Which sizes of this are in stock, and do you have similar items?',
              )
            }
          >
            <span className="btn-llama-icon" aria-hidden="true" />
            Ask the llama about this item
          </button>

          <h3>Tags</h3>
          <div className="chips">
            {product.search_tags.map((t) => (
              <span key={t} className="chip chip-tag">
                {t}
              </span>
            ))}
          </div>
        </div>
      </div>
    </>
  )
}
