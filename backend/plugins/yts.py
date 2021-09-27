from requests import get as get_sync
from urllib.parse import quote as uri_quote
import asyncio # pylint: disable=unused-import

from ..abstract_plugin import AbstractPlugin
from ..torrent import Torrent, Category


class CBPlugin(AbstractPlugin):
  def verify_status(self) -> bool:
    domain = self.info()['domain']
    return get_sync(domain).status_code == 200

  def info(self) -> dict:
    return {
        'name': 'yts',
        'category': Category.CINEMA,
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
          key=lambda x: x['seeds'])

      title_long = element['title_long']
      slug = element['slug']
      quality = max_seed_torrent['quality']
      type_ = max_seed_torrent['type']
      info_hash = max_seed_torrent['hash']
      seeders = max_seed_torrent['seeds']
      leechers = max_seed_torrent['peers']
      size = max_seed_torrent['size']
      date_uploaded = max_seed_torrent['date_uploaded']

      torrents.append(Torrent(
          f'{title_long} [{quality}] [{type_}]',
          self.make_magnet(slug, info_hash),
          int(seeders),
          int(leechers),
          size,
          'yts',
          date_uploaded))

    return torrents

  def make_magnet(self, slug, ih):
    return f'magnet:?xt=urn:btih:{ih}&dn={slug}&tr={self.trackers()}'

  def trackers(self):
    trackers = '&tr='.join(
      ['udp://open.demonii.com:1337/announce',
       'udp://tracker.openbittorrent.com:80',
       'udp://tracker.coppersurfer.tk:6969',
       'udp://glotorrents.pw:6969/announce',
       'udp://tracker.opentrackr.org:1337/announce',
       'udp://torrent.gresille.org:80/announce',
       'udp://p4p.arenabg.com:1337',
       'udp://tracker.leechers-paradise.org:6969'])
    return uri_quote(trackers)
