"""
East Money A-share ranking fetcher (SH + SZ + BJ).
Direct connection (no proxy). Handles JSONP and plain JSON.
"""

import json
import time
from datetime import datetime, timezone

import requests

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
ENDPOINT = "https://push2.eastmoney.com/api/qt/clist/get"
PAGES = 2
PAGE_SIZE = 100
MIN_INTERVAL = 1.0

# All A-shares: SH + SZ + BJ (北交所)
FS_ALL = "m:0+t:6,m:0+t:13,m:1+t:2,m:1+t:23,m:0+t:81"

MINIMAL_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6,zh-TW;q=0.5",
    "Cache-Control": "max-age=0",
    "Connection": "keep-alive",
    "Cookie": "qgqp_b_id=6f24ce867e6d37151ac67da4bad633e8; st_nvi=iwkiyZDkRrwzFNAAc4jf14d94; nid18=06946ed3ea7097d4f2b02ddb6fe992d1; nid18_create_time=1776065145069; gviem=0_WDG3VrS1fMOOElxFxpO3e26; gviem_create_time=1776065145070; emshistory=%5B%22%E5%85%89%E9%80%9A%E4%BF%A1%E6%A8%A1%E5%9D%97%22%2C%22cpo%22%2C%22%E5%85%AC%E5%91%8A%20%E5%BC%82%E5%B8%B8%E6%B3%A2%E5%8A%A8%22%5D; st_si=85288610064190; fullscreengg=1; fullscreengg2=1; st_asi=delete; st_pvi=41712159489713; st_sp=2023-11-22%2007%3A18%3A41; st_inirUrl=http%3A%2F%2Fquote.eastmoney.com%2Fforex%2FUSDCNYI.html; st_sn=80; st_psi=20260519162058128-111000300841-2213674589",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0",
    "sec-ch-ua": '"Chromium";v="148", "Microsoft Edge";v="148", "Not/A)Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}

FIELD_MAP = {
    "f12": "code",
    "f14": "name",
    "f2": "price",
    "f3": "change_pct",
    "f4": "change_amt",
    "f5": "volume",
    "f6": "turnover",
    "f17": "open",
    "f18": "prev_close",
    "f20": "market_cap",
}

# Sort config: (fid, po) where po=1 desc, po=-1 asc
RANK_CONFIG = {
    "gainers": ("f3", 1),
    "losers": ("f3", -1),
    "active": ("f6", 1),
}

_last_request_time = 0.0


def _rate_limit():
    """Enforce minimum interval between requests."""
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < MIN_INTERVAL:
        time.sleep(MIN_INTERVAL - elapsed)
    _last_request_time = time.time()


def _strip_jsonp(text: str) -> str:
    """Remove jQuery(...) wrapper if present."""
    text = text.strip()
    start = text.find("(")
    end = text.rfind(")")
    if start != -1 and end != -1 and end > start:
        return text[start + 1:end]
    return text


def _parse_item(raw: dict) -> dict:
    """Convert East Money f-fields to human-readable keys."""
    return {FIELD_MAP.get(k, k): v for k, v in raw.items()}


def _parse_response(text: str) -> list:
    """Parse raw response text into a list of raw stock dicts."""
    payload = json.loads(_strip_jsonp(text))
    data = payload.get("data") or {}
    return data.get("diff", []) or []


def _fetch_page(fid: str, po: int, page: int) -> list:
    """
    Fetch a single page using requests.get with minimal headers.
    Raises immediately on failure — no retry, no fallback.
    """
    fields = ",".join(FIELD_MAP.keys())
    params = (
        f"?pn={page}&pz={PAGE_SIZE}&po={po}&np=1&fltt=2&invt=2"
        f"&fid={fid}&fs={FS_ALL}&fields={fields}"
    )
    url = ENDPOINT + params

    _rate_limit()
    resp = requests.get(url, headers=MINIMAL_HEADERS, timeout=15)
    resp.raise_for_status()
    return _parse_response(resp.text)


def _get_numeric_change_pct(stock: dict) -> float:
    """Safely extract numeric change_pct from a parsed stock dict."""
    val = stock.get("change_pct")
    if isinstance(val, (int, float)):
        return float(val)
    try:
        return float(val) if val is not None else 999.0
    except (TypeError, ValueError):
        return 0.0


def fetch_ranking(rank_type: str = "gainers", min_count: int = 0, stop_pct: float = None) -> list:
    """
    Fetch top A-share rankings from East Money.

    Args:
        rank_type: "gainers" | "losers" | "active"
        min_count: Minimum number of stocks to fetch before considering stop_pct.
        stop_pct: If set, keep fetching until the last stock's change_pct <= stop_pct
                  AND at least min_count stocks have been fetched.

    Returns:
        List of dicts with human-readable keys.
    """
    if rank_type not in RANK_CONFIG:
        raise ValueError(f"Unknown rank_type '{rank_type}'. Choose from {list(RANK_CONFIG.keys())}")

    fid, po = RANK_CONFIG[rank_type]
    all_stocks = []
    page = 1

    while True:
        try:
            raw_items = _fetch_page(fid, po, page)
        except Exception as e:
            print(f"[warning] Page {page} fetch failed: {e}. Returning partial results.")
            break

        for item in raw_items:
            if item:
                all_stocks.append(_parse_item(item))

        no_more_data = len(raw_items) == 0
        count_met = len(all_stocks) >= min_count
        pct_met = stop_pct is None or (all_stocks and _get_numeric_change_pct(all_stocks[-1]) <= stop_pct)

        # Legacy behaviour: exactly PAGES pages when min_count and stop_pct are defaults
        if min_count == 0 and stop_pct is None:
            if page >= PAGES:
                break
        else:
            # New behaviour: stop when both conditions met, or no more data
            if no_more_data:
                break
            if count_met and pct_met:
                break

        time.sleep(1)
        page += 1

    return all_stocks


def fetch_gainers() -> list:
    """Convenience wrapper for top gainers."""
    return fetch_ranking("gainers")


def fetch_gainers_until_8pct(min_count: int = 150) -> list:
    """Fetch top gainers until change_pct <= 8% or min_count reached, whichever is longer."""
    return fetch_ranking("gainers", min_count=min_count, stop_pct=8.0)


def fetch_losers() -> list:
    """Convenience wrapper for top losers."""
    return fetch_ranking("losers")


def fetch_active() -> list:
    """Convenience wrapper for most active by turnover."""
    return fetch_ranking("active")
