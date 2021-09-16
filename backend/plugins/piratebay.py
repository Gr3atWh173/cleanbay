import requests
from urllib.parse import quote as uri_quote

from ..abstract_plugin import AbstractPlugin
from ..torrent import Torrent


class CBPlugin(AbstractPlugin):
  def __init__(self):
    self.session = requests.Session()
    self.session.headers.update({
        'user-agent': self.info()['user-agent']
    })

  def verify_cbplugin(self):
    return True

  def info(self):
    return {
        'name': 'piratebay',
        'domain': 'https://apibay.org',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36'
    }

  def verify_status(self):
    return self.session.get(self.info()['domain']).status_code != 500

  def search(self, search_param):
    domain = self.info()['domain']
    resp = self.session.get(domain + '/q.php?q=' + search_param + '&cat=')

    if resp.status_code != 200:
      return []

    torrents = []
    for element in resp.json():
      torrents.append(Torrent(
          element['name'],
          self.make_magnet(element['info_hash'], element['name']),
          element['seeders'],
          element['leechers'],
          element['size'],
          element['username'],
          element['added']
      ))

    return torrents

  def make_magnet(self, ih, name):
    return 'magnet:?xt=urn:btih:'+ih+'&dn='+uri_quote(name)+self.trackers()

  def trackers(self):
    tr = '&tr=' + uri_quote('udp://tracker.coppersurfer.tk:6969/announce')
    tr += '&tr=' + uri_quote('udp://tracker.openbittorrent.com:6969/announce')
    tr += '&tr=' + uri_quote('udp://9.rarbg.to:2710/announce')
    tr += '&tr=' + uri_quote('udp://9.rarbg.me:2780/announce')
    tr += '&tr=' + uri_quote('udp://9.rarbg.to:2730/announce')
    tr += '&tr=' + uri_quote('udp://tracker.opentrackr.org:1337')
    tr += '&tr=' + uri_quote('http://p4p.arenabg.com:1337/announce')
    tr += '&tr=' + uri_quote('udp://tracker.torrent.eu.org:451/announce')
    tr += '&tr=' + uri_quote('udp://tracker.tiny-vps.com:6969/announce')
    tr += '&tr=' + uri_quote('udp://open.stealth.si:80/announce')
    return tr
