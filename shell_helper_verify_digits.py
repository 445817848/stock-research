import redis

r = redis.Redis(host="naemini.local", port=6379, db=1, decode_responses=True)

# Show sample keys
name_keys = r.keys("stock:name:*")[:5]
for k in name_keys:
    print(f"{k} -> {r.get(k)}")

# Show count
total = len(r.keys("stock:name:*"))
print(f"\nTotal cached: {total}")
