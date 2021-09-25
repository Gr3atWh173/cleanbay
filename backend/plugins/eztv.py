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

    table = resp.findChildren('table')[4]
    if len(table) == 0:
      return []

    torrents = []
    for row in table.findChildren('tr')[2:]:
      seeders = row.findChildren('td')[5].text
      if not seeders.isnumeric():
        seeders = 0
      else:
        seeders = int(seeders)

      try:
        magnet = row.findChildren('td')[2].findChildren('a')[0]['href']
      except IndexError:
        continue
      
      torrents.append(Torrent(
          row.findChildren('td')[1].text.strip(),
          magnet,
          seeders,
          -1,
          row.findChildren('td')[3].text,
          'eztv',
          row.findChildren('td')[4].text
      ))
    return torrents

  def info(self):
    return {
        'name': 'eztv',
        'category': Category.TV,
        'domain': 'https://eztv.re',
        'search_url': 'https://eztv.re/search/',
    }
