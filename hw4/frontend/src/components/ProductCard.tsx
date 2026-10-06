import type { CSSProperties } from 'react'
import { Link } from 'react-router-dom'
import type { Product } from '../api'
import { formatPrice, rarityFor } from '../rarity'
import { stockLabel, swatch } from '../shop'

// Item-shop tile: rarity rays behind the garment, name plate, gold price tag.
export default function ProductCard({
  product,
  index = 0,
  featured = false,
}: {
  product: Product
  index?: number
  featured?: boolean
}) {
  const rarity = rarityFor(product.price)
  const urgency = stockLabel(product)
  return (
    <Link
      to={`/products/${product.product_id}`}
      className={['card', `rarity-${rarity}`, featured && 'card-featured'].filter(Boolean).join(' ')}
      style={{ '--i': Math.min(index, 14) } as CSSProperties}
    >
      <div className="card-image">
        <img src={product.image_url} alt={product.name} loading="lazy" />
        <span className="rarity-label">{rarity}</span>
        {urgency && (
          <span className={product.total_stock === 0 ? 'card-flag card-flag-out' : 'card-flag'}>{urgency}</span>
        )}
      </div>
      <div className="card-body">
        <h3 className="card-name">{product.name}</h3>
        <p className="card-info">{product.short_info}</p>
        <div className="card-meta">
          <span className="card-swatches" aria-label={`Colors: ${product.colors.join(', ')}`}>
            {product.colors.slice(0, 4).map((c) => (
              <span key={c} className="swatch-dot" style={{ background: swatch(c) }} title={c} />
            ))}
          </span>
          <span className="price-tag">{formatPrice(product.price)}</span>
        </div>
      </div>
    </Link>
  )
}
