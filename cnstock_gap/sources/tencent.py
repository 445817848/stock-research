"""Tencent QQ Stock API source.

Batch status: Multi-stock endpoint (qt.gtimg.cn). Up to 60 codes per URL.
Request cost: 1 request per 60 codes.
"""

import urllib.request

from ..core.ratelimit import rate_limit, track_request
from ..core.flow import chunk
from ..utils.codeutil import with_prefix

ENDPOINT = "https://qt.gtimg.cn/q="


def fetch_snapshot(codes: list[str]) -> list[dict]:
    """
    Fetch real-time snapshots for multiple stocks in one request.

    Args:
        codes: List of stock codes, e.g. ['301666', '600519'].

    Returns:
        List of dicts with keys:
        code, name, price, prev_close, open, change_amt, change_pct,
        high, low, volume, turnover.
    """
    symbols = [with_prefix(c) for c in codes]
    results = []

    for batch in chunk(symbols, batch_size=60):
        query = ",".join(batch)
        url = f"{ENDPOINT}{query}"

        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        rate_limit(min_interval=1.0)
        with urllib.request.urlopen(req, timeout=15) as resp:
            text = resp.read().decode("gbk", errors="ignore")

        track_request()

        for line in text.strip().split(";"):
            line = line.strip()
            if not line or '"' not in line:
                continue
            parts = line.split('"')[1].split("~")
            if len(parts) < 35:
                continue

            results.append(
                {
                    "code": parts[2],
                    "name": parts[1],
                    "price": _f(parts[3]),
                    "prev_close": _f(parts[4]),
                    "open": _f(parts[5]),
                    "change_amt": _f(parts[31]) if len(parts) > 31 else None,
                    "change_pct": _f(parts[32]) if len(parts) > 32 else None,
                    "high": _f(parts[33]) if len(parts) > 33 else None,
                    "low": _f(parts[34]) if len(parts) > 34 else None,
                    "volume": _f(parts[36]) if len(parts) > 36 else None,
                    "turnover": _f(parts[37]) if len(parts) > 37 else None,
                }
            )

    return results


def _f(s: str):
    """Safe float parse."""
    try:
        return float(s)
    except (ValueError, TypeError):
        return None
