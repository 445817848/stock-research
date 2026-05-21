#!/usr/bin/env python3
"""
CLI: fetch top ~300 A-shares ranked by today's change_pct (zdf)
from Tencent QQ Stock API (sort_type=priceRatio) and save to
poolmaker/snapshots/qq_price_ratio_YYYYMMDD_HHMM.json

Improved: caches code<->name mappings to Redis (naemini.local:6379, db=1).
Only caches what was actually fetched. No bulk pull.
"""

import json
import os
import random
import sys
import time
from datetime import datetime, timezone

import requests

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

_parent = os.path.dirname(_HERE)
if _parent not in sys.path:
    sys.path.insert(0, _parent)

from pool_manager import save_pool
from stock_code import normalize, redis_key_name, redis_key_code

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
ENDPOINT = "https://proxy.finance.qq.com/cgi/cgi-bin/rank/hs/getBoardRankList"
PAGE_SIZE = 180
MAX_STOCKS = 300
MIN_STOCKS = 150
MIN_CHANGE_PCT = 8.7
MIN_INTERVAL = 1.0

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://stockapp.finance.qq.com/",
    "Accept": "application/json, text/plain, */*",
}

_last_request_time = 0.0


# ---------------------------------------------------------------------------
# Redis cache helpers
# ---------------------------------------------------------------------------
def _get_redis():
    """Return Redis client or None if unavailable."""
    try:
        import redis as _redis
        return _redis.Redis(
            host="naemini.local",
            port=6379,
            db=1,
            decode_responses=True,
            socket_connect_timeout=3,
        )
    except Exception:
        return None


def _cache_stocks(stocks: list):
    """Cache code<->name mappings for the fetched stocks (digits-only keys)."""
    r = _get_redis()
    if r is None:
        print("[redis] skipped (not available)")
        return

    pipe = r.pipeline()
    cached = 0
    for s in stocks:
        code = s.get("code", "")
        name = s.get("name", "")
        digits = normalize(code)
        if digits and name:
            pipe.set(redis_key_name(digits), name)
            pipe.set(redis_key_code(name), digits)
            cached += 1

    pipe.execute()
    print(f"[redis] cached {cached} code<->name mappings")


def backfill_latest_snapshot():
    """Read the latest snapshot and cache its code<->name mappings to Redis."""
    path = _find_latest_snapshot()
    if path is None:
        print("[redis] no snapshot found for backfill")
        return

    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    stocks = payload.get("stocks", [])
    _cache_stocks(stocks)
    print(f"[redis] backfilled from {os.path.basename(path)}")


# ---------------------------------------------------------------------------
# Fetch logic (unchanged)
# ---------------------------------------------------------------------------
def _rate_limit():
    """Enforce minimum interval + random 1-2 s cooldown between requests."""
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < MIN_INTERVAL:
        time.sleep(MIN_INTERVAL - elapsed)
    time.sleep(random.uniform(1, 2))
    _last_request_time = time.time()


def _fetch_page(offset: int, direct: str = "down") -> list:
    """
    Fetch a single page from Tencent API.
    Raises immediately on failure — no retry.
    """
    params = {
        "_appver": "11.17.0",
        "board_code": "aStock",
        "sort_type": "priceRatio",
        "direct": direct,
        "offset": str(offset),
        "count": str(PAGE_SIZE),
    }

    _rate_limit()
    resp = requests.get(ENDPOINT, params=params, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    payload = resp.json()

    if payload.get("code") != 0:
        raise RuntimeError(
            f"API error {payload.get('code')}: {payload.get('msg')}"
        )

    return payload.get("data", {}).get("rank_list", [])


def _parse_item(raw: dict) -> dict:
    """Convert raw Tencent API item to standard pool dict."""
    price = float(raw.get("zxj", 0))
    zd = float(raw.get("zd", 0))
    return {
        "code": raw.get("code", ""),
        "name": raw.get("name", ""),
        "price": price,
        "change_pct": float(raw.get("zdf", 0)),
        "change_amt": zd,
        "prev_close": round(price - zd, 2),
        "volume": raw.get("volume"),
        "turnover": raw.get("turnover"),
        "turnover_rate": raw.get("hsl"),
        "market_cap": raw.get("zsz"),
        "float_cap": raw.get("ltsz"),
    }


def fetch_qq_ranking(
    direct: str = "down",
    max_stocks: int = MAX_STOCKS,
    min_stocks: int = MIN_STOCKS,
    min_change_pct: float = MIN_CHANGE_PCT,
) -> list:
    """
    Fetch A-share ranking by today's change_pct from Tencent API.

    Stops when:
      - at least min_stocks are fetched AND last stock's change_pct < min_change_pct, OR
      - max_stocks hard cap is reached.

    Args:
        direct: "down" for top gainers, "up" for top losers.
        max_stocks: Hard cap on number of stocks to fetch.
        min_stocks: Minimum stocks to fetch before considering early stop.
        min_change_pct: Change pct threshold for early stop.

    Returns:
        List of parsed stock dicts.
    """
    all_stocks = []
    offset = 0

    while len(all_stocks) < max_stocks:
        try:
            raw_items = _fetch_page(offset, direct=direct)
        except Exception as e:
            print(f"[warning] Page offset={offset} fetch failed: {e}")
            break

        if not raw_items:
            break

        for item in raw_items:
            if item:
                all_stocks.append(_parse_item(item))
                if len(all_stocks) >= max_stocks:
                    break

        # Early stop: have enough stocks and last one is below threshold
        if len(all_stocks) >= min_stocks:
            last_change = all_stocks[-1].get("change_pct", 0)
            if last_change < min_change_pct:
                break

        if len(raw_items) < PAGE_SIZE:
            break

        offset += PAGE_SIZE

    return all_stocks


def _find_latest_snapshot() -> str | None:
    """Return the newest qq_price_ratio_*.json filepath, or None."""
    snapshots_dir = os.path.join(_HERE, "snapshots")
    if not os.path.isdir(snapshots_dir):
        return None
    files = [
        f
        for f in os.listdir(snapshots_dir)
        if f.startswith("qq_price_ratio_") and f.endswith(".json")
    ]
    if not files:
        return None
    files.sort(reverse=True)
    return os.path.join(snapshots_dir, files[0])


def load_last_rank() -> dict | None:
    """Load the most recent qq_price_ratio snapshot without fetching."""
    path = _find_latest_snapshot()
    if path is None:
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    snapshots_dir = os.path.join(_HERE, "snapshots")
    os.makedirs(snapshots_dir, exist_ok=True)

    # If today's snapshot already exists, just report it
    latest = _find_latest_snapshot()
    if latest:
        today_prefix = datetime.now(timezone.utc).strftime("%Y%m%d")
        if os.path.basename(latest).startswith(f"qq_price_ratio_{today_prefix}"):
            with open(latest, "r", encoding="utf-8") as f:
                pool = json.load(f)
            print(f"[skip] Today's snapshot already exists: {os.path.basename(latest)}")
            print(f"Loaded {pool['count']} stocks from cache.")
            _cache_stocks(pool.get("stocks", []))
            if pool.get("stocks"):
                print(
                    f"Summary: top_change_pct={pool['stocks'][0]['change_pct']:.2f}%, "
                    f"bottom_change_pct={pool['stocks'][-1]['change_pct']:.2f}%"
                )
            return

    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y%m%d_%H%M")
    filename = f"qq_price_ratio_{timestamp}.json"
    filepath = os.path.join(snapshots_dir, filename)

    try:
        stocks = fetch_qq_ranking(direct="down", max_stocks=MAX_STOCKS)
    except Exception as e:
        print(f"[error] Failed to fetch QQ ranking: {e}", file=sys.stderr)
        sys.exit(1)

    pool_name = f"qq_price_ratio_{timestamp}"
    save_pool(pool_name, "ranking", stocks, filepath)
    _patch_source(filepath, "tencent")

    # Cache fetched code<->name mappings to Redis
    _cache_stocks(stocks)

    print(f"Saved {len(stocks)} stocks to poolmaker/snapshots/{filename}")
    if stocks:
        print(
            f"Summary: top_change_pct={stocks[0]['change_pct']:.2f}%, "
            f"bottom_change_pct={stocks[-1]['change_pct']:.2f}%"
        )


def _patch_source(filepath: str, source: str):
    """Overwrite the default source written by save_pool."""
    with open(filepath, "r", encoding="utf-8") as f:
        payload = json.load(f)
    payload["source"] = source
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
