// Thin client for the FastAPI backend in ../backend/main.py.
// Vite proxies /api and /images to it, so every URL here is relative.

/** Card-level product: the products grid and chat results both use this shape. */
export interface Product {
  product_id: string
  name: string
  garment_type: string
  price: number
  image_url: string
  short_info: string
  colors: string[]
  total_stock: number
  sizes_in_stock: string[]
  family: string
}

export interface SizeStock {
  size: string
  quantity: number
}

export interface ProductDetail extends Product {
  description: string
  search_tags: string[]
  sizes: SizeStock[]
}

export interface User {
  id: number
  name: string
  first_name: string
  last_name: string
  email: string
}

export interface AuthResponse {
  token: string
  user: User
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  products?: Product[]
}

export interface PageContext {
  path: string
  product_id?: string | null
}

export interface ChatResponse {
  reply: string
  products: Product[]
}

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function request<T>(url: string, init: RequestInit = {}, token?: string | null): Promise<T> {
  const headers = new Headers(init.headers)
  if (init.body) headers.set('Content-Type', 'application/json')
  if (token) headers.set('Authorization', `Bearer ${token}`)
  const res = await fetch(url, { ...init, headers })
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`
    try {
      const body = await res.json()
      if (typeof body.detail === 'string') detail = body.detail
      else if (Array.isArray(body.detail)) detail = body.detail.map((d: { msg: string }) => d.msg).join(', ')
    } catch {
      /* keep status text */
    }
    throw new ApiError(res.status, detail)
  }
  return (res.status === 204 ? undefined : await res.json()) as T
}

// ---------- products ----------

export const fetchProducts = () => request<Product[]>('/api/products')

export const fetchProduct = (id: string) => request<ProductDetail>(`/api/products/${encodeURIComponent(id)}`)

// ---------- auth ----------

export const login = (email: string, password: string) =>
  request<AuthResponse>('/api/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) })

export const signup = (data: { first_name: string; last_name: string; email: string; password: string }) =>
  request<AuthResponse>('/api/auth/signup', { method: 'POST', body: JSON.stringify(data) })

export const fetchMe = (token: string) => request<User>('/api/auth/me', {}, token)

export const logout = (token: string) => request<void>('/api/auth/logout', { method: 'POST' }, token)

// ---------- chat ----------

/**
 * Send one message to the shop agent. Logged-in shoppers' history lives in the
 * database, so it's only sent from the browser for guests.
 */
export const sendChatMessage = (
  message: string,
  page: PageContext,
  token: string | null,
  guestHistory: ChatMessage[],
) =>
  request<ChatResponse>(
    '/api/chat',
    {
      method: 'POST',
      body: JSON.stringify({
        message,
        page,
        history: token ? [] : guestHistory.slice(-20).map(({ role, content }) => ({ role, content })),
      }),
    },
    token,
  )

export const fetchChatHistory = (token: string) => request<ChatMessage[]>('/api/chat/history', {}, token)
