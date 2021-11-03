from urllib.parse import quote as uri_quote
import asyncio # pylint: disable=unused-import
import aiohttp

from bs4 import BeautifulSoup, SoupStrainer

from ..torrent import Torrent, Category
from ..abstract_plugin import AbstractPlugin

class CBPlugin(AbstractPlugin):
  def verify_status(self) -> bool:
    return True

  async def search(
    self,
    session: aiohttp.ClientSession,
    search_param: str
  ) -> list:
    domain = self.info()['domain']
    search_param = uri_quote(search_param)
    res = await session.get(f'{domain}/search.php?req={search_param}')

    strainer = SoupStrainer('table')
    soup = BeautifulSoup(await res.text(), features='lxml', parse_only=strainer)

    table = soup.findChildren('table')[2]

    torrents = []
    for row in table.findChildren('tr')[1:]:
      cols = row.findChildren('td')

      author = cols[1].text
      title = cols[2].text
      publisher = cols[3].text
      year = cols[4].text
      pages = cols[5].text
      language = cols[6].text
      size = cols[7].text
      download = cols[9].find('a')['href']

      name = f'[{author}] {title}'
      
      info = '('
      if publisher:
        info += publisher + ', '
      if year:
        info += year + ', '
      if pages:
        info += pages + 'p'
      info += ')'
      
      if info != '()':
        name += ' ' + info

      torrents.append(Torrent(
        name,
        download,
        1,
        -1,
        size.upper(),
        'libgen',
        year
      ))

    return torrents

  def info(self) -> dict:
    return {
      'name': 'libgen',
      'category': Category.BOOKS,
      'domain': 'https://libgen.is'
    }
