import { useCallback, useEffect, useRef, useState, type FormEvent } from 'react'
import { Link, matchPath, useLocation } from 'react-router-dom'
import { ApiError, fetchChatHistory, sendChatMessage, type ChatMessage } from '../api'
import { useAuth } from '../auth'
import { useChatBridge } from '../chatBridge'
import { formatPrice } from '../rarity'
import ChatText from './ChatText'
import LootLlama from './LootLlama'

const MINI_CARDS = 4
const SEEN_KEY = 'cc_chat_seen'

// Problem 9: quick replies change with the page so shoppers see what the llama can do.
const PRODUCT_PAGE_PROMPTS = ['Is this in stock in M?', 'What colors does it come in?', 'Show me similar items']
const BROWSE_PROMPTS = ['What hoodies do you have?', 'Gifts under $40', 'Crewnecks in navy']

function greeting(firstName?: string): ChatMessage {
  return {
    role: 'assistant',
    content: firstName
      ? `Welcome back, ${firstName}! Ask me about hoodies, sizes or what's in stock.`
      : "Hey, I'm the Campus Customs llama. Ask me about hoodies, sizes or what's in stock.",
  }
}

export default function ChatWidget() {
  const { user, token, ready } = useAuth()
  const { showPicks, ask } = useChatBridge()
  const location = useLocation()
  const [open, setOpen] = useState(false)
  const [seen, setSeen] = useState(() => localStorage.getItem(SEEN_KEY) === '1')
  const [messages, setMessages] = useState<ChatMessage[]>([greeting()])
  const [draft, setDraft] = useState('')
  const [sending, setSending] = useState(false)
  const logRef = useRef<HTMLDivElement>(null)
  const messagesRef = useRef(messages)
  messagesRef.current = messages

  // Page context: on /products/:productId the agent is told which item "it" is.
  const productId = matchPath('/products/:productId', location.pathname)?.params.productId ?? null
  const quickReplies = productId ? PRODUCT_PAGE_PROMPTS : BROWSE_PROMPTS

  // Logged in: reload saved history from the database. Logged out: fresh guest chat.
  useEffect(() => {
    if (!ready) return
    if (!token) {
      setMessages([greeting()])
      return
    }
    fetchChatHistory(token)
      .then((history) => setMessages([greeting(user?.first_name), ...history]))
      .catch(() => setMessages([greeting(user?.first_name)]))
  }, [ready, token, user?.first_name])

  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, open, sending])

  const openPanel = useCallback(() => {
    setOpen(true)
    setSeen(true)
    localStorage.setItem(SEEN_KEY, '1')
  }, [])

  const send = useCallback(
    async (text: string) => {
      if (!text.trim()) return
      const guestHistory = messagesRef.current.slice(1) // skip the local greeting
      setMessages((prev) => [...prev, { role: 'user', content: text }])
      setDraft('')
      setSending(true)
      try {
        const res = await sendChatMessage(text, { path: location.pathname, product_id: productId }, token, guestHistory)
        setMessages((prev) => [...prev, { role: 'assistant', content: res.reply, products: res.products }])
        if (res.products.length) showPicks(`Results for “${text}”`, res.products)
      } catch (err) {
        const content =
          err instanceof ApiError && err.status === 429 ? err.message : 'The storm hit my connection. Try again in a sec.'
        setMessages((prev) => [...prev, { role: 'assistant', content }])
      } finally {
        setSending(false)
      }
    },
    [location.pathname, productId, token, showPicks],
  )

  // "Ask the llama" buttons elsewhere on the site open the chat and send their question.
  useEffect(() => {
    if (!ask) return
    openPanel()
    void send(ask.text)
    // Only when a new ask arrives.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ask?.id])

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!sending) void send(draft.trim())
  }

  return (
    <div className="chat">
      {open && (
        <section className="chat-panel" aria-label="Campus Customs chat">
          <header className="chat-header">
            <div className="chat-header-llama">
              <LootLlama small />
            </div>
            <div>
              <strong>Llama Assistant</strong>
              <span className="chat-status">
                <span className="chat-dot" /> {user ? `Online · chatting as ${user.first_name}` : 'Online · guest chat'}
              </span>
            </div>
            <button className="chat-close" onClick={() => setOpen(false)} aria-label="Close chat">
              ×
            </button>
          </header>
          <div className="chat-log" ref={logRef}>
            {messages.map((m, i) => (
              <div key={i} className={`chat-row chat-row-${m.role}`}>
                {m.role === 'assistant' && <span className="chat-avatar" aria-hidden="true" />}
                <div className={`chat-bubble chat-${m.role}`}>
                  <ChatText text={m.content} />
                  {m.products && m.products.length > 0 && (
                    <div className="chat-cards">
                      {m.products.slice(0, MINI_CARDS).map((p) => (
                        <Link key={p.product_id} to={`/products/${p.product_id}`} className="chat-card">
                          <img src={p.image_url} alt="" />
                          <span className="chat-card-name">{p.name}</span>
                          <span className="chat-card-price">{formatPrice(p.price)}</span>
                        </Link>
                      ))}
                      <button className="chat-cards-more" onClick={() => showPicks('From your chat', m.products!)}>
                        {m.products.length > MINI_CARDS ? `Show all ${m.products.length} on page` : 'Show on page'}
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
            {sending && (
              <div className="chat-row chat-row-assistant">
                <span className="chat-avatar" aria-hidden="true" />
                <div className="chat-bubble chat-assistant chat-typing" aria-label="Llama is typing">
                  <span />
                  <span />
                  <span />
                </div>
              </div>
            )}
          </div>
          <div className="chat-chips" aria-label="Suggested questions">
            {quickReplies.map((q) => (
              <button key={q} className="chat-chip" disabled={sending} onClick={() => void send(q)}>
                {q}
              </button>
            ))}
          </div>
          <form className="chat-form" onSubmit={handleSubmit}>
            <input
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              placeholder={productId ? 'Ask about this item…' : 'Ask about gear…'}
              aria-label="Chat message"
              maxLength={2000}
            />
            <button type="submit" disabled={sending || !draft.trim()}>
              Send
            </button>
          </form>
        </section>
      )}
      <button
        className={open ? 'chat-launcher chat-launcher-open' : 'chat-launcher'}
        onClick={() => (open ? setOpen(false) : openPanel())}
        aria-label={open ? 'Close chat' : 'Open chat with the Campus Customs llama'}
      >
        {open ? <span className="chat-launcher-x">×</span> : <LootLlama small />}
        {!seen && !open && <span className="chat-badge">1</span>}
      </button>
      {!seen && !open && <div className="chat-nudge">Need your size? Ask me!</div>}
    </div>
  )
}
