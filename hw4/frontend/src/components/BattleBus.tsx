// The Battle Bus, hanging from its balloon, drawn entirely in CSS (.bus rules in index.css).
export default function BattleBus() {
  return (
    <div className="bus-flight" aria-hidden="true">
      <div className="bus-balloon">
        <span className="bus-balloon-y">Y</span>
      </div>
      <div className="bus-ropes" />
      <div className="bus">
        <div className="bus-roof" />
        <div className="bus-windows">
          <span />
          <span />
          <span />
          <span />
        </div>
        <div className="bus-stripe">CAMPUS CUSTOMS</div>
        <div className="bus-wheel bus-wheel-front" />
        <div className="bus-wheel bus-wheel-back" />
      </div>
      <div className="bus-trail" />
    </div>
  )
}
