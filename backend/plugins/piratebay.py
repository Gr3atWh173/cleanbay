from requests import get as get_sync
from urllib.parse import quote as uri_quote
from datetime import datetime, timezone

import asyncio # pylint: disable=unused-import
import math

from ..abstract_plugin import AbstractPlugin
from ..torrent import Torrent, Category


class CBPlugin(AbstractPlugin):
  def info(self):
    return {
        'name': 'piratebay',
        'category': Category.GENERAL,
        'domain': 'https://apibay.org',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36'
    }

  def verify_status(self):
    domain, useragent = self.info()['domain'], self.info()['user-agent']
    return get_sync(
        domain,
        headers={'user-agent': useragent}
    ).status_code != 500

  async def search(self, session, search_param):
    domain, useragent = self.info()['domain'], self.info()['user-agent']

    resp = await session.get(
        domain + '/q.php?q=' + search_param + '&cat=',
        headers={'user-agent': useragent})

    if resp.status != 200:
      return []

    torrents = []
    for element in await resp.json():
      torrents.append(Torrent(
          element['name'],
          self.make_magnet(element['info_hash'], element['name']),
          int(element['seeders']),
          int(element['leechers']),
          self.format_size(int(element['size'])),
          element['username'],
          self.format_date(int(element['added'])),
      ))
    return torrents

  def make_magnet(self, ih, name):
    return f'magnet:?xt=urn:btih:{ih}&dn={uri_quote(name)}&tr={self.trackers()}'

  def trackers(self):
    trackers = '&tr='.join(
      ['udp://tracker.coppersurfer.tk:6969/announce',
       'udp://tracker.openbittorrent.com:6969/announce',
       'udp://9.rarbg.to:2710/announce',
       'udp://9.rarbg.me:2780/announce',
       'udp://9.rarbg.to:2730/announce',
       'udp://tracker.opentrackr.org:1337',
       'http://p4p.arenabg.com:1337/announce',
       'udp://tracker.torrent.eu.org:451/announce',
       'udp://tracker.tiny-vps.com:6969/announce',
       'udp://open.stealth.si:80/announce'])
    return uri_quote(trackers)

  def format_size(self, size_bytes):
    if size_bytes == 0:
      return '0B'
    size_name = ('B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB')
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    # return "%s %s" % (s, size_name[i])
    return f'{s} {size_name[i]}'

  def format_date(self, epoch):
    return datetime.fromtimestamp(
      epoch,
      timezone.utc
    ).strftime('%Y-%m-%d %H:%M:%S')
