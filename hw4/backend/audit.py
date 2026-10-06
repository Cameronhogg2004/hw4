"""Append-only audit trail of agent runs: output/audit_trail.json.

Each chat turn appends one entry (time, tool calls with short args/results,
fact-check retries, token usage, stop reason). Existing entries are never
rewritten or dropped; an unreadable file is moved aside, not overwritten.
"""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUDIT_PATH = ROOT / "output" / "audit_trail.json"
_lock = threading.Lock()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def clip(value: object, limit: int = 200) -> str:
    text = " ".join(str(value).split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def append_entry(entry: dict) -> None:
    with _lock:
        AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        entries: list = []
        if AUDIT_PATH.is_file() and AUDIT_PATH.stat().st_size:
            try:
                loaded = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
                entries = loaded if isinstance(loaded, list) else [loaded]
            except json.JSONDecodeError:
                aside = AUDIT_PATH.with_name(f"audit_trail.corrupt-{datetime.now():%Y%m%d%H%M%S}.json")
                AUDIT_PATH.replace(aside)
                entries = [{"note": f"previous audit file was unreadable; kept as {aside.name}"}]
        entries.append(entry)
        tmp = AUDIT_PATH.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        os.replace(tmp, AUDIT_PATH)  # atomic: a crash mid-write can't truncate the trail
