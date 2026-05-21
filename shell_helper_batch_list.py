import json
import os
import time
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stock_code import normalize

with open("poolmaker/snapshots/qq_price_ratio_20260520_0954.json", "r", encoding="utf-8") as f:
    data = json.load(f)

stocks = data["stocks"][:160]

cutoff = time.time() - 15 * 3600
batch = []
for s in stocks:
    code = normalize(s["code"])
    name = s["name"]
    if not code or not name:
        continue
    path = f"stock_intel/{code}.json"
    if os.path.exists(path):
        if os.stat(path).st_mtime > cutoff:
            continue
    batch.append({"code": code, "name": name})

with open("batch_list.json", "w", encoding="utf-8") as f:
    json.dump(batch, f, ensure_ascii=False, indent=2)

print(f"Batch size: {len(batch)}")
