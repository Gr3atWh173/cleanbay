"""Contains the implementation for LFU-based cache manager"""
from datetime import datetime, timedelta

from typing import Tuple

from cleanbay.cache_manager.abstract_cache_manager import AbstractCacheManager


class LFUCache(AbstractCacheManager):
  """Manages an LFU cache with a timeout.

  Attributes:
    lines (dict): Cache items hashed by the tuple of the search term and the
    names of the plugins utilized in the search.
    max_size (int): Maximum number of entries in the cache.
    timeout (timedelta): Time in seconds after which a cache entry is
    invalidated.

  """

  def __init__(self, max_size: int, timeout: int):
    """Initializes the cache.

    Arguments:
      max_size (int): Maximum number of entries in the cache.
      timeout (int): Time in seconds after which a cache entry is invalidated.

    """
    self.lines = {}
    self.max_size = max_size
    self.timeout = timedelta(seconds=timeout)

  def store(self, search_term: str, plugins: list, listings: list):
    """Stores a search result into the cache.

    If the cache is at its maximum size, the least frequently used item is
    deleted before storing the incoming item.

    Arguments:
      search_term (str): The string that was searched.
      plugins (list): List of Plugin objects used in the search.
      listings (list): List of Torrents returned from the search.

    """
    if len(self.lines) == self.max_size:
      lfu = self.least_frequently_used()
      del self.lines[lfu]

    key = self.make_key(search_term, plugins)
    self.lines[key] = {
      'listings': listings,
      'hit_count': 1,
      'store_time': datetime.now()
    }

  def read(self, search_term: str, plugins: list) -> list:
    """Reads an item from the cache.

    If the item is in the cache, its 'hit_count' is increased by 1. In case of
    a cache miss, an empty list is returned.

    Arguments:
      search_term (str): The string that was searched.
      plugins (list): List of Plugin objects used in the search.

    Returns:
      A list of Torrents.

    """
    key = self.make_key(search_term, plugins)

    if key not in self.lines:
      return {}
    if not self.is_valid(self.lines[key]):
      return {}

    self.lines[key]['hit_count'] += 1
    return self.lines[key]['listings']

  def is_valid(self, line: dict) -> bool:
    """Checks if the cache item has timed out.

    Arguments:
      line (dict): The cache line to check.

    Returns:
      True if the item hasn't timed out. False otherwise.
    """
    current_time = datetime.now()
    store_time = line['store_time']

    return current_time - store_time < self.timeout

  def make_key(self, search_term: str, plugins: list) -> Tuple:
    names = [plugin.info()['name'] for plugin in plugins]
    return (search_term, frozenset(names))

  def least_frequently_used(self):
    return min(self.cache.items(), key=lambda x: x[1]['hit_count'])[0]
