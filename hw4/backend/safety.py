"""Input safety for the chat route: sensitive-data redaction, injection flags, rate limiting.

Runs in main.py before a message reaches the model or the database, so card
numbers or passwords a shopper pastes are never sent to the LLM or stored.
"""

from __future__ import annotations

import re
import time
from collections import defaultdict, deque

CARD_RE = re.compile(r"\b\d(?:[ -]?\d){12,18}\b")
SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
PASSWORD_RE = re.compile(r"\b(pass(?:word|code)?|pwd)\b(\s*(?:is|:|=)\s*)[^\s,.;]+", re.IGNORECASE)
INJECTION_RE = re.compile(
    r"ignore (all |any )?(previous|prior|above) (instructions|rules)|system prompt|you are now|"
    r"developer mode|jailbreak|reveal your (prompt|instructions)",
    re.IGNORECASE,
)


def _luhn_ok(digits: str) -> bool:
    total, parity = 0, len(digits) % 2
    for i, ch in enumerate(digits):
        d = int(ch)
        if i % 2 == parity:
            d = d * 2 - 9 if d > 4 else d * 2
        total += d
    return total % 10 == 0


def redact_sensitive(text: str) -> tuple[str, list[str]]:
    """Replace card numbers, SSNs and stated passwords. Returns (clean_text, flags)."""
    flags: list[str] = []

    def card(m: re.Match) -> str:
        digits = re.sub(r"\D", "", m.group())
        if 13 <= len(digits) <= 19 and _luhn_ok(digits):
            flags.append("card_number")
            return "[redacted card number]"
        return m.group()

    text = CARD_RE.sub(card, text)
    if SSN_RE.search(text):
        flags.append("ssn")
        text = SSN_RE.sub("[redacted SSN]", text)
    if PASSWORD_RE.search(text):
        flags.append("password")
        text = PASSWORD_RE.sub(lambda m: f"{m.group(1)}{m.group(2)}[redacted]", text)
    return text, flags


def looks_like_injection(text: str) -> bool:
    return bool(INJECTION_RE.search(text))


class RateLimiter:
    """Sliding-window limit per shopper (user id or client IP), kept in memory."""

    def __init__(self, max_events: int, window_seconds: float) -> None:
        self.max_events = max_events
        self.window = window_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        events = self._events[key]
        while events and now - events[0] > self.window:
            events.popleft()
        if len(events) >= self.max_events:
            return False
        events.append(now)
        return True
