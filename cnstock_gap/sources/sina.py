"""Sina Finance K-line API source.

Batch status: Single-stock endpoint. Multi-bar per request.
Request cost: 1 request returns up to `datalen` bars.
"""

import json
import urllib.request

from ..core.ratelimit import rate_limit, track_request
from ..utils.codeutil import with_prefix

ENDPOINT = (
    "https://money.finance.sina.com.cn/quotes_service/api/json_v2.php"
    "/CN_MarketData.getKLineData"
)


def fetch_kline(code: str, scale: int = 240, datalen: int = 40) -> list[dict]:
    """
    Fetch K-line bars from Sina Finance.

    Args:
        code: Stock code, e.g. '301666' or 'sz301666'.
        scale: Bar interval in minutes. Supported: 5, 30, 60, 240.
               240 = daily bars.
        datalen: Number of bars to fetch. Max safe ~1000.

    Returns:
        List of bar dicts with keys:
        day, open, high, low, close, volume, ma_price5, ma_volume5.
        For intraday scales, `day` includes time (e.g. '2026-05-29 15:00:00').
    """
    symbol = with_prefix(code)
    url = f"{ENDPOINT}?symbol={symbol}&scale={scale}&ma=5&datalen={datalen}"

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36"
            ),
            "Referer": "https://finance.sina.com.cn",
        },
    )

    rate_limit(min_interval=1.0)
    with urllib.request.urlopen(req, timeout=15) as resp:
        text = resp.read().decode("utf-8", errors="ignore")

    track_request()

    data = json.loads(text)
    if not isinstance(data, list):
        return []
    return data
