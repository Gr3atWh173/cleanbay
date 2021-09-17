from requests import get as get_sync
from urllib.parse import quote as uri_quote
import asyncio

from ..abstract_plugin import AbstractPlugin
from ..torrent import Torrent


class CBPlugin(AbstractPlugin):
  def verify_cbplugin(self) -> bool:
    return True

  def verify_status(self) -> bool:
    domain = self.info()['domain']
    return get_sync(domain).status_code == 200

  def info(self) -> dict:
    return {
        'name': 'yts',
        'api_url': 'https://yts.mx/api/v2/list_movies.json?query_term=',
        'domain': 'https://yts.mx'
    }

  async def search(self, session, search_param):
    api_url = self.info()['api_url']
    resp = await session.get(api_url + uri_quote(search_param))
    resp = await resp.json()

    if resp['status'] != 'ok' or resp['data']['movie_count'] == 0:
      return []

    torrents = []
    for element in resp['data']['movies']:
      max_seed_torrent = max(
          element['torrents'],
          key=lambda x: x['seeds']
      )
      torrents.append(Torrent(
          element['title'],
          self.make_magnet(element['title'], max_seed_torrent['hash']),
          max_seed_torrent['seeds'],
          max_seed_torrent['peers'],
          max_seed_torrent['size'],
          'yts',
          max_seed_torrent['date_uploaded'].split(' ')[0]
      ))
    return torrents

  def make_magnet(self, name, ih):
    return f'magnet:?xt=urn:btih:{ih}&dn={uri_quote(name)}{self.trackers()}'

  def trackers(self):
    tr = uri_quote('udp://open.demonii.com:1337/announce')
    tr += uri_quote('udp://tracker.openbittorrent.com:80')
    tr += uri_quote('udp://tracker.coppersurfer.tk:6969')
    tr += uri_quote('udp://glotorrents.pw:6969/announce')
    tr += uri_quote('udp://tracker.opentrackr.org:1337/announce')
    tr += uri_quote('udp://torrent.gresille.org:80/announce')
    tr += uri_quote('udp://p4p.arenabg.com:1337')
    tr += uri_quote('udp://tracker.leechers-paradise.org:6969')
    return tr
