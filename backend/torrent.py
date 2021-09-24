"""contains the `Torrent` data class"""
from dataclasses import dataclass


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
