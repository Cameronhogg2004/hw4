"""Password hashing and login sessions.

Passwords: PBKDF2-HMAC-SHA256 with a random 16-byte salt per user.
  New hashes:   pbkdf2_sha256$<iterations>$<salt>$<hex digest>
  Seed hashes:  pbkdf2_sha256$<salt>$<hex digest>  (120,000 iterations)
Both formats verify. Plain passwords are never stored or logged.

Sessions: a random token goes to the browser; only its SHA-256 hash is stored
in the sessions table, so a leaked database can't be replayed as logins.
"""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone

from db import connect
from models import UserPublic

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 600_000
SEED_ITERATIONS = 120_000
SESSION_DAYS = 7
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalize_email(email: str) -> str:
    return email.strip().lower()


def valid_email(email: str) -> bool:
    return bool(EMAIL_RE.match(email))


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), ITERATIONS).hex()
    return f"{ALGORITHM}${ITERATIONS}${salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    parts = stored.split("$")
    if len(parts) == 4 and parts[0] == ALGORITHM:
        _, iterations, salt, expected = parts
        rounds = int(iterations)
    elif len(parts) == 3 and parts[0] == ALGORITHM:
        _, salt, expected = parts
        rounds = SEED_ITERATIONS
    else:
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), rounds).hex()
    return hmac.compare_digest(digest, expected)


def to_public(row: sqlite3.Row) -> UserPublic:
    first = row["first_name"] or row["name"].split(" ")[0]
    last = row["last_name"] or " ".join(row["name"].split(" ")[1:])
    return UserPublic(id=row["id"], name=row["name"], first_name=first, last_name=last, email=row["email"])


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)
    with connect() as conn:
        conn.execute(
            "INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (?, ?, ?)",
            (_token_hash(token), user_id, expires.strftime("%Y-%m-%d %H:%M:%S")),
        )
    return token


def user_for_token(token: str) -> UserPublic | None:
    with connect() as conn:
        row = conn.execute(
            """
            SELECT u.* FROM sessions s JOIN users u ON u.id = s.user_id
            WHERE s.token_hash = ? AND s.expires_at > datetime('now')
            """,
            (_token_hash(token),),
        ).fetchone()
    return to_public(row) if row else None


def delete_session(token: str) -> None:
    with connect() as conn:
        conn.execute("DELETE FROM sessions WHERE token_hash = ?", (_token_hash(token),))
