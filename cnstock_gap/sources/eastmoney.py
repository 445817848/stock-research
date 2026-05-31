"""East Money A-share ranking API source.

Batch status: Multi-stock endpoint (paged). Each page returns up to 200 stocks.
Request cost: 1 request per page.
"""

import json
import urllib.request
import urllib.parse

from ..core.ratelimit import rate_limit, track_request

ENDPOINT = "https://push2.eastmoney.com/api/qt/clist/get"
FS_ALL = "m:0+t:6,m:0+t:13,m:1+t:2,m:1+t:23,m:0+t:81"
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


def _strip_jsonp(text: str) -> str:
    """Remove jQuery(...) wrapper if present."""
    text = text.strip()
    start = text.find("(")
    end = text.rfind(")")
    if start != -1 and end != -1 and end > start:
        return text[start + 1 : end]
    return text


def _parse_item(raw: dict) -> dict:
    """Convert East Money f-fields to human-readable keys."""
    return {FIELD_MAP.get(k, k): v for k, v in raw.items()}


def _parse_response(text: str) -> list:
    """Parse raw response text into a list of raw stock dicts."""
    payload = json.loads(_strip_jsonp(text))
    data = payload.get("data") or {}
    return data.get("diff", []) or []


def _fetch_page(fid: str, po: int, page: int, page_size: int = 100) -> list:
    """Fetch a single page. Cost: 1 request."""
    fields = ",".join(FIELD_MAP.keys())
    params = {
        "pn": page,
        "pz": page_size,
        "po": po,
        "np": 1,
        "fltt": 2,
        "invt": 2,
        "fid": fid,
        "fs": FS_ALL,
        "fields": fields,
    }
    url = f"{ENDPOINT}?{urllib.parse.urlencode(params)}"

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36"
            ),
        },
    )

    rate_limit(min_interval=1.0)
    with urllib.request.urlopen(req, timeout=15) as resp:
        text = resp.read().decode("utf-8", errors="ignore")

    track_request()
    return _parse_response(text)


def fetch_ranking(
    rank_type: str = "gainers", pages: int = 2, min_change: float = None
) -> list:
    """
    Fetch top A-share rankings from East Money.

    Args:
        rank_type: "gainers" | "losers" | "active"
        pages: Number of pages to fetch (default 2).
        min_change: If set, filter out stocks with change_pct < min_change.

    Returns:
        List of dicts with human-readable keys.
    """
    config = {
        "gainers": ("f3", 1),
        "losers": ("f3", -1),
        "active": ("f6", 1),
    }
    if rank_type not in config:
        raise ValueError(f"Unknown rank_type '{rank_type}'. Choose from {list(config.keys())}")

    fid, po = config[rank_type]
    all_stocks = []

    for page in range(1, pages + 1):
        try:
            raw_items = _fetch_page(fid, po, page)
        except Exception as e:
            print(f"[warning] Page {page} fetch failed: {e}. Returning partial results.")
            break

        for item in raw_items:
            if item:
                parsed = _parse_item(item)
                if min_change is not None:
                    try:
                        pct = float(parsed.get("change_pct") or 0)
                    except (TypeError, ValueError):
                        pct = 0
                    if pct < min_change:
                        continue
                all_stocks.append(parsed)

        if len(raw_items) == 0:
            break

    return all_stocks
