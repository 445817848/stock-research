import redis

r = redis.Redis(host="naemini.local", port=6379, db=1, decode_responses=True)

# Check a few keys from the new fetch
codes = ["bj920178", "sz301139", "sz301020", "sh688449"]
for code in codes:
    name = r.get(f"stock:name:{code}")
    print(f"{code:12} -> {name}")

# Count total cached entries (name keys + code keys)
name_keys = r.keys("stock:name:*")
code_keys = r.keys("stock:code:*")
print(f"\nTotal name mappings: {len(name_keys)}")
print(f"Total code mappings: {len(code_keys)}")
