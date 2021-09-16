"""contains the `Torrent` data class"""
from dataclasses import dataclass


@dataclass
class Torrent():
  """
  Members:
  name -- name/title of the torrent
  magnet -- the URL of the torrent
  seeders -- seeders of the torrent
  leechers -- leechers of the torrent
  size -- in no particular unit
  uploader -- who uploaded the torrent
  uploaded_at -- upload date
  """
  name: str
  magnet: str
  seeders: int
  leechers: int
  size: int
  uploader: str
  uploaded_at: str
