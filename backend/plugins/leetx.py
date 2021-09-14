from bs4 import BeautifulSoup, SoupStrainer
import requests

from .. import abstract_plugin
from .. import torrent

class CBPlugin(abstract_plugin.AbstractPlugin):
  def verify_cbplugin(self):
    return True

  def verify_status(self):
    return True

  def search(self, search_param):
    info = self.info()
    domain, useragent = info['domain'], info['user-agent']
    url = f'{domain}/search/{search_param}/1/'
    resp = requests.get(url, headers={'User-Agent': useragent}).text

    strainer = SoupStrainer('table')
    resp = BeautifulSoup(resp, features='lxml', parse_only=strainer)

    table = resp.findChildren('table')
    if len(table) == 0:
      return []

    torrents = []
    for row in table[0].findChildren('tr')[1:]:
      torrents.append(torrent.Torrent(
          row.findChildren('td')[0].findChildren('a')[1].text,
          # TODO(gr3atwh173): make this the actual magnet link, not the link to the page on 1337x
          row.findChildren('td')[0].findChildren('a')[1]['href'],
          int(row.findChildren('td')[1].text),
          int(row.findChildren('td')[2].text),
          row.findChildren('td')[4].text.split('B')[0] + 'B',
          row.findChildren('td')[5].text,
          row.findChildren('td')[3].text
      ))
    return torrents


  def info(self):
    return {
      'name': 'leetx',
      'domain': 'https://1337x.to',
      'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36'
    }
