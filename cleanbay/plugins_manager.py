from importlib import import_module
from os.path import isfile, basename
import glob


class NoPluginsError(Exception):
  """Indicates that no usable plugins could be loaded."""
  pass


class PluginsManager:
  def __init__(self, directory: str):
    self.plugins = {}

    # import all the files ending with `.py` except __init__ 
    modules = glob.glob(directory + '/*.py')
    plugins = [import_module(f'cleanbay.plugins.{basename(f)[:-3]}')
               for f in modules if isfile(f) and not f.endswith('__init__.py')]

    # filter out the unusable plugins
    for plugin in plugins:
      try:
        plugin = plugin.CBPlugin()
        info = plugin.info()

        if not plugin.verify_status():
          continue
        if ('name' not in info) or ('category' not in info):
          continue
        
        self.plugins[info['name']] = plugin
      except TypeError:
        # TODO(gr3atwh173): add logging
        pass
      except: # pylint: disable=bare-except
        pass
  
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
      NoPluginsError: if there are no usable plugins

    """
    if not self.plugins:
      raise NoPluginsError()
    
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

    return list(filtered_plugins)