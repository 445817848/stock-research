import json
import os
import time

# Load snapshot
with open("poolmaker/snapshots/qq_price_ratio_20260520_0954.json", "r", encoding="utf-8") as f:
    data = json.load(f)

stocks = data["stocks"][:160]

# Convert to digits-only codes for stock_intel filenames
from stock_code import normalize

codes = []
for s in stocks:
    digits = normalize(s["code"])
    if digits:
        codes.append(digits)

# Check 15h cooldown
cutoff = time.time() - 15 * 3600
filtered = []
for code in codes:
    path = f"stock_intel/{code}.json"
    if os.path.exists(path):
        mtime = os.stat(path).st_mtime
        if mtime > cutoff:
            continue  # skip, too fresh
    filtered.append(code)

print(f"Total from snapshot: {len(codes)}")
print(f"After 15h cooldown filter: {len(filtered)}")
for c in filtered[:20]:
    print(f"  {c}")
if len(filtered) > 20:
    print(f"  ... and {len(filtered) - 20} more")
