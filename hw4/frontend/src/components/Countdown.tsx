import { useEffect, useState } from 'react'

// Item-shop style "resets in" timer, counting down to local midnight.
function untilMidnight(): string {
  const now = new Date()
  const midnight = new Date(now)
  midnight.setHours(24, 0, 0, 0)
  const total = Math.max(0, Math.floor((midnight.getTime() - now.getTime()) / 1000))
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${pad(Math.floor(total / 3600))}:${pad(Math.floor((total % 3600) / 60))}:${pad(total % 60)}`
}

export default function Countdown({ label = 'Daily drops refresh in' }: { label?: string }) {
  const [time, setTime] = useState(untilMidnight)
  useEffect(() => {
    const id = setInterval(() => setTime(untilMidnight()), 1000)
    return () => clearInterval(id)
  }, [])
  return (
    <span className="countdown">
      <span className="countdown-label">{label}</span>
      <span className="countdown-time">{time}</span>
    </span>
  )
}
