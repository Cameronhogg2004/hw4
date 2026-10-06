"""Campus Customs shop agent: PydanticAI + gpt-5.6-luna through Portkey.

Loading:
  * system prompt  — prompts/AI_prompt.md, read once at import
  * model          — gpt-5.6-luna via Portkey's OpenAI-compatible gateway,
                     authenticated with PORTKEY_API_KEY from the course-root .env
  * output         — ShopReply (reply text + product_ids for cards), checked by
                     a price fact-checker before it reaches the shopper
  * deps           — ShopDeps: who is chatting, which page they're on, and a
                     per-run tool log; every tool receives it through RunContext
  * limits         — 6 model requests / 8 tool calls per message (USAGE_LIMITS)

main.py calls run_shop_agent(message, deps, history) and gets a ShopReply back.
Every run, successful or not, is appended to output/audit_trail.json.
"""

from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import BaseModel
from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.exceptions import ModelHTTPError, UnexpectedModelBehavior, UsageLimitExceeded
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    ToolReturnPart,
    UserPromptPart,
)
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.usage import UsageLimits

import audit
import tools as shop_tools
from models import (
    AlternativesResult,
    ChatTurn,
    Customer,
    PageContext,
    ProductInfo,
    SearchResults,
    ShopReply,
    StockReport,
)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PROMPT_PATH = HERE / "prompts" / "AI_prompt.md"

MODEL_NAME = "gpt-5.6-luna"
PORTKEY_BASE_URL = "https://api.portkey.ai/v1"
USAGE_LIMITS = UsageLimits(request_limit=6, tool_calls_limit=8)
OUTPUT_RETRIES = 2  # fact-check / validation retries before giving up
PRICE_RE = re.compile(r"\$\s?(\d{1,4}(?:,\d{3})*(?:\.\d{1,2})?)")
NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")


def _load_env() -> None:
    """Load .env files from hw-4 up to the home directory; the nearest wins."""
    for folder in [ROOT, *ROOT.parents]:
        if (folder / ".env").is_file():
            load_dotenv(folder / ".env")
        if folder == Path.home():
            break


_load_env()
PORTKEY_API_KEY = os.environ.get("PORTKEY_API_KEY")
if not PORTKEY_API_KEY:
    raise RuntimeError("PORTKEY_API_KEY is missing. Add it to the course-root .env file.")

_client = AsyncOpenAI(
    api_key=PORTKEY_API_KEY,
    base_url=PORTKEY_BASE_URL,
    default_headers={"x-portkey-api-key": PORTKEY_API_KEY},
)
model = OpenAIResponsesModel(MODEL_NAME, provider=OpenAIProvider(openai_client=_client))


@dataclass
class ShopDeps:
    """Per-request context handed to the instructions, every tool and the validator."""

    customer: Customer | None
    page: PageContext | None
    tool_log: list[dict] = field(default_factory=list)
    fact_check_retries: list[str] = field(default_factory=list)

    def log(self, tool: str, args: dict, result: str) -> None:
        self.tool_log.append(
            {"time": audit.now_iso(), "tool": tool, "args": {k: v for k, v in args.items() if v is not None},
             "result": audit.clip(result)}
        )


agent = Agent(
    model,
    deps_type=ShopDeps,
    output_type=ShopReply,
    instructions=PROMPT_PATH.read_text(encoding="utf-8"),
    retries=OUTPUT_RETRIES,
)


@agent.instructions
def context(ctx: RunContext[ShopDeps]) -> str:
    """Per-run Context section: customer identity and current page."""
    c, page = ctx.deps.customer, ctx.deps.page
    customer = f"{c.name} (first name {c.first_name}), email {c.email}, logged in" if c else "guest (not logged in)"
    if page and page.product_id:
        where = f"product page for {page.product_name!r} (product_id: {page.product_id}), path {page.path}"
    else:
        where = f"{page.path if page else '/'} (not a product page)"
    return f"## Context\n- Customer: {customer}\n- Page: {where}"


def _page_product(ctx: RunContext[ShopDeps], product_id: str | None) -> str | None:
    if product_id:
        return product_id
    return ctx.deps.page.product_id if ctx.deps.page else None


NO_PRODUCT = "No product given and the shopper isn't on a product page. Ask which item they mean."


@agent.tool
def search_catalogue(
    ctx: RunContext[ShopDeps],
    query: str,
    color: str | None = None,
    max_price: float | None = None,
    in_stock_only: bool = False,
) -> SearchResults:
    """Search the catalogue by garment type, name, team, college or style words.

    Use for "what X do you have" questions and to find alternatives. Put the
    returned product_ids in ShopReply.product_ids to show them as cards.

    Args:
        query: Words like "hoodie", "navy crewneck", "baseball", "Berkeley quarter zip".
        color: Only items whose color list contains this color (e.g. "pink", "navy").
        max_price: Only items at or under this price in dollars.
        in_stock_only: Skip items that are sold out in every size.
    """
    matches = shop_tools.search_catalogue(
        query, color=color, max_price=max_price, in_stock_only=in_stock_only, limit=None
    )
    prices = [m.price for m in matches]
    price_range = f"${min(prices):.2f}–${max(prices):.2f}" if prices else None
    ctx.deps.log(
        "search_catalogue",
        {"query": query, "color": color, "max_price": max_price, "in_stock_only": in_stock_only or None},
        f"{len(matches)} matches {price_range or ''}",
    )
    # count covers every match; the list is capped so the model's context stays small.
    return SearchResults(count=len(matches), price_range=price_range, products=matches[: shop_tools.MAX_RESULTS])


@agent.tool
def get_product_details(ctx: RunContext[ShopDeps], product_id: str | None = None) -> ProductInfo | str:
    """Full record for one product: description, colors, exact price and stock by size.

    Args:
        product_id: The product's ID (or exact name). Leave empty to use the
            product on the shopper's current page.
    """
    pid = _page_product(ctx, product_id)
    info = shop_tools.get_product_details(pid) if pid else None
    result = info or (f"No product found for {pid!r}." if pid else NO_PRODUCT)
    ctx.deps.log(
        "get_product_details",
        {"product_id": pid},
        f"{info.name} ${info.price:.2f}, {info.total_stock} in stock" if info else str(result),
    )
    return result


@agent.tool
def check_stock(ctx: RunContext[ShopDeps], product_id: str | None = None, size: str | None = None) -> StockReport | str:
    """Exact stock for a product, either for one size or for every size.

    Args:
        product_id: The product's ID (or exact name). Leave empty for the
            product on the shopper's current page.
        size: XS, S, M, L, XL or XXL ("medium", "large" also work). Leave empty for all sizes.
    """
    pid = _page_product(ctx, product_id)
    report = shop_tools.check_stock(pid, size) if pid else None
    result = report or (f"No product found for {pid!r}." if pid else NO_PRODUCT)
    ctx.deps.log("check_stock", {"product_id": pid, "size": size}, report.message if report else str(result))
    return result


@agent.tool
def find_alternatives(
    ctx: RunContext[ShopDeps],
    product_id: str | None = None,
    size: str | None = None,
    color: str | None = None,
    family: str | None = None,
) -> AlternativesResult:
    """Similar items that ARE available: same garment family, in stock in `size`, matching `color`.

    Call this whenever a requested size is sold out or a color isn't offered,
    and show the results as product cards.

    Args:
        product_id: The item the shopper wanted (empty = current page's product).
        size: The size they need (XS–XXL), if any.
        color: The color they want, if any.
        family: Only when there's no product: hoodies, crewnecks, tees, quarter-zips or jackets.
    """
    pid = _page_product(ctx, product_id)
    result = shop_tools.find_alternatives(pid, size=size, color=color, family=family)
    ctx.deps.log(
        "find_alternatives",
        {"product_id": pid, "size": size, "color": color, "family": family},
        f"{result.count} alternatives: " + ", ".join(a.name for a in result.alternatives[:3]),
    )
    return result


@agent.tool
def get_customer_profile(ctx: RunContext[ShopDeps]) -> dict:
    """The current shopper's name and email (only theirs), or guest status."""
    c = ctx.deps.customer
    ctx.deps.log("get_customer_profile", {}, "logged in" if c else "guest")
    if c is None:
        return {"logged_in": False}
    return {"logged_in": True, "name": c.name, "first_name": c.first_name, "email": c.email}


def _evidence_numbers(ctx: RunContext[ShopDeps]) -> set[float]:
    """Every number that appeared in this run's tool results or the shopper's message."""
    texts: list[str] = [ctx.prompt if isinstance(ctx.prompt, str) else ""]
    for message in ctx.messages:
        for part in getattr(message, "parts", []):
            if isinstance(part, ToolReturnPart):
                content = part.content
                texts.append(content.model_dump_json() if isinstance(content, BaseModel) else str(content))
    return {round(float(n), 2) for t in texts for n in NUMBER_RE.findall(t.replace(",", ""))}


@agent.output_validator
def fact_check(ctx: RunContext[ShopDeps], output: ShopReply) -> ShopReply:
    """Reject replies that quote a price no tool returned, or cite unknown product IDs."""
    unknown = [pid for pid in output.product_ids if shop_tools.product_name(pid) is None]
    if unknown:
        ctx.deps.fact_check_retries.append(f"unknown product_ids {unknown}")
        raise ModelRetry(f"These product_ids don't exist: {unknown}. Use only IDs returned by a tool.")

    quoted = {round(float(p.replace(",", "")), 2) for p in PRICE_RE.findall(output.reply)}
    unsupported = sorted(quoted - _evidence_numbers(ctx))
    if unsupported:
        ctx.deps.fact_check_retries.append(f"unsupported prices {unsupported}")
        shown = ", ".join(f"${p:.2f}" for p in unsupported)
        raise ModelRetry(
            f"Your reply quotes {shown}, but no tool result in this turn contains that price. "
            "Call get_product_details or search_catalogue and quote prices exactly as returned."
        )
    return output


def is_content_filtered(exc: Exception) -> bool:
    """Azure (behind Portkey) rejects jailbreak-style prompts with a 400 content-filter error."""
    text = str(exc).lower()
    return "content management policy" in text or "content_filter" in text


def to_model_history(turns: list[ChatTurn]) -> list[ModelMessage]:
    """Rebuild earlier turns as PydanticAI messages so the agent remembers the chat."""
    history: list[ModelMessage] = []
    for turn in turns:
        if turn.role == "user":
            history.append(ModelRequest(parts=[UserPromptPart(content=turn.content)]))
        else:
            history.append(ModelResponse(parts=[TextPart(content=turn.content)]))
    return history


async def run_shop_agent(
    message: str, deps: ShopDeps, history: list[ChatTurn], audit_meta: dict | None = None
) -> ShopReply:
    """One agent loop. Always appends an audit entry; re-raises failures for main.py."""
    started, t0 = audit.now_iso(), time.perf_counter()
    output: ShopReply | None = None
    usage, error, stop = None, None, "unknown"
    try:
        result = await agent.run(
            message, deps=deps, message_history=to_model_history(history), usage_limits=USAGE_LIMITS
        )
        output = result.output
        usage = result.usage() if callable(result.usage) else result.usage
        stop = f"final answer after {len(deps.tool_log)} tool call(s)"
        if deps.fact_check_retries:
            stop += f" and {len(deps.fact_check_retries)} fact-check retry(ies)"
        return output
    except UsageLimitExceeded as exc:
        stop, error = "stopped: usage limit reached", audit.clip(exc, 300)
        raise
    except UnexpectedModelBehavior as exc:
        stop, error = "stopped: output failed validation (fact-check) after retries", audit.clip(exc, 300)
        raise
    except ModelHTTPError as exc:
        if is_content_filtered(exc):
            stop = "blocked: provider content filter"
        else:
            stop = f"failed: {type(exc).__name__}"
        error = audit.clip(exc, 300)
        raise
    except Exception as exc:
        stop, error = f"failed: {type(exc).__name__}", audit.clip(exc, 300)
        raise
    finally:
        entry = {
            "started_at": started,
            "finished_at": audit.now_iso(),
            "duration_ms": round((time.perf_counter() - t0) * 1000),
            **(audit_meta or {}),
            "model": MODEL_NAME,
            "message": audit.clip(message),
            "tool_calls": deps.tool_log,
            "fact_check_retries": deps.fact_check_retries,
            "usage": {"requests": usage.requests, "input_tokens": usage.input_tokens,
                      "output_tokens": usage.output_tokens} if usage else None,
            "product_ids": output.product_ids if output else [],
            "reply": audit.clip(output.reply) if output else None,
            "stop_reason": stop,
        }
        if error:
            entry["error"] = error
        audit.append_entry(entry)
