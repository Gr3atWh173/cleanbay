'''This module is responsible for the management of plugins and the cache.'''
import json
from importlib import import_module
from os.path import isfile, basename
import glob
from typing import Tuple

class NoPluginsError(Exception):
  '''Indicates that no usable plugins could be loaded.'''
  pass

class Backend:
  '''The main class for this module. Handles all the behind-the-scenes logic
  like loading configs, plugins and managing the cache.'''

  def __init__(self):
    '''Initializes the backend object. Loads the config file, and plugins.'''
    self.config = {}
    self.plugins = {}
    self.cache = {}
    self.load_config()
    self.load_plugins()

  def search(self, search_param:str) -> Tuple:
    '''Returns cached results if any. If not, performs a fresh search,
    updates the cache and returns the results.

    The returned tuple contains a list of Torrent objects and a boolean
    indicating if the results were fetched from the cache

    Keyword Arguments:
    search_param -- the string to search for'''
    if not self.plugins:
      raise NoPluginsError('No plugins loaded.')
    search_param = search_param.lower()
    results = self.try_cache(search_param)
    if results:
      return (results, True)
    return (self.update_cache(search_param), False)

  def try_cache(self, search_param:str) -> list:
    '''Return the listings if they exist in the cache
    Otherwise returns an empty list

    Keyword Arguments:
    search_param -- the string to search for'''
    if search_param in self.cache:
      self.cache[search_param]['hit_count'] += 1
      return self.cache[search_param]['listings']

    return []

  def update_cache(self, search_param:str) -> list:
    '''Updates the cache.

    If the cache has grown more than the size specified in the config
    file - deletes the least frequently used entry and replaces it.

    Keyword Arguments:
    search_param -- the string to search for'''
    results = self.search_plugins(search_param, except_plugins=[])
    if not results:
      return results

    if self.config['cacheSize'] <= len(self.cache):
      del self.cache[self.least_frequently_used()]

    self.cache[search_param] = {
      'listings': results,
      'hit_count': 1
    }

    return results

  def search_plugins(self, search_param:str, except_plugins:list) -> list:
    '''Searches all plugins except the ones passed in `except_plugins`

    Keyword Arguments:
    search_param -- the string to search for
    except_plugins -- the plugins to skip (default is [])'''
    results = []
    for name, plugin in self.plugins.items():
      if name in except_plugins:
        continue
      results.extend(plugin.search(search_param))

    return results

  def least_frequently_used(self):
    return min(self.cache.items(), key=lambda x: x['hit_count'])

  def load_config(self):
    try:
      with open('./config.json', 'rt', encoding='utf-8') as f:
        self.config = json.loads(f.read())
    except EnvironmentError:
      # fallback settings
      self.config = {
        'pluginsDirectory': './plugins',
        'cacheSize': 128
      }

  def load_plugins(self):
    modules = glob.glob(self.config['pluginsDirectory'] + '/*.py')
    maybe_plugins = [ import_module('backend.plugins.' + basename(f)[:-3]).CBPlugin() for f in modules
      if isfile(f) and not (f.endswith('__init__.py') or f.endswith('abstract_plugin.py') or f.endswith('torrent.py')) ]

    # filter these based on if they have a 'verify_cbplugin' method
    for plugin in maybe_plugins:
      if plugin.verify_cbplugin() and plugin.verify_status():
        self.plugins[plugin.info()['name']] = plugin
