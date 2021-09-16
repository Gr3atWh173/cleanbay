from bs4 import BeautifulSoup, SoupStrainer
import requests

from ..abstract_plugin import AbstractPlugin
from ..torrent import Torrent


class CBPlugin(AbstractPlugin):
  def verify_cbplugin(self):
    return True

  def verify_status(self):
    return requests.get(self.info()['domain']).status_code == 200

  def search(self, search_param):
    info = self.info()
    url = info['search_url'] + search_param
    resp = requests.get(url).text

    strainer = SoupStrainer('table')
    resp = BeautifulSoup(resp, features='lxml', parse_only=strainer)

    table = resp.findChildren('table')[4]
    if len(table) == 0:
      return []

    torrents = []
    for row in table.findChildren('tr')[2:]:
      torrents.append(Torrent(
        row.findChildren('td')[1].text.strip().replace('[eztv]', ''),
        row.findChildren('td')[2].findChildren('a')[0]['href'],
        row.findChildren('td')[5].text,
        'N/A',
        row.findChildren('td')[3].text,
        'eztv',
        row.findChildren('td')[4].text
      ))
    return torrents

  def info(self):
    return {
      'name': 'eztv',
      'domain': 'https://eztv.re',
      'search_url': 'https://eztv.re/search/',
  }
