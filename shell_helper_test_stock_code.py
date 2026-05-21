from stock_code import normalize, with_prefix

tests = [
    ("sh600519", "600519", "sh600519"),
    ("SH600519", "600519", "sh600519"),
    ("600519.SH", "600519", "sh600519"),
    ("600519", "600519", "sh600519"),
    ("sz301020", "301020", "sz301020"),
    ("301020", "301020", "sz301020"),
    ("bj920178", "920178", "bj920178"),
    ("920178", "920178", "bj920178"),
    ("688449", "688449", "sh688449"),
]

for raw, expected_digits, expected_prefixed in tests:
    digits = normalize(raw)
    prefixed = with_prefix(raw)
    ok = "OK" if (digits == expected_digits and prefixed == expected_prefixed) else "FAIL"
    print(f"{ok}: {raw:15} -> digits={digits:8} prefixed={prefixed:12}")
