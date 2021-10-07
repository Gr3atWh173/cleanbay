"""Manages the plugins and the cache."""
from backend.torrent import Category

from importlib import import_module
from os.path import isfile, basename
from typing import Tuple
import glob

from difflib import SequenceMatcher

import asyncio
import aiohttp


class NoPluginsError(Exception):
  """Indicates that no usable plugins could be loaded."""
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
    search_param: str,
    category: Category = Category.ALL) -> Tuple:
    """Searches the loaded plugins for torrents.

    Looks in the cache first. Ideally finds the listings there.

    In case of a miss, invokes the search method of each plugin (which might
    be time consuming).

    Note:
      This will cause the cache to update in case of a miss. Which, if it is
      full, might cause even more delay

    Args:
      search_param (str): The string to search for.
      category (Category): Category of plugins to search (defaults to ALL)

    Returns:
      A tuple in the form ([], bool). The bool is True in case of a cache hit,
      False otherwise.

    """
    if not self.plugins:
      raise NoPluginsError('No plugins loaded.')

    search_param = search_param.lower()
    results = self.try_cache(search_param, category)
    cache_hit = True

    if not results:
      results = await self.update_cache(search_param, category)
      cache_hit = False

    self.sort_by_relevance_and_seeders(results, search_param)
    return (results, cache_hit)

  def try_cache(self, search_param: str, category: Category) -> list:
    """Returns the listings from the cache.

    Args:
      search_param (str): The string to search for.
      category (Category): Category of plugins to search.

    Returns:
      A list of torrents in case of a cache hit, an empty list otherwise.

    """
    key_tuple = (search_param, category)

    if key_tuple in self.cache:
      self.cache[key_tuple]['hit_count'] += 1
      return self.cache[key_tuple]['listings']

    return []

  async def update_cache(self, search_param: str, category: Category) -> list:
    """Updates the cache.

    Searches each plugin in the category and puts its results into the cache.

    Note:
      If the cache has grown more than the size specified in the config
      file - deletes the least frequently used entry and replaces it.

    Args:
      search_param (str): the string to search for.
      category (Category): category of plugins to search.

    Returns:
      List of torrents matching the search query

    """
    search_future = self.search_plugins(
      search_param,
      category=category,
      except_plugins=[])

    results = await search_future

    if not results:
      return []

    if self.config['cacheSize'] <= len(self.cache):
      del self.cache[self.least_frequently_used()]

    self.cache[(search_param, category)] = {
        'listings': results,
        'hit_count': 1
    }

    return results

  async def search_plugins(
          self,
          search_param: str,
          category: Category,
          except_plugins: list) -> list:
    """Searches the plugins etxcept the ones passed in `except_plugins`

    This is an asynchronus function which fires off the plugins, which, in turn,
    sends off HTTP requests, parse the results, and return their respective
    results.

    Args:
      search_param (str): the string to search for.
      category (Category): the category of plugins to search
      except_plugins (list): the plugins to skip.

    Returns:
      A list of compiled results from every plugin.

    """
    results = []
    plugins = self.get_plugins_by_category(category, except_plugins)
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

  def get_plugins_by_category(
    self,
    category: Category,
    except_plugins: list) -> list:
    """Returns a list of all plugins in a specific category"""
    if category == Category.ALL.value:
      return [plugin for _, plugin in self.plugins.items()]

    return [plugin for _, plugin in self.plugins.items()
            if plugin.info()['category'].value == category
            and plugin.info()['name'] not in except_plugins]
    
  def sort_by_relevance_and_seeders(
    self,
    listings: list,
    search_param: str) -> list:
    listings.sort(
      key=lambda z: (
          z.seeders,
          SequenceMatcher(None, z.name, search_param).ratio()),
      reverse=True)

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
