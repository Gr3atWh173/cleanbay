"""The module contains the abstract interface for plugins"""
from abc import ABC
import asyncio
import aiohttp


class AbstractPlugin(ABC):
  """All plugins must be derived from this abstract class."""

  def verify_status(self) -> bool:
    """Verifies the status of the external service used by the plugin.

    Returns `True` only if said service is online and usable;
    'False' otherwise.

    """
    pass

  async def search(
    self,
    session: aiohttp.ClientSession,
    search_param: str) -> list:
    """Searches the external service.

    Args:
      session (aiohttp.ClientSession): a session object that the plugin can use
        to access the web.
      search_param (str): the string to search for.

    """
    pass

  def info(self) -> dict:
    """Gives metadata about the plugin

    Must include a 'name' field.

    """
    pass
