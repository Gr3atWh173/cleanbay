from bs4 import BeautifulSoup, SoupStrainer
from requests import get as sync_get
import asyncio # pylint: disable=unused-import

from ..abstract_plugin import AbstractPlugin
from ..torrent import Torrent, Category


class CBPlugin(AbstractPlugin):
  def verify_status(self):
    return sync_get(self.info()['domain']).status_code == 200

  async def search(self, session, search_param):
    info = self.info()
    url = info['search_url'] + search_param
    resp = await session.get(url)

    strainer = SoupStrainer('table')
    resp = BeautifulSoup(
        await resp.text(),
        features='lxml',
        parse_only=strainer)

    table = resp.findChildren('table')[0]

    if len(table) == 0:
      return []

    torrents = []
    for row in table.findChildren('tr')[1:]:
      row_children = row.findChildren('td')

      seeders = row_children[5].text
      if not seeders.isnumeric():
        seeders = 0
      else:
        seeders = int(seeders)
      
      leechers = row_children[6].text
      if not leechers.isnumeric():
        leechers = 0
      else:
        leechers = int(leechers)

      try:
        magnet = row_children[2].findChildren('a')[1]['href']
      except IndexError:
        continue
      
      torrents.append(Torrent(
          row_children[1].text.strip(),
          magnet,
          seeders,
          leechers,
          row_children[3].text.replace("i", ""),
          'nyaa',
          row_children[4].text
      ))
    return torrents

  def info(self):
    return {
        'name': 'nyaa',
        'category': Category.TV,
        'domain': 'https://nyaa.iss.ink/',
        'search_url': 'https://nyaa.iss.ink/?f=0&c=0_0&q=',
    }
