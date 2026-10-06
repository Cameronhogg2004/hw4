"""Pydantic types shared by main.py, agent.py and tools.py.

Three groups:
  * Catalogue / API  — what the site's product pages and cards render.
  * Auth             — sign-up, login and the public view of a user.
  * Agent / chat     — the agent's structured output, its tool return types,
                       the chat route's request/response contract, and deps context.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# ---------- Catalogue / API ----------


class SizeStock(BaseModel):
    size: str
    quantity: int


class ProductCard(BaseModel):
    """What a product card needs: image, name, price and a short line of info.

    Used by the products grid and by chat results, so the frontend renders both
    with the same component and both link to /products/<product_id>.
    """

    product_id: str
    name: str
    garment_type: str
    price: float
    image_url: str
    short_info: str
    colors: list[str]
    total_stock: int
    sizes_in_stock: list[str] = Field(default_factory=list)
    family: str = Field(default="other", description="hoodies, crewnecks, tees, quarter-zips, jackets or other")


class ProductDetail(ProductCard):
    """Full single-item view: everything on the card plus description, tags and sizes."""

    description: str
    search_tags: list[str]
    sizes: list[SizeStock] = Field(default_factory=list)


# ---------- Auth ----------


class SignupRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=60)
    last_name: str = Field(min_length=1, max_length=60)
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: str
    password: str


class UserPublic(BaseModel):
    """The only user fields that ever leave the server (never the password hash)."""

    id: int
    name: str
    first_name: str
    last_name: str
    email: str


class AuthResponse(BaseModel):
    token: str
    user: UserPublic


# ---------- Agent context (deps) ----------


class Customer(BaseModel):
    """Who is chatting. Built from the logged-in user; None for guests."""

    user_id: int
    name: str
    first_name: str
    email: str


class PageContext(BaseModel):
    """Where the shopper is on the site when they send a message."""

    path: str = "/"
    product_id: str | None = None
    product_name: str | None = None


# ---------- Agent output + tool returns ----------


class ShopReply(BaseModel):
    """The agent's structured output.

    The agent only names products by ID; main.py turns those IDs into
    ProductCards straight from the database, so prices and stock shown on
    cards can never be invented by the model.
    """

    reply: str = Field(description="The message shown to the shopper, in the Campus Customs voice.")
    product_ids: list[str] = Field(
        default_factory=list,
        description=(
            "product_id values (from search_catalogue or get_product_details results) to show as "
            "product cards on the page. Empty when no cards are useful."
        ),
    )


class ProductMatch(BaseModel):
    """One search_catalogue hit: enough to describe and compare, not the full description."""

    product_id: str
    name: str
    garment_type: str
    price: float
    colors: list[str]
    total_stock: int
    sizes_in_stock: list[str]


class SearchResults(BaseModel):
    """search_catalogue result. `count` is the exact number of matches (the
    `products` list is capped at 30), so the agent never has to count by hand."""

    count: int
    price_range: str | None
    products: list[ProductMatch]


class AlternativesResult(BaseModel):
    """find_alternatives result: in-stock look-alikes when a size or color isn't available."""

    based_on: str | None = Field(description="Name of the product the shopper wanted, if known.")
    family: str
    size: str | None
    color: str | None
    count: int
    alternatives: list[ProductMatch]


class ProductInfo(BaseModel):
    """get_product_details result: the full record plus stock by size."""

    product_id: str
    name: str
    garment_type: str
    description: str
    colors: list[str]
    price: float
    total_stock: int
    sizes: list[SizeStock]
    sold_out_sizes: list[str]


class StockReport(BaseModel):
    """check_stock result. `message` is a plain-English summary the agent can relay."""

    product_id: str
    name: str
    size: str | None
    quantity: int
    in_stock: bool
    sizes: list[SizeStock]
    message: str


# ---------- Chat API ----------


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    page: PageContext | None = None
    # Guests only: the browser sends the recent conversation because the server
    # stores nothing for them. Logged-in history is loaded from the database.
    history: list[ChatTurn] = Field(default_factory=list, max_length=40)


class ChatResponse(BaseModel):
    reply: str
    products: list[ProductCard] = Field(default_factory=list)


class ChatHistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    products: list[ProductCard] = Field(default_factory=list)
    created_at: str
