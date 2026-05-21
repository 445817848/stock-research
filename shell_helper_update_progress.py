import json
import sys

with open('batch_progress.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

code = sys.argv[1]
name = sys.argv[2]

# Find and remove from remaining
found = None
for item in data['remaining_stocks']:
    if item['code'] == code:
        found = item
        break

if found:
    data['remaining_stocks'].remove(found)
    data['completed_stocks'].append(found)
    data['completed'] += 1
    data['remaining'] -= 1
    
    with open('batch_progress.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Updated: {code} {name} moved to completed")
else:
    print(f"Not found in remaining: {code} {name}")
