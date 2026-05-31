import redis

r = redis.Redis(host="naemini.local", port=6379, db=1, decode_responses=True)

# Clear all old stock keys
name_keys = r.keys("stock:name:*")
code_keys = r.keys("stock:code:*")

if name_keys:
    r.delete(*name_keys)
if code_keys:
    r.delete(*code_keys)

print(f"Cleared {len(name_keys)} name keys and {len(code_keys)} code keys")
