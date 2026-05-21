"""
Stock code normalization helpers.

Chinese A-share codes have a strict mapping between digits and market:
  600/601/603/605/688 -> sh
  000/001/002/003/300 -> sz
  4xxxxx / 8xxxxx / 9xxxxx -> bj

There is no standard prefixed format across sites. We store digits-only
in Redis for maximum compatibility. This module strips prefixes and
normalizes inputs to pure digits.
"""

import re

# Mapping of numeric patterns to market prefixes (for reference, not storage)
_MARKET_RULES = [
    (re.compile(r"^68\d{4}$"), "sh"),   # Shanghai STAR
    (re.compile(r"^60\d{4}$"), "sh"),   # Shanghai main
    (re.compile(r"^30\d{4}$"), "sz"),   # Shenzhen ChiNext
    (re.compile(r"^00\d{4}$"), "sz"),   # Shenzhen main
    (re.compile(r"^8\d{5}$"),  "bj"),   # Beijing NEEQ
    (re.compile(r"^4\d{5}$"),  "bj"),   # Beijing NEEQ
    (re.compile(r"^9\d{5}$"),  "bj"),   # Beijing NEEQ
]


def normalize(code: str) -> str:
    """
    Strip any market prefix/suffix and return digits only.

    Supports:
      - sh600519 / SH600519
      - 600519.SH / 600519.sh
      - 600519 (already digits)

    Returns pure digits, or empty string if input is empty.
    """
    if not code:
        return ""

    s = code.strip()

    # Suffix form: 600519.SH -> 600519
    if "." in s:
        parts = s.split(".")
        if len(parts) == 2 and parts[0].isdigit():
            return parts[0]

    # Prefixed form: sh600519 -> 600519
    if len(s) >= 8 and s[:2].isalpha() and s[2:].isdigit():
        return s[2:]

    # Already digits
    if s.isdigit():
        return s

    return s


def with_prefix(code: str) -> str:
    """
    Add market prefix to digits-only code for APIs that need it.

    >>> with_prefix("600519")
    'sh600519'
    >>> with_prefix("301020")
    'sz301020'
    """
    digits = normalize(code)
    if not digits:
        return code

    for pattern, prefix in _MARKET_RULES:
        if pattern.match(digits):
            return prefix + digits

    return digits


def redis_key_name(code: str) -> str:
    """Return Redis key for name lookup: stock:name:{digits}"""
    return f"stock:name:{normalize(code)}"


def redis_key_code(name: str) -> str:
    """Return Redis key for code lookup: stock:code:{name}"""
    return f"stock:code:{name}"
