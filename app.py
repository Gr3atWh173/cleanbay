"""Serves the API that enables searching the backend"""
import os
from typing import Tuple
from itertools import chain

from cleanbay.backend import Backend, InvalidSearchError
from cleanbay.torrent import Category
from cleanbay.plugins_manager import NoPluginsError

from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from pydantic import BaseModel

from dotenv import load_dotenv


# load the config data
load_dotenv()
config = {
  'pluginsDirectory': os.getenv('PLUGINS_DIRECTORY', './cleanbay/plugins'),
  'cacheSize': int(os.getenv('CACHE_SIZE', '128'))
}
rate_limit = os.getenv('RATE_LIMIT', '100/minute')
allowed_origin = os.getenv('ALLOWED_ORIGIN', '*')

# initialize tha app and the backend
backend = Backend(config)

app = FastAPI()
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(
  CORSMiddleware,
  allow_origins=[allowed_origin],
  allow_credentials=True,
  allow_methods=['*'],
  allow_headers=['*']
)


class SearchQuery(BaseModel):
  """Used to deserialize the JSON received in the request body

  Attributes:
    search_term (str): The string to search for
    include_categories (list): Categories in which to search
    exclude_categories (list): Categories in which to not search
    include_sites (list): Plugins/services to search
    exclude_sites (list): Plugins/services to not search

  """
  search_term: str
  include_categories: list
  exclude_categories: list
  include_sites: list
  exclude_sites: list


CATEGORY_MAP = {
  'all': Category.ALL,
  'general': Category.GENERAL,
  'cinema': Category.CINEMA,
  'tv': Category.TV,
  'software': Category.SOFTWARE
}


# define routes
@app.get('/api/v1/status')
@limiter.limit(rate_limit)
def status(request: Request, response: Response):
  """Returns the current status and list of available plugins"""
  plugins, is_ok = backend.state()
  status_word = 'ok' if is_ok else 'not ok'

  return {
    'status': status_word,
    'plugins': list(plugins)
  }


@app.post('/api/v1/search')
@limiter.limit(rate_limit)
async def search(request: Request, response: Response, sq: SearchQuery):
  """Searches the relevant plugins for torrents"""
  if not is_valid(sq):
    response.status_code = 400
    return make_error('Invalid search query.')

  s_term, i_cats, e_cats, i_sites, e_sites = parse_search_query(sq)

  try:
    listings, cache_hit = await backend.search(
      search_term=s_term,
      include_categories=i_cats,
      exclude_categories=e_cats,
      include_sites=i_sites,
      exclude_sites=e_sites
    )
  except NoPluginsError:
    response.status_code = 500
    return make_error("No searchable plugins.")
  except InvalidSearchError:
    response.status_code = 400
    return make_error("Invalid search.")

  return make_search_response(s_term, listings, cache_hit)


def make_search_response(
  search_term: str,
  listings: list,
  cache_hit: bool
) -> dict:
  return {
    'search_term': search_term,
    'length': len(listings),
    'cache_hit': cache_hit,
    'data': listings
  }


def make_error(msg: str) -> dict:
  return {'status': 'error', 'msg': msg}


def is_valid(sq: SearchQuery) -> bool:
  # we should atleast have a search_term
  if sq.search_term.strip() == '':
    return False

  # should only use inclusion or exclusion per filter
  if sq.include_categories and sq.exclude_categories:
    return False
  if sq.include_sites and sq.exclude_sites:
    return False

  # each filter should have valid values
  for cat in chain(sq.include_categories, sq.exclude_categories):
    if cat not in CATEGORY_MAP.keys():
      return False

  indexed_sites = backend.state()[0]
  for site in chain(sq.include_sites, sq.exclude_sites):
    if site not in indexed_sites:
      return False

  return True


def parse_search_query(sq: SearchQuery) -> Tuple:
  s_term = sq.search_term

  # if there's 'all' in the include category list, treat it as if the list was
  # empty, ie, include everything
  i_cats = []
  if any(x in sq.include_categories for x in ['all', '*']):
    i_cats = CATEGORY_MAP.values()
    i_cats.remove(Category.ALL)
  else:
    i_cats = [CATEGORY_MAP[cat] for cat in sq.include_categories]

  e_cats = [CATEGORY_MAP[cat] for cat in sq.exclude_categories]

  i_sites = sq.include_sites
  e_sites = sq.exclude_sites

  return (s_term, i_cats, e_cats, i_sites, e_sites)

if __name__ == '__main__':
  import uvicorn
  uvicorn.run(app, debug=True)
