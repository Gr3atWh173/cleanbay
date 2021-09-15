"""main"""

# just a test-bed for now
from backend import Backend

back = Backend()

print(back.config, back.plugins)

back.search("dont breathe")
# back.search("god of war")
# back.search("f9")
# back.search("god of war")

print(back.cache)
