"""Serves the API that enables searching the backend"""
from backend import Backend
from backend.torrent import Category
from typing import Optional

from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware

import json


# load the configuration file
# TODO(gr3atwh173): pull these values out of the environment instead
config = {}
try:
  with open('./config.json', 'rt', encoding='utf-8') as f:
    config = json.loads(f.read())

except EnvironmentError:
  config = {
      'pluginsDirectory': './backend/plugins',
      'cacheSize': 128
  }


app = FastAPI()
backend = Backend(config)

app.add_middleware(
  CORSMiddleware,
  allow_origins=['*'],
  allow_credentials=True,
  allow_methods=['*'],
  allow_headers=['*']
)


@app.get('/api/v1/status')
def status():
  plugins = backend.plugins.keys()
  is_ok = (len(plugins) != 0)

  return {
    'status': 'ok' if is_ok else 'not ok',
    # have to cast plugins to a list so that it can be serialized
    'plugins': list(plugins)
  }


@app.get('/api/v1/search/{search_query}')
async def search(search_query: str, category: Optional[int] = None):
  cat = category if category else Category.ALL.value
  (listings, is_from_cache) = await backend.search(search_query, cat)

  return {
    'search_query': search_query,
    'category': cat,
    'listings_length': len(listings),
    'cache_hit': is_from_cache,
    'listings': jsonable_encoder(listings)
  }
