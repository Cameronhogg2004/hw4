"""Catalogue and stock lookups over data/campus_customs.db.

Plain functions (no LLM) so they can be tested directly. agent.py wraps the
agent-facing ones as tools; main.py reuses the same queries for the product
pages, so the site and the chatbot always read identical numbers.
"""

from __future__ import annotations

import json
import re
import sqlite3

from db import connect
from models import AlternativesResult, ProductCard, ProductDetail, ProductInfo, ProductMatch, SizeStock, StockReport

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]
SIZE_ALIASES = {
    "EXTRA SMALL": "XS", "SMALL": "S", "MEDIUM": "M", "MED": "M", "LARGE": "L",
    "EXTRA LARGE": "XL", "XXXL": "XXL", "2XL": "XXL", "2X": "XXL", "XX LARGE": "XXL",
}
MAX_RESULTS = 30
MAX_ALTERNATIVES = 6

# Shoppers say "hoodie" but the catalogue also says "hooded sweatshirt"; each
# query word expands to every spelling the catalogue uses for it.
SYNONYMS = {
    "hoodie": ["hoodie", "hooded", "hood"],
    "hoody": ["hoodie", "hooded", "hood"],
    "hooded": ["hoodie", "hooded", "hood"],
    "tee": ["t shirt", "tee"],
    "tshirt": ["t shirt", "tee"],
    # Not "crew neck": T-shirt descriptions say "crew-neck", which isn't a crewneck sweatshirt.
    "crew": ["crewneck"],
    "crewneck": ["crewneck"],
    "sweatshirt": ["sweatshirt", "crewneck", "hoodie", "hooded"],
    "sweater": ["sweatshirt", "crewneck", "quarter zip"],
    "quarterzip": ["quarter zip", "1 4 zip", "quarter-zip"],
    "zip": ["zip"],
    "jacket": ["jacket", "fleece", "bomber"],
    "coat": ["jacket", "fleece"],
    "fleece": ["fleece"],
    "gray": ["gray", "grey"],
    "grey": ["gray", "grey"],
    "blue": ["blue", "navy"],
}
STOPWORDS = {
    "a", "an", "and", "any", "are", "do", "for", "got", "have", "i", "in", "is", "me", "of",
    "or", "please", "show", "some", "the", "what", "which", "with", "you", "your", "all",
    "options", "items", "stuff", "gear", "merch", "something", "looking", "want", "need",
}

PRODUCT_QUERY = """
    SELECT c.*, COALESCE(SUM(i.quantity), 0) AS total_stock,
           GROUP_CONCAT(CASE WHEN i.quantity > 0 THEN i.size END) AS sizes_csv
    FROM catalogue c LEFT JOIN inventory i ON i.product_id = c.product_id
"""

# Garment families used by the shop filters and find_alternatives. The catalogue
# has 22 spellings of garment_type; these collapse them into what shoppers browse.
FAMILIES = (
    ("quarter-zips", ("quarter",)),
    ("hoodies", ("hood",)),
    ("jackets", ("jacket", "fleece")),
    ("tees", ("t-shirt", "tee", "performance shirt")),
    ("crewnecks", ("crewneck", "mockneck")),
)


# ---------- row helpers ----------


def _normalize(text: str) -> str:
    text = text.lower().replace("1/4", "1 4").replace("-", " ")
    return re.sub(r"[^a-z0-9 ]+", " ", text)


def _short_info(row: sqlite3.Row) -> str:
    first_sentence = row["description"].split(". ")[0].rstrip(".")
    return first_sentence if len(first_sentence) <= 110 else first_sentence[:107].rstrip() + "…"


def _image_url(row: sqlite3.Row) -> str:
    return "/images/" + row["image_file_path"].removeprefix("products/")


def garment_family(garment_type: str) -> str:
    lowered = garment_type.lower()
    for family, needles in FAMILIES:
        if any(n in lowered for n in needles):
            return family
    return "other"


def _in_stock_sizes(row: sqlite3.Row) -> list[str]:
    sizes = (row["sizes_csv"] or "").split(",")
    return sorted((s for s in sizes if s), key=lambda s: SIZE_ORDER.index(s) if s in SIZE_ORDER else 99)


def _match(row: sqlite3.Row) -> ProductMatch:
    return ProductMatch(
        product_id=row["product_id"],
        name=row["name"],
        garment_type=row["garment_type"],
        price=row["price"],
        colors=json.loads(row["colors"]),
        total_stock=row["total_stock"],
        sizes_in_stock=_in_stock_sizes(row),
    )


def _card(row: sqlite3.Row) -> ProductCard:
    return ProductCard(
        product_id=row["product_id"],
        name=row["name"],
        garment_type=row["garment_type"],
        price=row["price"],
        image_url=_image_url(row),
        short_info=_short_info(row),
        colors=json.loads(row["colors"]),
        total_stock=row["total_stock"],
        sizes_in_stock=_in_stock_sizes(row),
        family=garment_family(row["garment_type"]),
    )


def _sizes(conn: sqlite3.Connection, product_id: str) -> list[SizeStock]:
    rows = conn.execute("SELECT size, quantity FROM inventory WHERE product_id = ?", (product_id,)).fetchall()
    sizes = [SizeStock(size=r["size"], quantity=r["quantity"]) for r in rows]
    return sorted(sizes, key=lambda s: SIZE_ORDER.index(s.size) if s.size in SIZE_ORDER else 99)


def _all_rows(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(PRODUCT_QUERY + " GROUP BY c.product_id ORDER BY c.name").fetchall()


def normalize_size(size: str) -> str:
    key = size.strip().upper().replace("-", " ")
    return SIZE_ALIASES.get(key, key)


# ---------- product pages (main.py) ----------


def list_product_cards() -> list[ProductCard]:
    with connect() as conn:
        return [_card(r) for r in _all_rows(conn)]


def get_product_page(product_id: str) -> ProductDetail | None:
    with connect() as conn:
        row = conn.execute(PRODUCT_QUERY + " WHERE c.product_id = ? GROUP BY c.product_id", (product_id,)).fetchone()
        if row is None:
            return None
        return ProductDetail(
            **_card(row).model_dump(),
            description=row["description"],
            search_tags=json.loads(row["search_tags"]),
            sizes=_sizes(conn, product_id),
        )


def product_cards(product_ids: list[str]) -> list[ProductCard]:
    """Turn agent-chosen IDs into cards from the database, keeping order, dropping unknown IDs."""
    if not product_ids:
        return []
    with connect() as conn:
        by_id = {r["product_id"]: r for r in _all_rows(conn)}
    seen: list[str] = []
    for pid in product_ids:
        if pid in by_id and pid not in seen:
            seen.append(pid)
    return [_card(by_id[pid]) for pid in seen[:MAX_RESULTS]]


def product_name(product_id: str) -> str | None:
    with connect() as conn:
        row = conn.execute("SELECT name FROM catalogue WHERE product_id = ?", (product_id,)).fetchone()
    return row["name"] if row else None


# ---------- agent tools ----------


def search_catalogue(
    query: str,
    color: str | None = None,
    max_price: float | None = None,
    in_stock_only: bool = False,
    limit: int | None = MAX_RESULTS,
) -> list[ProductMatch]:
    """Keyword search over name, garment type, description, colors and tags.

    Every query word must match (via SYNONYMS); if nothing matches all words,
    fall back to products matching any word, ranked by where the words landed.
    """
    text = f" {_normalize(query)} "
    for phrase, token in ((" quarter zip", " quarterzip"), (" 1 4 zip", " quarterzip"), (" t shirt", " tshirt"), (" tee shirt", " tshirt")):
        text = text.replace(phrase, token)
    terms = [w for w in text.split() if w not in STOPWORDS and len(w) > 1]
    # Plural to singular: hoodies -> hoodie, shirts -> shirt, tshirts -> tshirt.
    terms = [t[:-1] if t.endswith("s") and not t.endswith("ss") and len(t) > 3 else t for t in terms]
    alternatives = [SYNONYMS.get(t, [t]) for t in terms]

    with connect() as conn:
        rows = _all_rows(conn)

    def keep(row: sqlite3.Row) -> bool:
        if max_price is not None and row["price"] > max_price:
            return False
        if in_stock_only and row["total_stock"] == 0:
            return False
        if color:
            wanted = SYNONYMS.get(color.lower().strip(), [color.lower().strip()])
            if not any(w in c.lower() for c in json.loads(row["colors"]) for w in wanted):
                return False
        return True

    def score(row: sqlite3.Row) -> tuple[int, int]:
        fields = (
            (_normalize(row["name"]), 6),
            (_normalize(row["garment_type"]), 5),
            (_normalize(" ".join(json.loads(row["colors"]))), 3),
            (_normalize(" ".join(json.loads(row["search_tags"]))), 2),
            (_normalize(row["description"]), 1),
        )
        matched, total = 0, 0
        for alts in alternatives:
            best = max((w for text, w in fields if any(a in text for a in alts)), default=0)
            matched += best > 0
            total += best
        return matched, total

    candidates = [r for r in rows if keep(r)]
    if alternatives:
        scored = [(score(r), r) for r in candidates]
        hits = [(s, r) for s, r in scored if s[0] == len(alternatives)]
        if not hits:
            hits = [(s, r) for s, r in scored if s[0] > 0]
        hits.sort(key=lambda sr: (-sr[0][0], -sr[0][1], sr[1]["name"]))
        candidates = [r for _, r in hits]

    return [_match(r) for r in (candidates if limit is None else candidates[: max(1, limit)])]


def resolve_product_id(ref: str) -> str | None:
    """Accept an exact product_id, a product name, or a close description."""
    ref = ref.strip()
    with connect() as conn:
        row = conn.execute(
            "SELECT product_id FROM catalogue WHERE product_id = ? OR lower(name) = lower(?)", (ref, ref)
        ).fetchone()
    if row:
        return row["product_id"]
    hits = search_catalogue(ref.replace("-", " "), limit=1)
    return hits[0].product_id if hits else None


def get_product_details(product_id: str) -> ProductInfo | None:
    pid = resolve_product_id(product_id)
    if pid is None:
        return None
    with connect() as conn:
        row = conn.execute(PRODUCT_QUERY + " WHERE c.product_id = ? GROUP BY c.product_id", (pid,)).fetchone()
        sizes = _sizes(conn, pid)
    return ProductInfo(
        product_id=pid,
        name=row["name"],
        garment_type=row["garment_type"],
        description=row["description"],
        colors=json.loads(row["colors"]),
        price=row["price"],
        total_stock=row["total_stock"],
        sizes=sizes,
        sold_out_sizes=[s.size for s in sizes if s.quantity == 0],
    )


def check_stock(product_id: str, size: str | None = None) -> StockReport | None:
    info = get_product_details(product_id)
    if info is None:
        return None
    if size is None:
        in_stock = [f"{s.size} ({s.quantity})" for s in info.sizes if s.quantity > 0]
        message = (
            f"{info.name}: {info.total_stock} in stock. Available: {', '.join(in_stock)}."
            + (f" Sold out: {', '.join(info.sold_out_sizes)}." if info.sold_out_sizes else "")
            if info.total_stock
            else f"{info.name} is sold out in every size."
        )
        return StockReport(
            product_id=info.product_id, name=info.name, size=None, quantity=info.total_stock,
            in_stock=info.total_stock > 0, sizes=info.sizes, message=message,
        )

    wanted = normalize_size(size)
    match = next((s for s in info.sizes if s.size == wanted), None)
    if match is None:
        message = f"{info.name} doesn't come in size {size}. Sizes offered: {', '.join(s.size for s in info.sizes)}."
        quantity = 0
    elif match.quantity == 0:
        others = [s.size for s in info.sizes if s.quantity > 0]
        message = f"{info.name} is OUT OF STOCK in {wanted}." + (
            f" Still available in: {', '.join(others)}." if others else " It is sold out in every size."
        )
        quantity = 0
    else:
        message = f"{info.name} is in stock in {wanted}: {match.quantity} left."
        quantity = match.quantity
    return StockReport(
        product_id=info.product_id, name=info.name, size=wanted, quantity=quantity,
        in_stock=quantity > 0, sizes=info.sizes, message=message,
    )


def find_alternatives(
    product_id: str | None = None,
    size: str | None = None,
    color: str | None = None,
    family: str | None = None,
) -> AlternativesResult:
    """In-stock look-alikes: same garment family, has the size, matches the color.

    Ranked by shared search tags (same college/sport/style), then closeness in price.
    """
    wanted_size = normalize_size(size) if size else None
    wanted_color = color.lower().strip() if color else None
    color_words = SYNONYMS.get(wanted_color, [wanted_color]) if wanted_color else []

    with connect() as conn:
        rows = _all_rows(conn)
    base = None
    if product_id:
        pid = resolve_product_id(product_id)
        base = next((r for r in rows if r["product_id"] == pid), None)
    fam = garment_family(base["garment_type"]) if base else (family or "other")
    base_tags = {t.lower() for t in json.loads(base["search_tags"])} if base else set()
    generic = {"yale", "campus customs", "college merch", "yale merch"}

    scored = []
    for r in rows:
        if base is not None and r["product_id"] == base["product_id"]:
            continue
        if fam != "other" and garment_family(r["garment_type"]) != fam:
            continue
        in_stock = _in_stock_sizes(r)
        if not in_stock or (wanted_size and wanted_size not in in_stock):
            continue
        if color_words and not any(w in c.lower() for c in json.loads(r["colors"]) for w in color_words):
            continue
        shared = len(({t.lower() for t in json.loads(r["search_tags"])} & base_tags) - generic)
        price_gap = abs(r["price"] - base["price"]) if base else 0
        scored.append((-shared, price_gap, r["name"], r))

    scored.sort(key=lambda x: x[:3])
    picks = [_match(r) for *_, r in scored[:MAX_ALTERNATIVES]]
    return AlternativesResult(
        based_on=base["name"] if base else None,
        family=fam,
        size=wanted_size,
        color=wanted_color,
        count=len(scored),
        alternatives=picks,
    )
