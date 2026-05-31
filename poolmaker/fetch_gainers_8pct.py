#!/usr/bin/env python3
"""
CLI: fetch top gainers until change_pct <= 8%% or 150 stocks reached,
whichever is longer. Save to poolmaker/snapshots/gainers_8pct_YYYYMMDD_HHMM.json
"""

import os
import sys
from datetime import datetime, timezone

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from rank_fetcher import fetch_gainers_until_8pct, _get_numeric_change_pct
from pool_manager import save_pool


def verify(stocks: list) -> dict:
    """Verify the fetched pool meets basic quality checks."""
    result = {
        "ok": True,
        "count": len(stocks),
        "top_pct": None,
        "bottom_pct": None,
        "count_ok": len(stocks) >= 150,
        "pct_ok": False,
        "sorted_ok": True,
        "duplicates": 0,
        "errors": [],
    }

    if not stocks:
        result["ok"] = False
        result["errors"].append("Empty stock list")
        return result

    pcts = [_get_numeric_change_pct(s) for s in stocks]
    result["top_pct"] = pcts[0]
    result["bottom_pct"] = pcts[-1]
    result["pct_ok"] = pcts[-1] <= 8.0

    # Check descending sort
    for i in range(1, len(pcts)):
        if pcts[i] > pcts[i - 1]:
            result["sorted_ok"] = False
            break

    # Check duplicates
    codes = [s["code"] for s in stocks]
    result["duplicates"] = len(codes) - len(set(codes))
    if result["duplicates"] > 0:
        result["errors"].append(f"Found {result['duplicates']} duplicate code(s)")

    if not result["sorted_ok"]:
        result["errors"].append("Stocks are not sorted by change_pct descending")

    result["ok"] = result["count_ok"] or result["pct_ok"]
    if not result["ok"]:
        result["errors"].append("Count < 150 AND last change_pct > 8.0")

    return result


def main():
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y%m%d_%H%M")
    filename = f"gainers_8pct_{timestamp}.json"
    snapshots_dir = os.path.join(_HERE, "snapshots")
    os.makedirs(snapshots_dir, exist_ok=True)
    filepath = os.path.join(snapshots_dir, filename)

    try:
        stocks = fetch_gainers_until_8pct(min_count=150)
    except Exception as e:
        print(f"[error] Failed to fetch gainers: {e}", file=sys.stderr)
        sys.exit(1)

    pool_name = f"gainers_8pct_{timestamp}"
    save_pool(pool_name, "ranking", stocks, filepath)
    print(f"Saved {len(stocks)} stocks to poolmaker/snapshots/{filename}")

    # Verification
    v = verify(stocks)
    print(
        f"Summary: count={v['count']}, top_change_pct={v['top_pct']:.2f}%, "
        f"bottom_change_pct={v['bottom_pct']:.2f}%"
    )
    if v["errors"]:
        for err in v["errors"]:
            print(f"[verify-warning] {err}", file=sys.stderr)
    if not v["ok"]:
        sys.exit(2)


if __name__ == "__main__":
    main()
