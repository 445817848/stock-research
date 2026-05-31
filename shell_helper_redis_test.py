import redis

r = redis.Redis(
    host='naemini.local',
    port=6379,
    decode_responses=True,
    db=1
)

print("PING:", r.ping())

r.set('stock:name:600519', '贵州茅台')
r.set('stock:name:002594', '比亚迪')

print("600519:", r.get('stock:name:600519'))
print("002594:", r.get('stock:name:002594'))

r.delete('stock:name:600519', 'stock:name:002594')
print("OK")
