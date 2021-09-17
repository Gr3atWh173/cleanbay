"""This module is responsible for the management of plugins and the cache."""
import json
from importlib import import_module
from os.path import isfile, basename
import glob
from typing import Tuple
import asyncio
import aiohttp


class NoPluginsError(Exception):
  """Indicates that no usable plugins could be loaded."""
  pass


class Backend:
  """This class handles all behind-the-scenes logic.

  The main purpose of this class is to handle the loading of the config and
  the plugins as well as searching each of the plugins asynchronusly.

  Attributes:
    config (dict): All the configuration information including which directory
      the plugins are in and what the cache size should be.
    plugins (dict): All the usable plugins hashed with their name.
    cache (dict): A simplistic lFU cache implementation.

  """

  def __init__(self):
    """Initializes the backend object.

    Loads the config from `config.json` and accordingly loads the plugins.

    """
    self.config = {}
    self.plugins = {}
    self.cache = {}
    self.load_config()
    self.load_plugins()

  def search(self, search_param: str) -> Tuple:
    """Searches the loaded plugins for torrents.

    Looks in the cache first. Ideally finds the listings there.

    In case of a miss, invokes the search method of each plugin (which might
    be time consuming).

    Note:
      This will cause the cache to update in case of a miss. Which, if it is
      full, might cause even more delay

    Args:
      search_param (str): The string to search for.

    Returns:
      A tuple in the form ([], bool). The bool is True in case of a cache hit,
      False otherwise.

    """
    if not self.plugins:
      raise NoPluginsError('No plugins loaded.')

    search_param = search_param.lower()
    results = self.try_cache(search_param)

    if results:
      return (results, True)
    return (self.update_cache(search_param), False)

  def try_cache(self, search_param: str) -> list:
    """Returns the listings from the cache.

    Args:
      search_param (str): The string to search for.

    Returns:
      A list of torrents in case of a cache hit, an empty list otherwise.

    """
    if search_param in self.cache:
      self.cache[search_param]['hit_count'] += 1
      return self.cache[search_param]['listings']
    return []

  def update_cache(self, search_param: str) -> list:
    """Updates the cache.

    Searches each plugin and puts its results into the cache.

    Note:
      If the cache has grown more than the size specified in the config
      file - deletes the least frequently used entry and replaces it.

    Args:
      search_param (str): the string to search for.

    Returns:
      List of torrents matching the search query

    """
    event_loop = asyncio.get_event_loop()
    search_future = self.search_plugins(search_param, except_plugins=[])
    results = event_loop.run_until_complete(search_future)

    if not results:
      return results

    if self.config['cacheSize'] <= len(self.cache):
      del self.cache[self.least_frequently_used()]

    self.cache[search_param] = {
        'listings': results,
        'hit_count': 1
    }
    return results

  async def search_plugins(
          self,
          search_param: str,
          except_plugins: list) -> list:
    """Searches the plugins except the ones passed in `except_plugins`

    This is an asynchronus function which fires off the plugins, which, in turn,
    sends off HTTP requests, parse the results, and return their respective
    results.

    Args:
      search_param (str): the string to search for.
      except_plugins (list): the plugins to skip.

    Returns:
      A list of compiled results from every plugin.

    """
    results = []
    async with aiohttp.ClientSession() as session:
      tasks = self.create_search_tasks(session, search_param, except_plugins)
      results = await asyncio.gather(*tasks)
    return self.flatten(results)

  def create_search_tasks(
          self,
          session: aiohttp.ClientSession,
          search_param: str,
          except_plugins: list) -> list:
    """Creates async tasks for each plugin"""
    tasks = []
    for name, plugin in self.plugins.items():
      if name in except_plugins:
        continue
      task = asyncio.create_task(plugin.search(session, search_param))
      tasks.append(task)
    return tasks

  def flatten(self, t: list) -> list:
    return [item for sublist in t for item in sublist]

  def least_frequently_used(self):
    return min(self.cache.items(), key=lambda x: x['hit_count'])

  def load_config(self):
    try:
      with open('./config.json', 'rt', encoding='utf-8') as f:
        self.config = json.loads(f.read())
    except EnvironmentError:
      self.config = {
          'pluginsDirectory': './plugins',
          'cacheSize': 128
      }

  def load_plugins(self):
    modules = glob.glob(self.config['pluginsDirectory'] + '/*.py')
    plugins = [import_module(f'backend.plugins.{basename(f)[:-3]}').CBPlugin()
               for f in modules if isfile(f) and not f.endswith('__init__.py')]

    # filter these based on if they have a 'verify_cbplugin' method
    for plugin in plugins:
      if plugin.verify_cbplugin() and plugin.verify_status():
        self.plugins[plugin.info()['name']] = plugin
