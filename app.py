"""main"""

# just a test-bed for now
from backend import Backend

back = Backend()

print(back.config, back.plugins)

print(back.search_plugin("game of thrones", "eztv"))

