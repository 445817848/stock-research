import json
import os

# Load batch list
with open("batch_list.json", "r", encoding="utf-8") as f:
    batch = json.load(f)

# Check which are done
done = []
not_done = []
for item in batch:
    code = item["code"]
    path = f"stock_intel/{code}.json"
    if os.path.exists(path):
        done.append(item)
    else:
        not_done.append(item)

# Save progress
progress = {
    "total_in_batch": len(batch),
    "completed": len(done),
    "remaining": len(not_done),
    "completed_stocks": done,
    "remaining_stocks": not_done,
}

with open("batch_progress.json", "w", encoding="utf-8") as f:
    json.dump(progress, f, ensure_ascii=False, indent=2)

print(f"Done: {len(done)}/{len(batch)}")
print(f"Remaining: {len(not_done)}")
if not_done:
    print(f"Next: {not_done[0]['code']} {not_done[0]['name']}")
