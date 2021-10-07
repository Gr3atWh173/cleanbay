from bs4 import BeautifulSoup
from requests import get as sync_get
import asyncio # pylint: disable=unused-import

from ..abstract_plugin import AbstractPlugin
from ..torrent import Torrent, Category


class CBPlugin(AbstractPlugin):
  def info(self):
    return {
        'name': 'linuxtracker',
        'category': Category.SOFTWARE,
        'domain': 'https://linuxtracker.org',
    }

  def verify_status(self):
    domain  = self.info()['domain']
    return sync_get(domain).status_code == 200

  async def search(self, session, search_param):
    domain = self.info()['domain']
    search_url = '{}/index.php?page=torrents&search={}&category=0&active=1'

    resp = await session.get(search_url.format(domain, search_param))
    soup = BeautifulSoup(await resp.text(), features='lxml')

    table = soup.find_all('table', {'class': 'lista'})[4]
    if len(table) == 0:
      return []

    torrents = []
    for row in table.findChildren('tr')[1:]:
      try:
        name = row.find_all('td')[1].find_all()[2].text
        magnet = row.find_all('td')[1].find_all()[26].find_all('a')[1]['href']
        date, size, seeders, leechers = self.extract_info(
          row.find_all('td')[1].find_all()[7].text.split('\n')[2:6]
        )

        torrents.append(Torrent(
            name,
            magnet,
            int(seeders),
            int(leechers),
            size,
            'linuxtracker',
            date,
        ))
      except IndexError:
        pass

    return torrents

  def extract_info(self, raw_list):
    date = raw_list[0].split(':')[1].strip()
    size = raw_list[1].split(':')[1].strip()
    seeders =  raw_list[2].strip().split(' ')[1]
    leechers = raw_list[3].strip().split(' ')[1]

    return (date, size, seeders, leechers)
