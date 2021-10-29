"""Manages the plugins and the cache."""
from backend.torrent import Category

from importlib import import_module
from os.path import isfile, basename
from typing import Tuple
import glob
from urllib.parse import urlparse

import asyncio
import aiohttp


class NoPluginsError(Exception):
  """Indicates that no usable plugins could be loaded."""
  pass


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
      config (dict): a dictionary containing the 'pluginsDirectory' and
        'cacheSize' keys.

    """
    self.config = config
    self.plugins = {}
    self.cache = {} # TODO(gr3atwh173): make cache its own module
    self.load_plugins()

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
      NoPluginsError: If there are no loaded plugins.

    """
    if not self.plugins:
      raise NoPluginsError()

    search_term = search_term.lower()
    plugins = self.filter_plugins(
      include_categories, exclude_categories,
      include_sites, exclude_sites
    )

    results, cache_hit = self.try_cache(search_term, plugins)
    if not cache_hit:
      results = await self.update_cache(search_term, plugins)

    return (results, cache_hit)

  def filter_plugins(
    self,
    include_categories: list,
    exclude_categories: list,
    include_sites: list,
    exclude_sites: list
  ) -> list:
    """Filters the plugins based on the passed arguments.

    Individual plugins are given more preference than categories. If a plugin
    was excluded in the category filtering phase, it may be added back if it
    was passed in the `include_sites` list.

    Args:
      include_categories (list): Categories of plugins to search
      exclude_categories (list): Categories of plugins to not search
      include_sites (list): Names of services to search
      exclude_sites (list): Names of services to not search

    Returns:
      A list of filtered plugin objects.

    Raises:
      InvalidSearchError: if both include and exclude variants of a filter are
      used together or if no plugins are left after filtering.

    """
    # probably should not be using include and exclude together
    if include_categories and exclude_categories \
      or include_sites and exclude_sites:
      raise InvalidSearchError()

    filtered_plugins = set(self.plugins.values())

    # categories
    if include_categories:
      filtered_plugins = set()
      for plugin in self.plugins.values():
        cat = plugin.info()['category']
        if cat in include_categories:
          filtered_plugins.add(plugin)

    elif exclude_categories:
      for plugin in self.plugins.values():
        cat = plugin.info()['category']
        if cat in exclude_categories:
          filtered_plugins.remove(plugin)

    # sites
    if include_sites:
      filtered_plugins = set()
      for site, plugin in self.plugins.items():
        if site in include_sites:
          filtered_plugins.add(plugin)

    elif exclude_sites:
      for site, plugin in self.plugins.items():
        if site in exclude_sites and plugin in filtered_plugins:
          filtered_plugins.remove(plugin)

    if not filtered_plugins:
      raise InvalidSearchError()

    return list(filtered_plugins)

  def try_cache(self, search_param: str, plugins: list) -> Tuple:
    """Returns the listings from the cache.

    Args:
      search_param (str): The string to search for.
      plugins (list): Plugin objects implementing the `search()` method.

    Returns:
      A tuple containing a list of torrents and a bool denoting if there was a
      cache hit or not.

    """
    key_tuple = (search_param, frozenset(plugins))

    if key_tuple in self.cache:
      self.cache[key_tuple]['hit_count'] += 1
      return (self.cache[key_tuple]['listings'], True)

    return ([], False)

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
    search_future = self.search_plugins(search_param, plugins)
    results = await search_future

    if not results:
      return []

    if self.config['cacheSize'] <= len(self.cache):
      del self.cache[self.least_frequently_used()]

    key_tuple = (search_param, frozenset(plugins))
    self.cache[key_tuple] = {
        'listings': results,
        'hit_count': 1
    }

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

    async with aiohttp.ClientSession(
      connector=aiohttp.TCPConnector(ssl=False)
    ) as session:
      tasks = self.create_search_tasks(session, search_param, plugins)
      results = await asyncio.gather(*tasks, return_exceptions=True)

    results = self.exclude_errors(results)

    return self.flatten(results)

  def create_search_tasks(
          self,
          session: aiohttp.ClientSession,
          search_param: str,
          plugins: list) -> list:
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

  def least_frequently_used(self):
    return min(self.cache.items(), key=lambda x: x['hit_count'])

  def load_plugins(self):
    modules = glob.glob(self.config['pluginsDirectory'] + '/*.py')
    plugins = [import_module(f'backend.plugins.{basename(f)[:-3]}')
               for f in modules if isfile(f) and not f.endswith('__init__.py')]

    # filter out the unusable plugins
    for plugin in plugins:
      plugin = plugin.CBPlugin()
      try:
        if plugin.verify_status() and 'name' in plugin.info():
          self.plugins[plugin.info()['name']] = plugin

      except TypeError:
        # TODO(gr3atwh173): add logging
        pass

      except: # pylint: disable=bare-except
        # Something probably went wrong in 'verify_status()'
        pass
