import redis

r = redis.Redis(host="localhost", port=6379, decode_responses=True)

r.set("test_key", "hello", ex=10)   # ex=10 means TTL of 10 seconds
print(r.get("test_key"))            # should print: hello
print(r.ttl("test_key"))            # seconds remaining, roughly 10