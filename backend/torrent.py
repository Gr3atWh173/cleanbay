"""contains the `Torrent` data class"""
from dataclasses import dataclass


@dataclass
class Torrent():
  """Represents a torrent listing.

  Attributes:
    name (str): name/title of the torrent
    magnet (str): the URL of the torrent
    seeders (int|str): seeders of the torrent
    leechers (int|str): leechers of the torrent
    size (str): size in no particular unit
    uploader (str): who uploaded the torrent
    uploaded_at (str): upload date

  """
  name: str
  magnet: str
  seeders: int
  leechers: int
  size: int
  uploader: str
  uploaded_at: str
