"""The module contains the abstract interface for plugins"""
from abc import ABC

class AbstractPlugin(ABC):
  """All plugins must be derived from this abstract class."""
  def verify_cbplugin(self) -> bool:
    """Verifies if this is indeed a valid CBPlugin. Must return `True`."""
    pass

  def verify_status(self) -> bool:
    """Verifies the status of the external service used by the plugin.
    Returns `True` only if said service is online and usable;
    'False' otherwise."""
    pass

  def search(self, search_param: str) -> list:
    """Searches the external service and returns a list of `Torrent` objects.

    Keyword Arguments:
    search_param -- the string to search for.
    """
    pass

  def info(self) -> dict:
    """Gives metadata about the plugin in the form of a dictionary.
    Must include a unique `name` field."""
    pass
