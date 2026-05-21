"""
Minimal pool persistence manager for stock-research.
"""

import glob
import json
import os
from datetime import datetime, timezone

POOL_DIR = os.path.dirname(os.path.abspath(__file__))


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def save_pool(pool_name: str, pool_type: str, stocks: list, filepath: str) -> None:
    """
    Save a stock pool to JSON.

    Args:
        pool_name: Human-readable pool identifier.
        pool_type: e.g. "ranking", "block", "custom".
        stocks: List of stock dicts.
        filepath: Destination file path.
    """
    payload = {
        "pool_name": pool_name,
        "pool_type": pool_type,
        "created_at": _now_iso(),
        "source": "eastmoney",
        "count": len(stocks),
        "stocks": stocks,
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def load_pool(filepath: str) -> dict:
    """Load a pool JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def list_pools() -> list:
    """Return list of .json pool files in poolmaker/."""
    pattern = os.path.join(POOL_DIR, "*.json")
    return sorted(glob.glob(pattern))


def merge_pools(pool_paths: list, output_path: str) -> dict:
    """
    Merge stocks from multiple pools, deduplicating by 'code'.
    Keeps the first occurrence's metadata.

    Returns:
        The merged pool dict (also written to output_path).
    """
    seen = set()
    merged_stocks = []
    for path in pool_paths:
        pool = load_pool(path)
        for stock in pool.get("stocks", []):
            code = stock.get("code")
            if code and code not in seen:
                seen.add(code)
                merged_stocks.append(stock)

    result = {
        "pool_name": "merged",
        "pool_type": "merged",
        "created_at": _now_iso(),
        "source": "eastmoney",
        "count": len(merged_stocks),
        "stocks": merged_stocks,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    return result
