"""Campus Customs API: products, images, auth and the shop chatbot.

Run from hw-4/backend/:  uvicorn main:app --reload --port 8000
API docs:                http://127.0.0.1:8000/docs
Frontend (Vite):         http://localhost:5173 (proxies /api and /images here)
"""

from __future__ import annotations

import json
import logging
import sqlite3

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import auth
import safety
import tools
from agent import ShopDeps, is_content_filtered, run_shop_agent
from pydantic_ai.exceptions import UnexpectedModelBehavior, UsageLimitExceeded
from db import DATA_DIR, connect, init_db
from models import (
    AuthResponse,
    ChatHistoryMessage,
    ChatRequest,
    ChatResponse,
    ChatTurn,
    Customer,
    LoginRequest,
    PageContext,
    ProductCard,
    ProductDetail,
    SignupRequest,
    UserPublic,
)

HISTORY_TURNS = 20  # earlier messages sent to the agent as memory
chat_limiter = safety.RateLimiter(max_events=15, window_seconds=60)  # per shopper
log = logging.getLogger("campus_customs")

init_db()
app = FastAPI(title="Campus Customs", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
# image_file_path in the catalogue is products/<file>; /images/<file> serves it.
app.mount("/images", StaticFiles(directory=DATA_DIR / "products"), name="images")


# ---------- auth helpers ----------


def _bearer(authorization: str | None) -> str | None:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip() or None
    return None


def optional_user(authorization: str | None = Header(default=None)) -> UserPublic | None:
    token = _bearer(authorization)
    return auth.user_for_token(token) if token else None


def require_user(user: UserPublic | None = Depends(optional_user)) -> UserPublic:
    if user is None:
        raise HTTPException(status_code=401, detail="Please log in.")
    return user


# ---------- health + products ----------


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/products", response_model=list[ProductCard])
def list_products():
    return tools.list_product_cards()


@app.get("/api/products/{product_id}", response_model=ProductDetail)
def get_product(product_id: str):
    product = tools.get_product_page(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


# ---------- auth ----------


@app.post("/api/auth/signup", response_model=AuthResponse, status_code=201)
def signup(body: SignupRequest):
    email = auth.normalize_email(body.email)
    if not auth.valid_email(email):
        raise HTTPException(status_code=422, detail="Please enter a valid email address.")
    first, last = body.first_name.strip(), body.last_name.strip()
    try:
        with connect() as conn:
            cur = conn.execute(
                "INSERT INTO users (name, email, password_hash, first_name, last_name) VALUES (?, ?, ?, ?, ?)",
                (f"{first} {last}", email, auth.hash_password(body.password), first, last),
            )
            row = conn.execute("SELECT * FROM users WHERE id = ?", (cur.lastrowid,)).fetchone()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="An account with that email already exists.")
    user = auth.to_public(row)
    return AuthResponse(token=auth.create_session(user.id), user=user)


@app.post("/api/auth/login", response_model=AuthResponse)
def login(body: LoginRequest):
    with connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (auth.normalize_email(body.email),)).fetchone()
    # Same message for unknown email and wrong password, so emails can't be probed.
    if row is None or not auth.verify_password(body.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    user = auth.to_public(row)
    return AuthResponse(token=auth.create_session(user.id), user=user)


@app.post("/api/auth/logout", status_code=204)
def logout(authorization: str | None = Header(default=None)):
    token = _bearer(authorization)
    if token:
        auth.delete_session(token)


@app.get("/api/auth/me", response_model=UserPublic)
def me(user: UserPublic = Depends(require_user)):
    return user


# ---------- chat ----------


def _cards_from_json(products_json: str | None) -> list[ProductCard]:
    """Stored rows keep product IDs; re-read them so cards show today's price/stock."""
    if not products_json:
        return []
    try:
        items = json.loads(products_json)
    except json.JSONDecodeError:
        return []
    ids = [i.get("product_id") if isinstance(i, dict) else i for i in items]
    return tools.product_cards([i for i in ids if isinstance(i, str)])


def _load_history(user_id: int, limit: int) -> list[sqlite3.Row]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT role, content, products_json, created_at FROM chat_messages "
            "WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return list(reversed(rows))


def _save_turn(user_id: int, message: str, reply: str, cards: list[ProductCard]) -> None:
    products_json = json.dumps([c.model_dump() for c in cards]) if cards else None
    with connect() as conn:
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content) VALUES (?, 'user', ?)", (user_id, message)
        )
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content, products_json) VALUES (?, 'assistant', ?, ?)",
            (user_id, reply, products_json),
        )


@app.get("/api/chat/history", response_model=list[ChatHistoryMessage])
def chat_history(user: UserPublic = Depends(require_user)):
    return [
        ChatHistoryMessage(
            role=r["role"], content=r["content"], products=_cards_from_json(r["products_json"]), created_at=r["created_at"]
        )
        for r in _load_history(user.id, limit=100)
    ]


@app.post("/api/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, request: Request, user: UserPublic | None = Depends(optional_user)):
    shopper = f"user:{user.id}" if user else f"ip:{request.client.host if request.client else 'unknown'}"
    if not chat_limiter.allow(shopper):
        raise HTTPException(status_code=429, detail="Whoa, that's a lot of messages! Give me a minute to catch up.")

    # Card numbers, SSNs and stated passwords never reach the model or the database.
    message, redactions = safety.redact_sensitive(body.message)

    page = body.page or PageContext()
    if page.product_id:
        page.product_name = tools.product_name(page.product_id)
        if page.product_name is None:
            page.product_id = None

    if user:
        customer = Customer(user_id=user.id, name=user.name, first_name=user.first_name, email=user.email)
        history = [ChatTurn(role=r["role"], content=r["content"]) for r in _load_history(user.id, HISTORY_TURNS)]
    else:
        customer = None
        history = [
            ChatTurn(role=t.role, content=safety.redact_sensitive(t.content)[0]) for t in body.history[-HISTORY_TURNS:]
        ]

    audit_meta = {
        "shopper": f"user {user.id}" if user else "guest",  # id only: no names or emails in the log
        "page": page.product_id or page.path,
        "redactions": redactions,
        "injection_suspected": safety.looks_like_injection(message),
    }
    try:
        result = await run_shop_agent(message, ShopDeps(customer=customer, page=page), history, audit_meta)
    except UnexpectedModelBehavior:
        # Usually the price fact-checker rejected every attempt: refuse to guess.
        return ChatResponse(
            reply="I couldn't double-check those numbers, so I won't guess. The product page always shows the live price and stock."
        )
    except UsageLimitExceeded:
        return ChatResponse(reply="That one took me too many steps. Could you ask in a simpler way, like one item at a time?")
    except Exception as exc:  # noqa: BLE001 - never 500 the chat widget
        if is_content_filtered(exc):
            return ChatResponse(
                reply="I can't help with that one, but I'd love to help you find some Bulldog gear. What are you shopping for?"
            )
        log.exception("agent run failed")
        return ChatResponse(reply="Sorry, I hit a snag reaching my brain just now. Please try again in a moment.")

    reply = result.reply
    if redactions:
        reply = "Heads up: I removed what looked like private info from your message. Please never share card numbers or passwords in chat.\n\n" + reply
    cards = tools.product_cards(result.product_ids)
    if user:
        _save_turn(user.id, message, reply, cards)
    return ChatResponse(reply=reply, products=cards)
