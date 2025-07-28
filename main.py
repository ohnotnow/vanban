#!/usr/bin/env python3
"""
Monitor Vanilla Forum comments for policy violations via OpenAI Moderation.

Changelog – 2025‑07‑28
─────────────────────
• Fixed *username* field in the final report – Vanilla’s comment payload uses
  `insertUser.name`, not `insertName`. We now resolve it safely via the nested
  object and fall back to `insertUserID`/“unknown”.
• Previous enhancements: bare‑list handling, reliable date filter, optional
  unbounded scan.
"""

from __future__ import annotations

import os
import time
import logging
from typing import List, Dict, Any
from datetime import datetime, timezone, timedelta

import requests
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration (override via environment variables)
# ---------------------------------------------------------------------------
OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
VANILLA_API_TOKEN: str | None = os.getenv("VANILLA_API_TOKEN")
VANILLA_BASE_URL: str = os.getenv("VANILLA_BASE_URL", "https://forum.example.com").rstrip("/")

MODERATION_THRESHOLD: float = float(os.getenv("MODERATION_THRESHOLD", 0.01))
LOOKBACK_HOURS: int = int(os.getenv("LOOKBACK_HOURS", 24))  # 0 = no cutoff
PAGE_SIZE: int = int(os.getenv("PAGE_SIZE", 100))

if not OPENAI_API_KEY: 
    raise SystemExit("OPENAI_API_KEY and VANILLA_API_TOKEN must be set as environment variables.")

# ---------------------------------------------------------------------------
# Pydantic model
# ---------------------------------------------------------------------------
class FlaggedPost(BaseModel):
    link: str
    username: str
    reason: str

# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def vanilla_get(endpoint: str, params: Dict[str, Any] | None = None) -> Any:
    headers = {
        "Authorization": f"Bearer {VANILLA_API_TOKEN}",
        "Accept": "application/json",
    }
    url = f"{VANILLA_BASE_URL}{endpoint}"
    r = requests.get(url, headers=headers, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

# ---------------------------------------------------------------------------
# Comment fetcher
# ---------------------------------------------------------------------------

def fetch_recent_comments() -> List[Dict[str, Any]]:
    params: Dict[str, Any] = {"limit": PAGE_SIZE, "page": 1}
    if LOOKBACK_HOURS > 0:
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)).isoformat()
        params["dateInserted"] = f">{cutoff}"

    comments: List[Dict[str, Any]] = []
    while True:
        data = vanilla_get("/api/v2/comments", params=params)
        items = data if isinstance(data, list) else data.get("items", [])
        if not items:
            break
        comments.extend(items)
        if isinstance(data, list):
            break  # no pagination
        params["page"] = params.get("page", 1) + 1
    return comments

# ---------------------------------------------------------------------------
# OpenAI moderation helpers
# ---------------------------------------------------------------------------

def openai_moderate(text: str) -> Dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    r = requests.post("https://api.openai.com/v1/moderations", json={"input": text}, headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()["results"][0]


def triggered(res: Dict[str, Any]) -> bool:
    return res.get("flagged") or any(v >= MODERATION_THRESHOLD for v in res["category_scores"].values())

# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

def _username(c: Dict[str, Any]) -> str:
    """Extract display name from comment payload with fallbacks."""
    if (u := c.get("insertUser", {})).get("name"):
        return u["name"]
    return f"user_{c.get('insertUserID', '?')}"


def analyse_comments(comments: List[Dict[str, Any]]) -> List[FlaggedPost]:
    flagged: List[FlaggedPost] = []
    for c in comments[0:3]:
        res = openai_moderate(c.get("body", "")[:7000])
#        if not triggered(res):
#            continue
        reason = ", ".join(
            f"{k.replace('_', ' ')} ({v:.2f})" for k, v in res["category_scores"].items() if v >= MODERATION_THRESHOLD
        ) or "OpenAI flagged"
        flagged.append(
            FlaggedPost(
                link=f"{VANILLA_BASE_URL}/discussion/comment/{c['commentID']}",
                username=_username(c),
                reason=reason,
            )
        )
        time.sleep(0.4)  # stay well under rate limits
    return flagged

# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------

def list_to_markdown(rows: List[FlaggedPost]) -> str:
    if not rows:
        return "_No policy concerns detected in the selected window._"
    header = "| User | Comment | Reason |\n|------|---------|--------|"
    return header + "\n" + "\n".join(f"| {r.username} | [link]({r.link}) | {r.reason} |" for r in rows)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    comments = fetch_recent_comments()
    logging.info("Fetched %d comment(s) for review", len(comments))
    flagged = analyse_comments(comments)
    logging.info("Flagged %d comment(s)", len(flagged))
    print(list_to_markdown(flagged))


if __name__ == "__main__":
    main()

