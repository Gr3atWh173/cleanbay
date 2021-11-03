"""contains the `Torrent` data class and the `Category` enum"""
from dataclasses import dataclass
from enum import Enum


class Category(Enum):
  """Represents the category of a plugin.

  Variants:
    ALL: Everything under the sun
    GENERAL: Plugins that track everything
    CINEMA: Plugins that track movies
    TV: Plugins that track shows on TV, OTT or anything that's not a movie
    SOFTWARE: Plugins that track software excluding games
    
  """
  ALL = 0
  GENERAL = 1
  CINEMA = 2
  TV = 3
  SOFTWARE = 4
  BOOKS = 5


@dataclass
class Torrent():
  """Represents a torrent listing.

  Attributes:
    name (str): Name/title of the torrent
    magnet (str): Magnet URL of the torrent
    seeders (int): Number of seeders. -1 if not listed
    leechers (int): Number of leechers. -1 if not listed
    size (str): Size in the format "<size> <unit>"
    uploader (str): Username of the uploader
    uploaded_at (str): Upload date or time since upload

  """
  name: str
  magnet: str
  seeders: int
  leechers: int
  size: int
  uploader: str
  uploaded_at: str
