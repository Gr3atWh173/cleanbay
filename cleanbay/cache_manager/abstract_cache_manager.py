"""Contains the cache manager interface/abstract class"""
from abc import ABC, abstractmethod


class AbstractCacheManager(ABC):
    """All cache managers must be derived from this class"""

    @abstractmethod
    def store(self, search_term: str, plugins: list, listings: list):
        """Stores a search result into the cache.

        Arguments:
        search_term (str): The string that was searched.
        plugins (list): List of Plugin objects used in the search.
        listings (list): List of Torrents returned from the search.

        """
        pass

    @abstractmethod
    def read(self, search_term: str, plugins: list) -> list:
        """Reads an item from the cache.

        Arguments:
          search_term (str): The string that was searched.
          plugins (list): List of Plugin objects used in the search.

        Returns:
          A list of Torrents.

        """
        pass
