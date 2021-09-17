"""main"""

# just a test-bed for now
from backend import Backend
import asyncio
import time

back = Backend()

print(back.config, back.plugins)

start = time.time()
results = asyncio.get_event_loop().run_until_complete(back.search_plugins("fast and furious", []))
elapsed = time.time() - start
print("async: took {} seconds to search {} plugins.".format(elapsed, len(back.plugins)))

print(results[0])
