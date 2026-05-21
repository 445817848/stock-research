#!/usr/bin/env python3
"""
CLI: compare two active pool JSON files by code.

Usage:
    python3 compare_pools.py <old_pool.json> <new_pool.json>
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from pool_manager import load_pool


def _code_map(stocks):
    return {s["code"]: s for s in stocks if s.get("code")}


def _fmt_delta(old_val, new_val):
    try:
        old_f = float(old_val)
        new_f = float(new_val)
        delta = new_f - old_f
        return f"{old_f} → {new_f} (Δ {delta:+.2f})"
    except (TypeError, ValueError):
        return f"{old_val} → {new_val}"


def compare(old_path, new_path):
    old_pool = load_pool(old_path)
    new_pool = load_pool(new_path)
    old_stocks = old_pool.get("stocks", [])
    new_stocks = new_pool.get("stocks", [])
    old_map = _code_map(old_stocks)
    new_map = _code_map(new_stocks)

    entered = []
    left = []
    changed = []

    for code, stock in new_map.items():
        if code not in old_map:
            entered.append(stock)
        else:
            old_stock = old_map[code]
            deltas = []
            for field in ("change_pct", "price"):
                old_val = old_stock.get(field)
                new_val = stock.get(field)
                if old_val != new_val:
                    deltas.append(f"{field}: {_fmt_delta(old_val, new_val)}")
            if deltas:
                changed.append((stock, deltas))

    for code, stock in old_map.items():
        if code not in new_map:
            left.append(stock)

    lines = []
    lines.append("=" * 60)
    lines.append(f"Pool comparison: {os.path.basename(old_path)} → {os.path.basename(new_path)}")
    lines.append(f"Old count: {len(old_stocks)} | New count: {len(new_stocks)}")
    lines.append("")

    lines.append(f"--- Entered ({len(entered)}) ---")
    for s in entered:
        lines.append(f"  {s.get('code')} {s.get('name')}  price={s.get('price')}  change_pct={s.get('change_pct')}")
    if not entered:
        lines.append("  (none)")
    lines.append("")

    lines.append(f"--- Left ({len(left)}) ---")
    for s in left:
        lines.append(f"  {s.get('code')} {s.get('name')}  price={s.get('price')}  change_pct={s.get('change_pct')}")
    if not left:
        lines.append("  (none)")
    lines.append("")

    lines.append(f"--- Changed ({len(changed)}) ---")
    for s, deltas in changed:
        lines.append(f"  {s.get('code')} {s.get('name')}  {', '.join(deltas)}")
    if not changed:
        lines.append("  (none)")
    lines.append("")

    lines.append("=" * 60)
    summary = "\n".join(lines)
    print(summary)

    old_base = os.path.splitext(os.path.basename(old_path))[0]
    new_base = os.path.splitext(os.path.basename(new_path))[0]
    diff_filename = f"diff_{old_base}_{new_base}.txt"
    diff_path = os.path.join(os.path.dirname(os.path.abspath(new_path)), diff_filename)
    with open(diff_path, "w", encoding="utf-8") as f:
        f.write(summary)
    print(f"Diff saved to {diff_path}")


def main():
    if len(sys.argv) != 3:
        print("Usage: python3 compare_pools.py <old_pool.json> <new_pool.json>", file=sys.stderr)
        sys.exit(1)
    compare(sys.argv[1], sys.argv[2])


if __name__ == "__main__":
    main()
