import { createContext, useCallback, useContext, useState, type ReactNode } from 'react'
import type { Product } from './api'

// Shared chat state so the rest of the site can talk to the chat widget:
//  * picks — product cards the agent returned, rendered on the page (Problem 7)
//  * ask   — a question another component wants the llama to answer (Problem 9)
interface Picks {
  title: string
  products: Product[]
}

interface Ask {
  id: number
  text: string
}

interface ChatBridgeState {
  picks: Picks | null
  showPicks: (title: string, products: Product[]) => void
  clearPicks: () => void
  ask: Ask | null
  askLlama: (text: string) => void
}

const ChatBridgeContext = createContext<ChatBridgeState | null>(null)

export function ChatBridgeProvider({ children }: { children: ReactNode }) {
  const [picks, setPicks] = useState<Picks | null>(null)
  const [ask, setAsk] = useState<Ask | null>(null)
  const askLlama = useCallback((text: string) => setAsk({ id: Date.now(), text }), [])

  return (
    <ChatBridgeContext.Provider
      value={{
        picks,
        showPicks: (title, products) => setPicks(products.length ? { title, products } : null),
        clearPicks: () => setPicks(null),
        ask,
        askLlama,
      }}
    >
      {children}
    </ChatBridgeContext.Provider>
  )
}

export function useChatBridge() {
  const ctx = useContext(ChatBridgeContext)
  if (!ctx) throw new Error('useChatBridge must be used inside ChatBridgeProvider')
  return ctx
}
