"""Serves the API that enables searching the backend"""
import os
from typing import Tuple

from backend import Backend

from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import Response
# from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from pydantic import BaseModel

from dotenv import load_dotenv

from backend.torrent import Category


# load the config data
load_dotenv()
config = {
  'pluginsDirectory': os.getenv('PLUGINS_DIRECTORY', './backend/plugins'),
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
    included_categories (list): Categories in which to search
    excluded_categories (list): Categories in which to not search
    included_sites (list): Plugins/services to search
    excluded_sites (list): Plugins/services to not search

  """
  search_term: str
  included_categories: list
  excluded_categories: list
  included_sites: list
  excluded_sites: list


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
  """returns the current status and list of available plugins"""
  plugins = backend.plugins.keys()
  status_word = 'ok' if len(plugins) != 0 else 'not ok'

  return {
    'status': status_word,
    'plugins': list(plugins)
  }


@app.post('/api/v1/search')
@limiter.limit(rate_limit)
async def search(request: Request, response: Response, sq: SearchQuery):
  """performs the search on all available plugins"""
  sq_is_valid, msg = validate_search_query(sq)
  if not sq_is_valid:
    return make_error(msg)

  s_term, i_cats, e_cats, i_sites, e_sites = parse_search_query(sq)

  listings, cache_hit = await backend.search(
    search_term=s_term,
    include_categories=i_cats,
    exclude_categories=e_cats,
    include_sites=i_sites,
    exclude_sites=e_sites
  )

  return make_search_response(s_term, listings, cache_hit)
  # return {
  #   's_term': s_term,
  #   'i_cats': i_cats,
  #   'e_cats': e_cats,
  #   'i_sites': i_sites,
  #   'e_sites': e_sites
  # }

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


def validate_search_query(sq: SearchQuery) -> Tuple:
  return (True, '')


def parse_search_query(search_query: SearchQuery) -> Tuple:
  s_term = search_query.search_term
  i_cats = [CATEGORY_MAP[cat] for cat in search_query.included_categories]
  e_cats = [CATEGORY_MAP[cat] for cat in search_query.excluded_categories]
  i_sites = search_query.included_sites
  e_sites = search_query.excluded_sites
  return (s_term, i_cats, e_cats, i_sites, e_sites)

