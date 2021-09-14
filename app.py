"""main"""

# just a test-bed for now
from backend import Backend

back = Backend()

print(back.config, back.plugins)

back.search("Star trek")
back.search("Star wars")
back.search("Fast and the Furious")
back.search("Star Trek")

print(back.cache)
