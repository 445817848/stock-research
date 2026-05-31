"""Stock code normalization (self-contained, duplicated from stock_code.py)."""

import re

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
    """Strip any market prefix/suffix and return digits only."""
    if not code:
        return ""
    s = code.strip()
    if "." in s:
        parts = s.split(".")
        if len(parts) == 2 and parts[0].isdigit():
            return parts[0]
    if len(s) >= 8 and s[:2].isalpha() and s[2:].isdigit():
        return s[2:]
    if s.isdigit():
        return s
    return s


def with_prefix(code: str) -> str:
    """Add market prefix to digits-only code for APIs that need it."""
    digits = normalize(code)
    if not digits:
        return code
    for pattern, prefix in _MARKET_RULES:
        if pattern.match(digits):
            return prefix + digits
    return digits
