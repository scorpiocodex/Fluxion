import asyncio
import aiodns

async def test():
    resolver = aiodns.DNSResolver()
    try:
        res = await resolver.query("google.com", "A")
        print("A:", res)
    except Exception as e:
        print("Exception:", type(e), e)

asyncio.run(test())
