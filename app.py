"""Serves the API that enables searching the backend"""
import os
from typing import Optional

from backend import Backend
from backend.torrent import Category

from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import Response
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from dotenv import load_dotenv


# prepare the config and rate limits
load_dotenv()

config = {
  'pluginsDirectory': os.getenv('PLUGINS_DIRECTORY', './backend/plugins'),
  'cacheSize': int(os.getenv('CACHE_SIZE', '128'))
}
rate_limit = os.getenv('RATE_LIMIT', '100/minute')
allowed_origin = os.getenv('ALLOWED_ORIGIN', '*')

# initialize tha app (with limiting and cors) and the backend
app = FastAPI()
limiter = Limiter(key_func=get_remote_address)
backend = Backend(config)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(
  CORSMiddleware,
  allow_origins=[allowed_origin],
  allow_credentials=True,
  allow_methods=['*'],
  allow_headers=['*']
)


# define routes
@app.get('/api/v1/status')
@limiter.limit(rate_limit)
def status(
  request: Request,
  response: Response):
  """returns the current status and list of available plugins"""
  plugins = backend.plugins.keys()
  is_ok = (len(plugins) != 0)

  return {
    'status': 'ok' if is_ok else 'not ok',
    # have to cast plugins to a list so that it can be serialized
    'plugins': list(plugins)
  }

@app.get('/api/v1/search/{search_query}')
@limiter.limit(rate_limit)
async def search(
  request: Request,
  response: Response,
  search_query: str,
  category: Optional[int] = None):
  """performs the search on all available plugins"""
  cat = category if category else Category.ALL.value
  (listings, is_from_cache) = await backend.search(search_query, cat)

  return {
    'search_query': search_query,
    'category': cat,
    'listings_length': len(listings),
    'cache_hit': is_from_cache,
    'listings': jsonable_encoder(listings)
  }
