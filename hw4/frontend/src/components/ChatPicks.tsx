import { useEffect, useRef } from 'react'
import { useChatBridge } from '../chatBridge'
import ProductCard from './ProductCard'

// Remembered across remounts so navigating to a product page doesn't re-scroll.
let lastScrolled: object | null = null

// The chat agent's product matches, rendered on the page as regular product
// cards. Each card links to /products/<id>, the same detail view as the grid.
export default function ChatPicks() {
  const { picks, clearPicks } = useChatBridge()
  const ref = useRef<HTMLElement>(null)

  // Bring fresh results into view once, when the chat delivers them.
  useEffect(() => {
    if (picks && picks !== lastScrolled) {
      lastScrolled = picks
      ref.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }, [picks])

  if (!picks) return null

  return (
    <section className="picks" aria-label="Products from chat" ref={ref}>
      <div className="section-head">
        <div>
          <span className="eyebrow">Llama's picks · {picks.products.length} items</span>
          <h2 className="section-title">{picks.title}</h2>
        </div>
        <button className="btn btn-ghost btn-small" onClick={clearPicks}>
          Clear
        </button>
      </div>
      <div className="grid">
        {picks.products.map((p, i) => (
          <ProductCard key={p.product_id} product={p} index={i} />
        ))}
      </div>
    </section>
  )
}
