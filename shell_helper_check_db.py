import redis

# Check DB 0
r0 = redis.Redis(host="naemini.local", port=6379, db=0, decode_responses=True)
keys_0 = r0.keys("stock:name:*")
print(f"DB 0 name keys: {len(keys_0)}")

# Check DB 1
r1 = redis.Redis(host="naemini.local", port=6379, db=1, decode_responses=True)
keys_1 = r1.keys("stock:name:*")
print(f"DB 1 name keys: {len(keys_1)}")

if keys_1:
    print(f"Sample DB 1 key: {keys_1[0]}")
    print(f"Sample value: {r1.get(keys_1[0])}")
