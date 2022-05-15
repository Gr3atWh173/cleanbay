"""Manages the plugins and the cache."""
import asyncio

from aiohttp import ClientSession, ClientTimeout, TCPConnector

from typing import Tuple

from .cache_manager import CacheManager
from .plugins_manager import PluginsManager


class InvalidSearchError(Exception):
  """Indicates that the search parameters were invalid."""
  pass


class Backend:
  """This class handles all behind-the-scenes logic.

  Handle the loading of the config and the plugins as well as searching each of
  the plugins asynchronusly.

  Attributes:
    config (dict): All the configuration information including which directory
    the plugins are in and what the cache size should be.
    plugins (dict): All the usable plugins hashed with their name.
    cache (dict): A simplistic lFU cache implementation.

  """

  def __init__(self, config: dict):
    """Initializes the backend object.

    Arguments:
      config (dict): a dictionary containing the 'pluginsDirectory', 'cacheSize',
      'sessionTimeout' and 'cacheTimeout' keys.

    """
    self.timeout = config['sessionTimeout']
    self.cache = CacheManager(config['cacheSize'], config['cacheTimeout'])
    self.plugins_manager = PluginsManager(config['pluginsDirectory'])

  def state(self):
    plugins = self.plugins_manager.plugins.keys()
    is_ok = bool(plugins)

    return (plugins, is_ok)

  async def search(
    self,
    search_term: str,
    include_categories: list,
    exclude_categories: list,
    include_sites: list,
    exclude_sites: list
  ) -> Tuple:
    """Searches the relevant plugins for torrents.

    Looks in the cache first. Ideally finds the listings there.

    In case of a miss, invokes the search method of each plugin (which might
    be time consuming).

    Note:
      1. This will cause the cache to update in case of a miss. Which, if it is
      full, might cause even more delay.
      2. For each filter, use either the include or the exclude variant. Using
      both may cause undefined behaviour.

    Args:
      search_param (str): The string to search for.
      include_categories (list): Categories of plugins to search
      exclude_categories (list): Categories of plugins to not search
      include_sites (list): Names of services to search
      exclude_sites (list): Names of services to not search

    Returns:
      A tuple in the form ([], bool). The bool is True in case of a cache hit,
      False otherwise.

    Raises:
      InvalidSearchError: if both include and exclude variants of a filter are
      used together or if no plugins are left after filtering.

    """
    # should not be using include and exclude together
    if include_categories and exclude_categories \
      or include_sites and exclude_sites:
      raise InvalidSearchError()

    search_term = search_term.lower()

    plugins = self.plugins_manager.filter_plugins(
      include_categories, exclude_categories,
      include_sites, exclude_sites
    )

    results, cache_hit = self.try_cache(search_term, plugins)
    if not cache_hit:
      results = await self.update_cache(search_term, plugins)

    return (results, cache_hit)

  def try_cache(self, search_param: str, plugins: list) -> Tuple:
    """Returns the listings from the cache.

    Args:
      search_param (str): The string to search for.
      plugins (list): Plugin objects implementing the `search()` method.

    Returns:
      A tuple containing a list of torrents and a bool denoting if there was a
      cache hit or not.

    """
    cache_hit = self.cache.read(search_param, plugins)

    if not cache_hit:
      return [], False

    return cache_hit, True

  async def update_cache(self, search_param: str, plugins: list) -> list:
    """Updates the cache.

    Searches each plugin in the category and puts its results into the cache.

    Note:
      If the cache has grown more than the size specified in the config
      file - deletes the least frequently used entry and replaces it.

    Args:
      search_param (str): the string to search for.
      plugins (list): Plugin objects implementing the `search()` method.

    Returns:
      List of torrents matching the search query

    """
    results = await self.search_plugins(search_param, plugins)

    if not results:
      return []

    self.cache.store(search_param, plugins, results)

    return results

  async def search_plugins(self, search_param: str, plugins: list) -> list:
    """Searches the plugins etxcept the ones passed in `except_plugins`

    This is an asynchronus function which fires off the plugins, which, in turn,
    sends off HTTP requests, parse the results, and return their respective
    results.

    Args:
      search_param (str): the string to search for.
      plugins (list): Plugin objects implementing the `search()` method.

    Returns:
      A list of compiled results from the specified plugin.

    """
    results = []

    session_timeout = ClientTimeout(total=self.timeout)
    async with ClientSession(
      connector=TCPConnector(ssl=False), timeout=session_timeout
    ) as session:
      tasks = self.create_search_tasks(session, search_param, plugins)
      results = await asyncio.gather(*tasks, return_exceptions=True)

    results = self.exclude_errors(results)

    return self.flatten(results)

  def create_search_tasks(
    self,
    session: ClientSession,
    search_param: str,
    plugins: list
  ) -> list:
    """Creates async tasks for each plugin"""
    tasks = []
    for plugin in plugins:
      search_future = plugin.search(session, search_param)
      task = asyncio.create_task(search_future)
      tasks.append(task)

    return tasks

  def exclude_errors(self, listings: list):
    return [listing for listing in listings if isinstance(listing, list)]

  def flatten(self, t: list) -> list:
    return [item for sublist in t for item in sublist]
