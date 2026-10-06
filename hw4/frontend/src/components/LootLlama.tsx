// A Fortnite loot llama drawn entirely with CSS (see .llama rules in index.css).
export default function LootLlama({ small = false }: { small?: boolean }) {
  return (
    <div className={small ? 'llama llama-small' : 'llama'} aria-hidden="true">
      <div className="llama-ear llama-ear-left" />
      <div className="llama-ear llama-ear-right" />
      <div className="llama-neck">
        <div className="llama-head">
          <div className="llama-eye llama-eye-left" />
          <div className="llama-eye llama-eye-right" />
          <div className="llama-snout" />
        </div>
      </div>
      <div className="llama-body">
        <div className="llama-saddle" />
      </div>
      <div className="llama-leg llama-leg-1" />
      <div className="llama-leg llama-leg-2" />
      <div className="llama-leg llama-leg-3" />
      <div className="llama-leg llama-leg-4" />
    </div>
  )
}
