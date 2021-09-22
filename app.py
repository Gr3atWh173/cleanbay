"""Serves the API that enables searching the backend"""
from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from backend import Backend


app = FastAPI()
backend = Backend()

app.add_middleware(
  CORSMiddleware,
  allow_origins=['*'],
  allow_credentials=True,
  allow_methods=['GET'],
  allow_headers=['*']
)


@app.get('/api/v1/status')
def status():
  plugins = list(backend.plugins.keys())
  is_ok = (plugins != [])
  return {
    'status': 'ok' if is_ok else 'not ok',
    'plugins': plugins
  }


@app.get('/api/v1/search/{search_query}')
async def search(search_query: str):
  (listings, from_cache) = await backend.search(search_query)
  return {
    'search_query': search_query,
    'listings_length': len(listings),
    'cache_hit': from_cache,
    'listings': jsonable_encoder(listings)
  }

